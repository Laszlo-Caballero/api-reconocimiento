import cv2
import numpy as np
import networkx as nx
from typing import List, Tuple, Dict
import math
import os
import requests
import json
import base64


class GraphBuilder:
    """
    Construye un grafo a partir de una imagen de plano de planta.
    Utiliza un pipeline con OpenCV, OCR y Qwen2.5-VL 7B en Ollama para modelar el grafo
    y mapear las tiendas.
    """

    def __init__(self, open_space_threshold: int = 30, min_node_distance: int = 20,
                 door_close_kernel: int = 0, min_room_area: int = 500,
                 debug_dir: str = ""):
        self.open_space_threshold = open_space_threshold
        self.min_node_distance = min_node_distance
        self.door_close_kernel = door_close_kernel  # 0 = auto
        self.min_room_area = min_room_area
        self.debug_dir = debug_dir
        self.graph = nx.Graph()

    def _save_debug(self, name: str, img: np.ndarray):
        """Guarda imagen de debug."""
        d_dir = self.debug_dir if self.debug_dir else "images"
        os.makedirs(d_dir, exist_ok=True)
        path = os.path.join(d_dir, f"debug_{name}.png")
        cv2.imwrite(path, img)

    def remove_color_annotations(self, image: np.ndarray) -> np.ndarray:
        """Elimina solo flechas/íconos de color intenso (S > 120) sin dañar paredes cercanas."""
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        color_mask = (hsv[:, :, 1] > 120).astype(np.uint8) * 255

        # Dilatar muy poco para cubrir bordes de antialiasing sin invadir paredes
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        color_mask = cv2.dilate(color_mask, kernel, iterations=1)

        # Reemplazar con blanco
        cleaned = image.copy()
        cleaned[color_mask > 0] = [255, 255, 255]

        self._save_debug("01_color_removed", cleaned)
        return cleaned

    def get_walkable_area(self, image: np.ndarray) -> np.ndarray:
        """
        Obtiene el área transitable usando adaptive threshold.
        Zonas claras = transitable (255), zonas oscuras = pared (0).
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()

        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        self._save_debug("02_gray_blurred", blurred)

        # Adaptive threshold: C=5 es más sensible para capturar paredes finas/fantasmas
        walkable = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=25,
            C=5
        )
        self._save_debug("03_adaptive_raw", walkable)

        # Operar directamente sobre las paredes para no destruir líneas finas de walkable
        walls = cv2.bitwise_not(walkable)

        # Cerrar pequeñas grietas/gaps en las paredes (MORPH_CLOSE sobre paredes)
        kernel_walls = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        walls = cv2.morphologyEx(walls, cv2.MORPH_CLOSE, kernel_walls, iterations=1)

        # Eliminar pequeños artefactos aislados en las paredes (texto, iconos residuales)
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(walls, connectivity=8)
        walls_clean = np.zeros_like(walls)
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] >= 60:
                walls_clean[labels == i] = 255
        walkable = cv2.bitwise_not(walls_clean)

        # Eliminar regiones transitables pequeñas aisladas (huecos dentro de paredes gruesas)
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(walkable, connectivity=8)
        walkable_clean = np.zeros_like(walkable)
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] >= 300:
                walkable_clean[labels == i] = 255
        self._save_debug("04_walkable_clean", walkable_clean)

        return walkable_clean

    def build_graph(self, image: np.ndarray) -> Dict:
        h, w = image.shape[:2]

        # 1. Preprocesamiento (OpenCV)
        cleaned = self.remove_color_annotations(image)
        walkable = self.get_walkable_area(cleaned)
        walls = cv2.bitwise_not(walkable)
        dist_transform = cv2.distanceTransform(walkable, cv2.DIST_L2, 5)

        # Dummy closed labels/closed walkable for compatibility
        walkable_closed = walkable.copy()
        labels_closed = np.zeros_like(walkable)

        # 2. OCR (opcional)
        ocr_text = ""
        try:
            import pytesseract
            ocr_text = pytesseract.image_to_string(cleaned)
        except Exception:
            pass

        # 3. Qwen2.5-VL 7B via Ollama
        # Encode original full-color image
        _, buf_orig = cv2.imencode('.png', image)
        img_orig_b64 = base64.b64encode(buf_orig).decode('utf-8')

        # Encode walkable mask
        _, buf_walk = cv2.imencode('.png', walkable)
        img_walk_b64 = base64.b64encode(buf_walk).decode('utf-8')

        prompt = f"""You are an expert floorplan graph builder and layout analyzer.
