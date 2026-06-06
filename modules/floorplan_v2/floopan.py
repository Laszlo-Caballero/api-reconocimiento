import cv2
import numpy as np
import math
import json
import re
import os
from PIL import Image
from fastapi import UploadFile
import ollama
import networkx as nx
from pyvis.network import Network


class FloorPan:

    # ------------------------------------------------------------------ #
    #  Colores por tipo — BGR para OpenCV, hex para pyvis                  #
    # ------------------------------------------------------------------ #
    ROOM_COLORS_BGR = {
        "office":       (200, 100,  50),
        "meeting_room": ( 50, 150, 200),
        "bathroom":     (212, 139,  59),
        "hallway":      (128, 135, 136),
        "reception":    ( 80, 180,  30),
        "storage":      ( 90,  94,  95),
        "staircase":    ( 60,  60, 180),
        "open_space":   ( 40, 200, 120),
        # legacy
        "bedroom":      (221, 119, 127),
        "living_room":  (117, 158,  29),
        "kitchen":      ( 39, 159, 239),
        "dining_room":  ( 48,  90, 216),
        "garage":       ( 90,  94,  95),
        "other":        (169, 178, 180),
    }

    def _bgr_to_hex(self, bgr: tuple) -> str:
        b, g, r = bgr
        return f"#{r:02x}{g:02x}{b:02x}"

    def get_color(self, room_type: str) -> tuple:
        return self.ROOM_COLORS_BGR.get(room_type, (169, 178, 180))

    # ------------------------------------------------------------------ #
    #  1. Carga                                                            #
    # ------------------------------------------------------------------ #
    def load_image(self, file: UploadFile) -> Image.Image:
        image = Image.open(file.file)
        return image

    # ------------------------------------------------------------------ #
    #  2. Preprocesamiento                                                 #
    # ------------------------------------------------------------------ #
    def preprocess_image(self, image: Image.Image):
        """
        Devuelve (img_bgr, img_gray, walls_mask).

        Estrategia:
          - Detectar paredes VERDES (borde exterior del plano) por HSV.
          - Detectar paredes GRISES (divisiones internas) por luminancia.
          - Unir ambas máscaras → estructura completa de paredes.
          - Cerrar huecos con morfología.
        """
        img_bgr = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        img_hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

        # -- Paredes verdes (H≈38-85, S≈70-255, V≈100-255) --
        lower_green = np.array([38,  70, 100])
        upper_green = np.array([85, 255, 255])
        green_mask = cv2.inRange(img_hsv, lower_green, upper_green)

        # -- Paredes grises internas (luminancia 90-205, no verde) --
        gray_wall = np.zeros_like(img_gray)
        gray_wall[(img_gray >= 90) & (img_gray <= 205)] = 255
        gray_wall[green_mask > 0] = 0          # quitar solapamiento con verde

        # -- Unión --
        all_walls = cv2.bitwise_or(green_mask, gray_wall)

        # -- Cerrar huecos entre segmentos de pared --
        k4 = np.ones((4, 4), np.uint8)
        walls_closed = cv2.morphologyEx(all_walls, cv2.MORPH_CLOSE, k4, iterations=3)
        walls_final  = cv2.dilate(walls_closed, k4, iterations=1)

        return img_bgr, img_gray, walls_final

    # ------------------------------------------------------------------ #
    #  3. Detección de cuartos                                            #
    # ------------------------------------------------------------------ #
    def detect_rooms(self, walls_mask, original_img) -> list:
        """
        Detecta espacios interiores (áreas blancas rodeadas de paredes).

        Filtros aplicados:
          - Área relativa al tamaño del plano (0.3 % – 50 %).
          - Sin tocar el borde de la imagen (margen 15 px).
          - Aspect ratio ≤ 8 (descarta líneas y tiras delgadas).
          - Deduplicación por proximidad de centroides (< 50 px).
        """
        h_img, w_img = walls_mask.shape[:2]
        total_area = h_img * w_img
        margin = 15

        # Interior = NOT paredes
        interior = cv2.bitwise_not(walls_mask)

        # Erosionar para separar cuartos que comparten borde fino
        k4 = np.ones((4, 4), np.uint8)
        interior_sep = cv2.erode(interior, k4, iterations=2)

        contours, _ = cv2.findContours(
            interior_sep, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
        )

        min_area = total_area * 0.003   # ≈1 200 px en 400k-px imagen
        max_area = total_area * 0.50    # excluir el plano completo como un solo blob

        rooms = []
        seen_centroids = []

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area or area > max_area:
                continue

            x, y, w, h = cv2.boundingRect(cnt)

            # Excluir si el bbox toca el borde de la imagen
            if (x <= margin or y <= margin
                    or x + w >= w_img - margin
                    or y + h  >= h_img - margin):
                continue

            # Descartar formas muy alargadas (ruido lineal)
            aspect = max(w, h) / (min(w, h) + 1)
            if aspect > 8:
                continue

            M = cv2.moments(cnt)
            if M["m00"] == 0:
                continue
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])

            # Deduplicar centroides cercanos
            if any(abs(cx - px) < 50 and abs(cy - py) < 50
                   for px, py in seen_centroids):
                continue

            seen_centroids.append((cx, cy))
            peri   = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

            rooms.append({
                "id":       len(rooms),
                "contour":  cnt,
                "approx":   approx,
                "area":     area,
                "bbox":     (x, y, w, h),
                "centroid": (cx, cy),
                "vertices": len(approx),
            })

        print(f"[detect_rooms] {len(rooms)} espacios detectados")
        return rooms

    # ------------------------------------------------------------------ #
    #  4. Clasificación con Qwen2.5-VL (Ollama)                          #
    # ------------------------------------------------------------------ #
    def classify_rooms_with_ai(self, image_bytes: bytes, rooms_data: list) -> dict:
        """
        Envía la imagen + resumen de regiones a Qwen2.5-VL.
        Devuelve {"rooms": [...]} con nombres, tipos y conexiones.
        """
        rooms_summary = [
            {
                "id":       r["id"],
                "area_px":  int(r["area"]),
                "centroid": list(r["centroid"]),
                "bbox":     list(r["bbox"]),   # x, y, w, h — ayuda al modelo a ubicarse
            }
            for r in rooms_data
        ]

        prompt = (
            f"This is an evacuation floor plan image (plano de evacuación de oficina).\n"
            f"Computer vision detected {len(rooms_data)} interior spaces by pixel coordinates.\n\n"
            f"Detected regions — id, area_px, centroid [x,y], bbox [x,y,w,h]:\n"
            f"{json.dumps(rooms_summary, indent=2)}\n\n"
            f"Instructions:\n"
            f"1. Identify each region by its position and visual context in the image.\n"
            f"2. Assign a descriptive Spanish name (e.g. 'Oficina principal', 'Baño', "
            f"'Sala de reuniones', 'Recepción', 'Pasillo central', 'Almacén').\n"
            f"3. Assign one type from: office, meeting_room, bathroom, hallway, "
            f"reception, storage, staircase, open_space, other.\n"
            f"4. List which region IDs are directly connected (share a door or opening).\n"
            f"5. Estimate real area in m² based on typical office building proportions.\n\n"
            f"Respond ONLY with valid JSON — no markdown, no extra text:\n"
            f'{{"rooms": [{{"id": 0, "name": "...", "type": "...", '
            f'"estimated_sqm": 0, "connections": []}}]}}'
        )

        response = ollama.chat(
            model="qwen2.5vl:7b",
            messages=[{
                "role":    "user",
                "content": prompt,
                "images":  [image_bytes],
            }],
            options={"temperature": 0.05, "num_predict": 2000},
        )

        raw = response["message"]["content"].strip()
        result = self._safe_parse(raw)

        # Fallback: si la IA no devuelve rooms para todos los IDs detectados,
        # rellenar con datos genéricos para no perder nodos en el grafo
        ai_ids = {r["id"] for r in result.get("rooms", [])}
        for room in rooms_data:
            if room["id"] not in ai_ids:
                result.setdefault("rooms", []).append({
                    "id":            room["id"],
                    "name":          f"Espacio {room['id']}",
                    "type":          "other",
                    "estimated_sqm": round(room["area"] / 400, 1),
                    "connections":   [],
                })

        return result

    def _safe_parse(self, raw: str) -> dict:
        """Extrae JSON aunque el modelo añada texto antes/después."""
        clean = re.sub(r"```(?:json)?", "", raw).replace("```", "").strip()
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            pass
        match = re.search(r"(\{[\s\S]*\})", clean)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        print(f"[WARN] _safe_parse falló. Raw (400 chars):\n{raw[:400]}")
        return {"rooms": []}

    # ------------------------------------------------------------------ #
    #  5. Construcción del grafo                                          #
    # ------------------------------------------------------------------ #
    def build_floor_graph(self, rooms_cv: list, rooms_ai: dict) -> nx.Graph:
        """
        Construye un grafo NetworkX donde:
          - Nodos  = espacios detectados (atributos: nombre, tipo, área, centroide…)
          - Aristas = conexiones reportadas por la IA  +  proximidad espacial (fallback)

        El umbral de proximidad es dinámico: 70 % de la distancia media entre centroides.
        """
        G = nx.Graph()
        ai_map = {r["id"]: r for r in rooms_ai.get("rooms", [])}

        # -- Añadir nodos --
        for room in rooms_cv:
            rid     = room["id"]
            ai_data = ai_map.get(rid, {})
            G.add_node(
                rid,
                name    = ai_data.get("name",  f"Espacio {rid}"),
                type    = ai_data.get("type",  "other"),
                area    = room["area"],
                centroid= room["centroid"],
                bbox    = room["bbox"],
                sqm     = ai_data.get("estimated_sqm", 0),
            )

        # -- Aristas de la IA (puertas / aperturas) --
        for room in rooms_ai.get("rooms", []):
            src = room["id"]
            for dst in room.get("connections", []):
                if G.has_node(src) and G.has_node(dst) and not G.has_edge(src, dst):
                    G.add_edge(src, dst, weight=1.0, connection_type="door")

        # -- Aristas por proximidad (fallback robusto) --
        node_list = list(G.nodes(data=True))
        centroids = [d["centroid"] for _, d in node_list]

        # Umbral dinámico: 70 % de la distancia media entre todos los pares
        if len(centroids) >= 2:
            all_dists = [
                math.dist(centroids[i], centroids[j])
                for i in range(len(centroids))
                for j in range(i + 1, len(centroids))
            ]
            threshold = (sum(all_dists) / len(all_dists)) * 0.70
        else:
            threshold = 200.0

        for i in range(len(node_list)):
            for j in range(i + 1, len(node_list)):
                id_a, data_a = node_list[i]
                id_b, data_b = node_list[j]
                if G.has_edge(id_a, id_b):
                    continue
                dist = math.dist(data_a["centroid"], data_b["centroid"])
                if dist < threshold:
                    G.add_edge(id_a, id_b,
                               weight=round(dist / 100, 2),
                               connection_type="proximity")

        print(f"[build_graph] {G.number_of_nodes()} nodos, "
              f"{G.number_of_edges()} aristas | "
              f"umbral_proximidad={threshold:.0f}px")
        return G

    # ------------------------------------------------------------------ #
    #  6. Navegación / pathfinding                                        #
    # ------------------------------------------------------------------ #
    def find_route(self, G: nx.Graph,
                   from_room_name: str,
                   to_room_name: str) -> tuple[list, list]:
        try:
            from_id = next(n for n, d in G.nodes(data=True)
                           if d["name"].lower() == from_room_name.lower())
            to_id   = next(n for n, d in G.nodes(data=True)
                           if d["name"].lower() == to_room_name.lower())
            path  = nx.shortest_path(G, from_id, to_id, weight="weight")
            names = [G.nodes[n]["name"] for n in path]
            return path, names
        except (StopIteration, nx.NetworkXNoPath):
            return [], []

    # ------------------------------------------------------------------ #
    #  7. Visualización: overlay sobre imagen original                    #
    # ------------------------------------------------------------------ #
    def overlay_on_image(self, original_img, rooms_cv: list, G: nx.Graph):
        """
        Dibuja sobre la imagen original:
          - Relleno semitransparente por cuarto (color según tipo).
          - Borde de cada contorno.
          - Aristas del grafo (naranja = puerta, amarillo = proximidad).
          - Círculo + etiqueta con fondo negro en cada nodo.
        """
        overlay = original_img.copy()

        # Rellenos semitransparentes
        for room in rooms_cv:
            rid = room["id"]
            if not G.has_node(rid):
                continue
            color = self.get_color(G.nodes[rid]["type"])
            fill_layer = np.zeros_like(original_img)
            cv2.drawContours(fill_layer, [room["contour"]], -1, color, -1)
            overlay = cv2.addWeighted(overlay, 1.0, fill_layer, 0.28, 0)
            cv2.drawContours(overlay, [room["contour"]], -1, color, 2)

        # Aristas
        for u, v, edata in G.edges(data=True):
            if not (G.has_node(u) and G.has_node(v)):
                continue
            p1 = tuple(G.nodes[u]["centroid"])
            p2 = tuple(G.nodes[v]["centroid"])
            edge_color = (0, 140, 255) if edata.get("connection_type") == "door" \
                         else (40, 200, 220)
            cv2.line(overlay, p1, p2, edge_color, 2, cv2.LINE_AA)

        # Nodos y etiquetas
        for rid, data in G.nodes(data=True):
            cx, cy = data["centroid"]
            color  = self.get_color(data["type"])

            cv2.circle(overlay, (cx, cy), 11, color,         -1)
            cv2.circle(overlay, (cx, cy), 11, (255, 255, 255), 2)

            label = data["name"][:16]
            font  = cv2.FONT_HERSHEY_SIMPLEX
            scale = 0.42
            (tw, th), _ = cv2.getTextSize(label, font, scale, 1)
            # Fondo negro para legibilidad
            cv2.rectangle(
                overlay,
                (cx - tw // 2 - 3, cy - 26),
                (cx + tw // 2 + 3, cy - 11),
                (0, 0, 0), -1,
            )
            cv2.putText(
                overlay, label,
                (cx - tw // 2, cy - 13),
                font, scale, (255, 255, 255), 1, cv2.LINE_AA,
            )

        return overlay

    # ------------------------------------------------------------------ #
    #  8. Visualización interactiva (pyvis HTML)                         #
    # ------------------------------------------------------------------ #
    def visualize_interactive(self, G: nx.Graph, output_html: str = "floor_graph.html"):
        try:
            net = Network(height="700px", width="100%",
                          bgcolor="#1a1a1a", font_color="white")

            for node_id, data in G.nodes(data=True):
                cx, cy    = data["centroid"]
                hex_color = self._bgr_to_hex(self.get_color(data["type"]))
                net.add_node(
                    node_id,
                    label = f"{data['name']}\n{data['sqm']}m²",
                    color = hex_color,
                    x     = int(cx),
                    y     = int(cy),
                    size  = int(max(20, data["sqm"] * 1.5)),
                    title = (f"Tipo: {data['type']}<br>"
                             f"Área: {data['sqm']}m²<br>"
                             f"Centroide: {data['centroid']}"),
                )

            for u, v, edata in G.edges(data=True):
                net.add_edge(
                    u, v,
                    title = edata.get("connection_type", ""),
                    color = "#FF8C00" if edata.get("connection_type") == "door"
                            else "#AAAAAA",
                )

            # Sin física para respetar posiciones reales del plano
            net.set_options('{"physics": {"enabled": false}}')
            net.save_graph(output_html)
            print(f"[pyvis] Grafo guardado en {output_html}")

        except Exception as exc:
            print(f"[ERROR] visualize_interactive: {exc}")

    # ------------------------------------------------------------------ #
    #  9. Debug: guardar imagen con contornos crudos                     #
    # ------------------------------------------------------------------ #
    def save_debug_image(self, original_img, rooms_cv: list,
                         output_path: str = "/tmp/debug_rooms.png"):
        """Útil para calibrar parámetros sin correr la IA."""
        debug = original_img.copy()
        palette = [
            (220, 80, 50), (50, 150, 230), (40, 200, 80),
            (190, 80, 200), (210, 160, 40), (70, 80, 220),
            (210, 120, 40), (60, 190, 180), (180, 50, 180), (50, 180, 50),
        ]
        for r in rooms_cv:
            c  = palette[r["id"] % len(palette)]
            cx, cy = r["centroid"]
            cv2.drawContours(debug, [r["contour"]], -1, c, 2)
            cv2.circle(debug, (cx, cy), 8, c, -1)
            cv2.circle(debug, (cx, cy), 8, (255, 255, 255), 1)
            cv2.putText(debug, str(r["id"]),
                        (cx + 10, cy + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        (0, 0, 0), 3)
            cv2.putText(debug, str(r["id"]),
                        (cx + 10, cy + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, c, 1)
        cv2.imwrite(output_path, debug)
        print(f"[debug] Imagen guardada en {output_path}")