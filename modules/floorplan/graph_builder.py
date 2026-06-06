import cv2
import numpy as np
import networkx as nx
from typing import List, Tuple, Dict
import math
import os


class GraphBuilder:
    """
    Construye un grafo a partir de una imagen de plano de planta.
    Detecta habitaciones cerrando puertas temporalmente y encontrando regiones aisladas.
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
        """Guarda imagen de debug si hay directorio configurado."""
        if self.debug_dir:
            os.makedirs(self.debug_dir, exist_ok=True)
            path = os.path.join(self.debug_dir, f"debug_{name}.png")
            cv2.imwrite(path, img)

    # =========================================================================
    # Preprocesamiento
    # =========================================================================

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
        self._save_debug("01b_color_mask", color_mask)
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
        walls = self._remove_small_components(walls, min_area=60)

        # Recuperar el área transitable
        walkable = cv2.bitwise_not(walls)

        # Eliminar regiones transitables pequeñas aisladas (huecos dentro de paredes gruesas)
        walkable = self._remove_small_components(walkable, min_area=300)
        self._save_debug("04_walkable_clean", walkable)

        return walkable

    # =========================================================================
    # Detección de habitaciones
    # =========================================================================

    def _get_door_close_kernel_size(self, image_shape: Tuple) -> int:
        if self.door_close_kernel > 0:
            return self.door_close_kernel
        h, w = image_shape[:2]
        # ~3% del lado menor (adecuado para planos reales)
        k_size = max(5, int(min(h, w) * 0.03))
        if k_size % 2 == 0:
            k_size += 1
        return k_size

    def close_doors(self, walls: np.ndarray, image_shape: Tuple) -> np.ndarray:
        """Cierra puertas dilatando paredes. Kernel auto-calculado."""
        k_size = self._get_door_close_kernel_size(image_shape)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_size, k_size))
        walls_closed = cv2.dilate(walls, kernel, iterations=2)
        self._save_debug("06_walls_closed", walls_closed)
        return walls_closed

    def detect_rooms(self, walkable_closed: np.ndarray,
                     dist_transform: np.ndarray, image_shape: Tuple) -> Tuple[List[Dict], np.ndarray]:
        """Detecta habitaciones como componentes conectados."""
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            walkable_closed, connectivity=4
        )

        h, w = image_shape[:2]
        total_area = h * w
        rooms = []

        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if area < self.min_room_area:
                continue

            cx = int(centroids[i][0])
            cy = int(centroids[i][1])
            rw = stats[i, cv2.CC_STAT_WIDTH]
            rh = stats[i, cv2.CC_STAT_HEIGHT]
            aspect = max(rw, rh) / max(min(rw, rh), 1)

            # Radio inscrito máximo
            region_mask = (labels == i).astype(np.uint8)
            max_radius = float(np.max(dist_transform * region_mask))

            # Clasificar
            if max_radius > self.open_space_threshold:
                rtype = "open_space"
            elif aspect > 5:
                rtype = "corridor"
            else:
                rtype = "room"

            rooms.append({
                "x": cx, "y": cy, "type": rtype,
                "radius": max_radius, "area": area,
                "label": i, "width": rw, "height": rh,
            })

        return rooms, labels

    # =========================================================================
    # Detección de conexiones
    # =========================================================================

    def detect_connections(self, rooms: List[Dict], labels_closed: np.ndarray,
                           walkable_original: np.ndarray) -> List[Dict]:
        """Detecta puertas entre habitaciones adyacentes."""
        edges = []
        visited = set()

        h, w = labels_closed.shape
        # Calcular el tamaño de la dilatación usada para cerrar puertas
        door_k = self._get_door_close_kernel_size(labels_closed.shape)
        wall_dilation_radius = 2 * (door_k // 2)
        expansion_radius = wall_dilation_radius + 4
        k_size = 2 * expansion_radius + 1

        dilate_k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k_size, k_size))

        for a in rooms:
            mask_a = (labels_closed == a["label"]).astype(np.uint8)
            expanded_a = cv2.dilate(mask_a, dilate_k, iterations=1)
            expansion_a = expanded_a - mask_a

            for b in rooms:
                if a["label"] >= b["label"]:
                    continue
                pair = (a["label"], b["label"])
                if pair in visited:
                    continue

                mask_b = (labels_closed == b["label"]).astype(np.uint8)

                # ¿La expansión de A toca B?
                touch = cv2.bitwise_and(expansion_a, mask_b)
                if np.sum(touch) > 0:
                    visited.add(pair)
                    w_val = math.sqrt((a["x"] - b["x"])**2 + (a["y"] - b["y"])**2)
                    edges.append({"source_label": a["label"], "target_label": b["label"],
                                  "weight": round(w_val, 1)})
                    continue

                # Fallback: expansiones se tocan en zona transitable
                expanded_b = cv2.dilate(mask_b, dilate_k, iterations=1)
                expansion_b = expanded_b - mask_b
                bridge = cv2.bitwise_and(expansion_a, expansion_b)
                bridge_walk = cv2.bitwise_and(bridge, (walkable_original > 0).astype(np.uint8))
                if np.sum(bridge_walk) > 0:
                    visited.add(pair)
                    w_val = math.sqrt((a["x"] - b["x"])**2 + (a["y"] - b["y"])**2)
                    edges.append({"source_label": a["label"], "target_label": b["label"],
                                  "weight": round(w_val, 1)})

        return edges

    # =========================================================================
    # Pipeline principal
    # =========================================================================

    def build_graph(self, image: np.ndarray) -> Dict:
        # 1. Limpiar colores
        cleaned = self.remove_color_annotations(image)

        # 2. Obtener área transitable
        walkable = self.get_walkable_area(cleaned)

        # 3. Paredes = inversión del área transitable
        walls = cv2.bitwise_not(walkable)
        self._save_debug("05_walls", walls)

        # 4. Transformada de distancia
        dist_transform = cv2.distanceTransform(walkable, cv2.DIST_L2, 5)

        # 5. Cerrar puertas
        walls_closed = self.close_doors(walls, image.shape)
        walkable_closed = cv2.bitwise_not(walls_closed)
        walkable_closed = self._remove_small_components(walkable_closed, self.min_room_area // 2)
        self._save_debug("07_walkable_closed", walkable_closed)

        # 6. Detectar habitaciones
        rooms, labels_closed = self.detect_rooms(walkable_closed, dist_transform, image.shape)

        # Debug: colorear habitaciones
        if self.debug_dir:
            debug_rooms = np.zeros((*labels_closed.shape, 3), dtype=np.uint8)
            for room in rooms:
                color = np.random.randint(50, 255, 3).tolist()
                debug_rooms[labels_closed == room["label"]] = color
            self._save_debug("08_rooms_colored", debug_rooms)

        # 7. Detectar conexiones
        raw_edges = self.detect_connections(rooms, labels_closed, walkable)

        # 8. Construir grafo
        nodes = []
        label_to_id = {}
        self.graph = nx.Graph()

        for idx, room in enumerate(rooms):
            label_to_id[room["label"]] = idx
            node = {"id": idx, "x": room["x"], "y": room["y"],
                    "type": room["type"], "radius": round(room["radius"], 1)}
            nodes.append(node)
            self.graph.add_node(idx, **node)

        edges = []
        for raw in raw_edges:
            s = label_to_id.get(raw["source_label"])
            t = label_to_id.get(raw["target_label"])
            if s is not None and t is not None:
                edge = {"source": min(s, t), "target": max(s, t), "weight": raw["weight"]}
                edges.append(edge)
                self.graph.add_edge(s, t, weight=raw["weight"])

        summary = {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "rooms": sum(1 for n in nodes if n["type"] == "room"),
            "corridors": sum(1 for n in nodes if n["type"] == "corridor"),
            "open_spaces": sum(1 for n in nodes if n["type"] == "open_space"),
        }

        return {
            "nodes": nodes, "edges": edges, "summary": summary,
            "binary": walkable, "walls": walls,
            "walkable_closed": walkable_closed, "labels_closed": labels_closed,
            "dist_transform": dist_transform,
        }

    def _remove_small_components(self, binary: np.ndarray, min_area: int) -> np.ndarray:
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
        result = np.zeros_like(binary)
        for i in range(1, num_labels):
            if stats[i, cv2.CC_STAT_AREA] >= min_area:
                result[labels == i] = 255
        return result