You are provided with two images of the same floorplan of size {w}x{h} pixels:
1. The first image is the original full-color floorplan containing store names, room labels, and exit signs.
2. The second image is a binary walkable area mask where white (255) represents walkable space and black (0) represents walls/obstacles.

Tasks:
1. Identify all distinct rooms, corridors, and open spaces as nodes.
2. Place a node inside each room or store. The coordinate (x, y) should be exactly at the center of the room/store.
3. For each store/room name or number visible in the first image, create a node, and list it in the "tiendas" array.
4. Construct a navigation graph (edges) connecting these nodes. Connections must follow walkable corridors and doorways (white pixels in the second image) in straight lines. Connections MUST NOT cross black wall pixels.
5. Store names in "tiendas" must correspond to text visible in the first image (and refer to the OCR text below).

OCR text for reference:
{ocr_text}

You must return a JSON object matching this schema:
{{
  "nodes": [
    {{
      "id": int,
      "name": "Room/Store name or 'Corridor'/'Open Space'",
      "x": float (0 to {w}),
      "y": float (0 to {h}),
      "type": "room" | "corridor" | "open_space",
      "radius": float (estimated width/radius of this space)
    }}
  ],
  "edges": [
    {{
      "source": int,
      "target": int,
      "weight": float (Euclidean distance between nodes)
    }}
  ],
  "tiendas": [
    {{
      "nombre": "Store Name",
      "x": float,
      "y": float,
      "nodo_id": int
    }}
  ]
}}

Ensure high geometric precision for coordinates (x, y). Output ONLY the raw JSON object. Do not include explanations.
"""

        nodes = []
        edges = []
        tiendas = []

        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen2.5vl:7b",
                    "prompt": prompt,
                    "images": [img_orig_b64, img_walk_b64],
                    "stream": False,
                    "format": "json"
                },
            )
            response.raise_for_status()
            resp_json = response.json()
            response_text = resp_json.get("response", "").strip()
            
            # Robustly remove markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                response_text = "\n".join(lines).strip()
                
            model_output = json.loads(response_text)

            # 4. JSON estructurado & 5. Validación
            nodes = model_output.get("nodes", [])
            edges = model_output.get("edges", [])
            tiendas = model_output.get("tiendas", [])
        except Exception as e:
            print(f"Error querying Ollama Qwen2.5-VL: {e}")
            nodes = [
                {"id": 0, "name": "Centro", "x": w / 2, "y": h / 2, "type": "open_space", "radius": 30.0}
            ]
            edges = []
            tiendas = []

        # 6. NetworkX
        self.graph = nx.Graph()
        for node in nodes:
            self.graph.add_node(node["id"], **node)
        for edge in edges:
            self.graph.add_edge(edge["source"], edge["target"], weight=edge["weight"])

        # 7. Relacionar tiendas en la base de datos (PostgreSQL)
        if tiendas:
            try:
                from database.db import PostgreDatabase
                from modules.product.models.tienda import Tienda
                from modules.product.models.product import Product

                db = PostgreDatabase()
                session = db.get_session()

                for t in tiendas:
                    nombre = t.get("nombre")
                    tx = t.get("x")
                    ty = t.get("y")
                    nid = t.get("nodo_id")

                    if not nombre:
                        continue

                    # Store mapping logic
                    db_tienda = session.query(Tienda).filter_by(nombre=nombre).first()
                    if not db_tienda:
                        db_tienda = Tienda(
                            nombre=nombre,
                            ubicacion_x=tx,
                            ubicacion_y=ty,
                            nodo_id=nid
                        )
                        session.add(db_tienda)
                        session.flush()
                    else:
                        db_tienda.ubicacion_x = tx
                        db_tienda.ubicacion_y = ty
                        db_tienda.nodo_id = nid

                    # Associate existing products matching store name (vendido_por)
                    products = session.query(Product).filter(
                        Product.vendido_por.ilike(nombre)
                    ).all()
                    for p in products:
                        if db_tienda not in p.tiendas:
                            p.tiendas.append(db_tienda)

                session.commit()
                session.close()
            except Exception as db_err:
                print(f"Error persisting tiendas/relaciones in DB: {db_err}")

        summary = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "rooms": sum(1 for n in nodes if n.get("type") == "room"),
            "corridors": sum(1 for n in nodes if n.get("type") == "corridor"),
            "open_spaces": sum(1 for n in nodes if n.get("type") == "open_space"),
        }

        return {
            "nodes": nodes, "edges": edges, "summary": summary,
            "binary": walkable, "walls": walls,
            "walkable_closed": walkable_closed, "labels_closed": labels_closed,
            "dist_transform": dist_transform,
        }
