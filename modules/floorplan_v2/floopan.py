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
    """
    Pipeline completo: imagen de plano → grafo navegable.

    Soporta dos tipos de plano automáticamente:
      - Tipo A: paredes verdes brillantes + fondo blanco  (plano de evacuación estándar)
      - Tipo B: paredes grises tenues + mobiliario + zonas coloreadas  (plano de oficina foto)
    La detección del tipo se hace midiendo cuánto verde saturado hay en la imagen.
    """

    # ------------------------------------------------------------------ #
    #  Paleta de colores por tipo de espacio (BGR para OpenCV)            #
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
        "zone_red":     ( 60,  60, 200),
        "zone_blue":    (200,  80,  40),
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
        return Image.open(file.file)

    # ------------------------------------------------------------------ #
    #  2. Detección automática de tipo de plano                           #
    # ------------------------------------------------------------------ #
    def _detect_plan_type(self, img_bgr: np.ndarray, img_hsv: np.ndarray) -> str:
        """
        Retorna 'green_walls' o 'gray_photo'.
        Criterio: si > 5% de píxeles son verde saturado → tipo A.
        """
        total = img_bgr.shape[0] * img_bgr.shape[1]
        green_mask = cv2.inRange(img_hsv,
                                 np.array([38,  70, 100]),
                                 np.array([85, 255, 255]))
        ratio = np.sum(green_mask > 0) / total
        plan_type = "green_walls" if ratio > 0.05 else "gray_photo"
        print(f"[detect_plan_type] verde={ratio*100:.1f}% → tipo='{plan_type}'")
        return plan_type

    # ------------------------------------------------------------------ #
    #  3. Preprocesamiento                                                 #
    # ------------------------------------------------------------------ #
    def preprocess_image(self, image: Image.Image):
        """
        Devuelve (img_bgr, img_gray, walls_mask, plan_type).
        walls_mask es la máscara binaria de PAREDES (blanco = pared).
        """
        img_bgr  = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        img_hsv  = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

        plan_type = self._detect_plan_type(img_bgr, img_hsv)

        if plan_type == "green_walls":
            walls_mask = self._preprocess_green_walls(img_bgr, img_gray, img_hsv)
        else:
            walls_mask = self._preprocess_gray_photo(img_bgr, img_gray)

        return img_bgr, img_gray, walls_mask, plan_type

    def _preprocess_green_walls(self, img_bgr, img_gray, img_hsv) -> np.ndarray:
        """Tipo A: paredes verdes brillantes sobre fondo blanco."""
        lower_green = np.array([38,  70, 100])
        upper_green = np.array([85, 255, 255])
        green_mask  = cv2.inRange(img_hsv, lower_green, upper_green)

        # Paredes grises internas
        gray_wall = np.zeros_like(img_gray)
        gray_wall[(img_gray >= 90) & (img_gray <= 205)] = 255
        gray_wall[green_mask > 0] = 0

        all_walls = cv2.bitwise_or(green_mask, gray_wall)
        k4 = np.ones((4, 4), np.uint8)
        walls = cv2.morphologyEx(all_walls, cv2.MORPH_CLOSE, k4, iterations=3)
        walls = cv2.dilate(walls, k4, iterations=1)
        return walls

    def _preprocess_gray_photo(self, img_bgr, img_gray) -> np.ndarray:
        """
        Tipo B: plano fotográfico con paredes grises tenues y mobiliario.
        Usa Canny + zonas de color para construir la máscara de paredes.
        """
        b_ch = img_bgr[:,:,0].astype(np.float32)
        g_ch = img_bgr[:,:,1].astype(np.float32)
        r_ch = img_bgr[:,:,2].astype(np.float32)

        # Paredes oscuras por threshold global
        _, walls_gray = cv2.threshold(img_gray, 148, 255, cv2.THRESH_BINARY_INV)

        # Quitar zonas de color (rojo/azul) de la máscara de paredes
        red_px  = ((r_ch - b_ch > 12) & (r_ch - g_ch > 8) & (r_ch > 100))
        blue_px = ((b_ch - r_ch > 10) & (b_ch > g_ch)     & (b_ch > 100))
        walls_gray[red_px  > 0] = 0
        walls_gray[blue_px > 0] = 0

        # Canny para bordes finos (paredes internas)
        blurred = cv2.GaussianBlur(img_gray, (3, 3), 0)
        edges   = cv2.Canny(blurred, 20, 60)

        k3 = np.ones((3, 3), np.uint8)
        k5 = np.ones((5, 5), np.uint8)
        edges_d = cv2.dilate(edges, k3, iterations=3)
        edges_c = cv2.morphologyEx(edges_d, cv2.MORPH_CLOSE, k5, iterations=3)

        walls_all = cv2.bitwise_or(edges_c, walls_gray)
        walls_all = cv2.morphologyEx(walls_all, cv2.MORPH_CLOSE, k3, iterations=2)
        return walls_all

    # ------------------------------------------------------------------ #
    #  4. Detección de cuartos                                            #
    # ------------------------------------------------------------------ #
    def detect_rooms(self, walls_mask: np.ndarray,
                     original_img: np.ndarray,
                     plan_type: str = "green_walls") -> list:
        """
        Detecta espacios interiores.
        Para tipo B también incorpora las zonas de color (rojo/azul) como regiones.
        """
        if plan_type == "green_walls":
            return self._detect_rooms_green(walls_mask, original_img)
        else:
            return self._detect_rooms_gray(walls_mask, original_img)

    def _detect_rooms_green(self, walls_mask, original_img) -> list:
        """Detección estándar para planos con paredes verdes."""
        h_img, w_img = walls_mask.shape[:2]
        total_area   = h_img * w_img
        margin       = 15

        interior     = cv2.bitwise_not(walls_mask)
        k4           = np.ones((4, 4), np.uint8)
        interior_sep = cv2.erode(interior, k4, iterations=2)

        contours, _ = cv2.findContours(
            interior_sep, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
        )

        min_area = total_area * 0.003
        max_area = total_area * 0.50

        rooms = []; seen = []
        for cnt in contours:
            room = self._eval_contour(cnt, w_img, h_img, total_area,
                                      min_area, max_area, margin, 8, seen, len(rooms))
            if room:
                seen.append(room["centroid"])
                rooms.append(room)

        print(f"[detect_rooms_green] {len(rooms)} espacios")
        return rooms

    def _detect_rooms_gray(self, walls_mask, original_img) -> list:
        """
        Detección híbrida para planos fotográficos:
        1. Zonas de color rojo/azul → regiones de alta confianza.
        2. Zonas grises (cuartos sin color) → desde interior de paredes.
        """
        h_img, w_img = walls_mask.shape[:2]
        total_area   = h_img * w_img
        margin       = 15
        min_area     = total_area * 0.003
        max_area     = total_area * 0.55

        b_ch = original_img[:,:,0].astype(np.float32)
        g_ch = original_img[:,:,1].astype(np.float32)
        r_ch = original_img[:,:,2].astype(np.float32)

        red_px  = ((r_ch - b_ch > 12) & (r_ch - g_ch > 8) & (r_ch > 100)).astype(np.uint8) * 255
        blue_px = ((b_ch - r_ch > 10) & (b_ch > g_ch)     & (b_ch > 100)).astype(np.uint8) * 255

        k9 = np.ones((9, 9), np.uint8)
        red_filled  = cv2.morphologyEx(red_px,  cv2.MORPH_CLOSE, k9, iterations=4)
        red_filled  = cv2.dilate(red_filled,  k9, iterations=2)
        blue_filled = cv2.morphologyEx(blue_px, cv2.MORPH_CLOSE, k9, iterations=4)
        blue_filled = cv2.dilate(blue_filled, k9, iterations=2)

        k5 = np.ones((5, 5), np.uint8)
        interior     = cv2.bitwise_not(walls_mask)
        interior_sep = cv2.erode(interior, k5, iterations=1)

        cnts_gray, _ = cv2.findContours(interior_sep, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
        cnts_red,  _ = cv2.findContours(red_filled,   cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts_blue, _ = cv2.findContours(blue_filled,  cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        rooms = []; seen = []

        # Zonas de color primero (mayor prioridad)
        for cnt in sorted(cnts_red,  key=cv2.contourArea, reverse=True)[:4]:
            r = self._eval_contour(cnt, w_img, h_img, total_area,
                                   min_area, max_area, margin, 12, seen, len(rooms))
            if r:
                r["color_tag"] = "zone_red"
                seen.append(r["centroid"]); rooms.append(r)

        for cnt in sorted(cnts_blue, key=cv2.contourArea, reverse=True)[:4]:
            r = self._eval_contour(cnt, w_img, h_img, total_area,
                                   min_area, max_area, margin, 12, seen, len(rooms))
            if r:
                r["color_tag"] = "zone_blue"
                seen.append(r["centroid"]); rooms.append(r)

        # Cuartos grises (sin color)
        for cnt in sorted(cnts_gray, key=cv2.contourArea, reverse=True):
            r = self._eval_contour(cnt, w_img, h_img, total_area,
                                   min_area * 0.8, max_area, margin, 9, seen, len(rooms))
            if r:
                r["color_tag"] = "gray"
                seen.append(r["centroid"]); rooms.append(r)

        print(f"[detect_rooms_gray] {len(rooms)} espacios "
              f"({sum(1 for r in rooms if r['color_tag']=='zone_red')} rojo, "
              f"{sum(1 for r in rooms if r['color_tag']=='zone_blue')} azul, "
              f"{sum(1 for r in rooms if r['color_tag']=='gray')} gris)")
        return rooms

    def _eval_contour(self, cnt, w_img, h_img, total_area,
                      min_area, max_area, margin, max_aspect,
                      seen_centroids, current_id) -> dict | None:
        """Evalúa si un contorno es válido y lo convierte a dict de cuarto."""
        area = cv2.contourArea(cnt)
        if area < min_area or area > max_area:
            return None

        x, y, w, h = cv2.boundingRect(cnt)
        if (x <= margin or y <= margin
                or x + w >= w_img - margin
                or y + h  >= h_img - margin):
            return None

        if max(w, h) / (min(w, h) + 1) > max_aspect:
            return None

        M = cv2.moments(cnt)
        if M["m00"] == 0:
            return None

        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])

        dedup_dist = 55
        if any(abs(cx - px) < dedup_dist and abs(cy - py) < dedup_dist
               for px, py in seen_centroids):
            return None

        peri   = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * peri, True)

        return {
            "id":        current_id,
            "contour":   cnt,
            "approx":    approx,
            "area":      area,
            "bbox":      (x, y, w, h),
            "centroid":  (cx, cy),
            "vertices":  len(approx),
            "color_tag": "unknown",
        }

    # ------------------------------------------------------------------ #
    #  5. Clasificación con Qwen2.5-VL (Ollama)                          #
    # ------------------------------------------------------------------ #
    def classify_rooms_with_ai(self, image_bytes: bytes, rooms_data: list) -> dict:
        rooms_summary = [
            {
                "id":       r["id"],
                "area_px":  int(r["area"]),
                "centroid": list(r["centroid"]),
                "bbox":     list(r["bbox"]),
                "color_zone": r.get("color_tag", "unknown"),
            }
            for r in rooms_data
        ]

        prompt = (
            f"This is a floor plan image (plano de oficina / evacuación).\n"
            f"Computer vision detected {len(rooms_data)} interior spaces.\n\n"
            f"Regions — id, area_px, centroid [x,y], bbox [x,y,w,h], color_zone:\n"
            f"{json.dumps(rooms_summary, indent=2)}\n\n"
            f"'color_zone' hints: zone_red=ruta/zona roja de evacuación, "
            f"zone_blue=ruta/zona azul, gray=espacio neutro.\n\n"
            f"Instructions:\n"
            f"1. Identify each space by its position, size and color_zone.\n"
            f"2. Assign a Spanish name ('Oficina A', 'Baño', 'Pasillo', 'Sala de reuniones', etc.).\n"
            f"3. Assign a type: office | meeting_room | bathroom | hallway | "
            f"reception | storage | staircase | open_space | other.\n"
            f"4. List connected region IDs (share a door/corridor).\n"
            f"5. Estimate real area in m².\n\n"
            f"Respond ONLY with valid JSON, no markdown:\n"
            f'{{"rooms":[{{"id":0,"name":"...","type":"...","estimated_sqm":0,"connections":[]}}]}}'
        )

        response = ollama.chat(
            model="qwen2.5vl:7b",
            messages=[{
                "role":    "user",
                "content": prompt,
                "images":  [image_bytes],
            }],
            options={"temperature": 0.05, "num_predict": 2500},
        )

        raw    = response["message"]["content"].strip()
        result = self._safe_parse(raw)

        # Fallback: rellenar IDs no devueltos por la IA
        ai_ids = {r["id"] for r in result.get("rooms", [])}
        for room in rooms_data:
            if room["id"] not in ai_ids:
                rtype = room.get("color_tag", "other")
                if rtype not in ("zone_red", "zone_blue", "gray"):
                    rtype = "other"
                result.setdefault("rooms", []).append({
                    "id":            room["id"],
                    "name":          f"Espacio {room['id']}",
                    "type":          rtype if rtype in self.ROOM_COLORS_BGR else "other",
                    "estimated_sqm": round(room["area"] / 400, 1),
                    "connections":   [],
                })

        return result

    def _safe_parse(self, raw: str) -> dict:
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
        print(f"[WARN] _safe_parse falló:\n{raw[:400]}")
        return {"rooms": []}

    # ------------------------------------------------------------------ #
    #  6. Construcción del grafo                                          #
    # ------------------------------------------------------------------ #
    def build_floor_graph(self, rooms_cv: list, rooms_ai: dict) -> nx.Graph:
        G      = nx.Graph()
        ai_map = {r["id"]: r for r in rooms_ai.get("rooms", [])}

        # Nodos
        for room in rooms_cv:
            rid     = room["id"]
            ai_data = ai_map.get(rid, {})
            G.add_node(
                rid,
                name     = ai_data.get("name",  f"Espacio {rid}"),
                type     = ai_data.get("type",  room.get("color_tag", "other")),
                area     = room["area"],
                centroid = room["centroid"],
                bbox     = room["bbox"],
                sqm      = ai_data.get("estimated_sqm", 0),
            )

        # Aristas de la IA
        for room in rooms_ai.get("rooms", []):
            src = room["id"]
            for dst in room.get("connections", []):
                if G.has_node(src) and G.has_node(dst) and not G.has_edge(src, dst):
                    G.add_edge(src, dst, weight=1.0, connection_type="door")

        # Umbral de proximidad dinámico
        node_list  = list(G.nodes(data=True))
        centroids  = [d["centroid"] for _, d in node_list]
        n          = len(centroids)

        if n >= 2:
            all_dists = [
                math.dist(centroids[i], centroids[j])
                for i in range(n)
                for j in range(i + 1, n)
            ]
            avg_dist  = sum(all_dists) / len(all_dists)
            # 45% del promedio — más estricto que antes para evitar aristas largas
            threshold = avg_dist * 0.45
        else:
            threshold = 150.0

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
              f"umbral={threshold:.0f}px")
        return G

    # ------------------------------------------------------------------ #
    #  7. Pathfinding                                                      #
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
    #  8. Overlay sobre imagen                                            #
    # ------------------------------------------------------------------ #
    def overlay_on_image(self, original_img: np.ndarray,
                         rooms_cv: list, G: nx.Graph) -> np.ndarray:
        overlay = original_img.copy()

        # Rellenos semitransparentes
        for room in rooms_cv:
            rid = room["id"]
            if not G.has_node(rid):
                continue
            color      = self.get_color(G.nodes[rid]["type"])
            fill_layer = np.zeros_like(original_img)
            cv2.drawContours(fill_layer, [room["contour"]], -1, color, -1)
            overlay = cv2.addWeighted(overlay, 1.0, fill_layer, 0.28, 0)
            cv2.drawContours(overlay, [room["contour"]], -1, color, 2)

        # Aristas
        for u, v, edata in G.edges(data=True):
            if not (G.has_node(u) and G.has_node(v)):
                continue
            p1         = tuple(G.nodes[u]["centroid"])
            p2         = tuple(G.nodes[v]["centroid"])
            edge_color = (0, 140, 255) if edata.get("connection_type") == "door" \
                         else (40, 200, 220)
            cv2.line(overlay, p1, p2, edge_color, 2, cv2.LINE_AA)

        # Nodos y etiquetas
        for rid, data in G.nodes(data=True):
            cx, cy = data["centroid"]
            color  = self.get_color(data["type"])

            cv2.circle(overlay, (cx, cy), 11, color,          -1)
            cv2.circle(overlay, (cx, cy), 11, (255, 255, 255), 2)

            label        = data["name"][:16]
            font, scale  = cv2.FONT_HERSHEY_SIMPLEX, 0.42
            (tw, th), _  = cv2.getTextSize(label, font, scale, 1)
            cv2.rectangle(overlay,
                          (cx - tw // 2 - 3, cy - 26),
                          (cx + tw // 2 + 3, cy - 11),
                          (0, 0, 0), -1)
            cv2.putText(overlay, label,
                        (cx - tw // 2, cy - 13),
                        font, scale, (255, 255, 255), 1, cv2.LINE_AA)

        return overlay

    # ------------------------------------------------------------------ #
    #  9. Visualización interactiva (pyvis HTML)                         #
    # ------------------------------------------------------------------ #
    def visualize_interactive(self, G: nx.Graph,
                               output_html: str = "floor_graph.html"):
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
                    x     = int(cx), y = int(cy),
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

            net.set_options('{"physics": {"enabled": false}}')
            net.save_graph(output_html)
            print(f"[pyvis] Guardado en {output_html}")

        except Exception as exc:
            print(f"[ERROR] visualize_interactive: {exc}")

    # ------------------------------------------------------------------ #
    #  10. Debug                                                           #
    # ------------------------------------------------------------------ #
    def save_debug_image(self, original_img: np.ndarray,
                         rooms_cv: list,
                         output_path: str = "/tmp/debug_rooms.png"):
        debug   = original_img.copy()
        palette = [
            (220, 80, 50), (50, 150, 230), (40, 200, 80),
            (190, 80, 200), (210, 160, 40), (70, 80, 220),
            (210, 120, 40), (60, 190, 180), (180, 50, 180),
            (50, 180, 50), (120, 60, 200), (200, 120, 60),
        ]
        for r in rooms_cv:
            c      = palette[r["id"] % len(palette)]
            cx, cy = r["centroid"]
            cv2.drawContours(debug, [r["contour"]], -1, c, 2)
            cv2.circle(debug, (cx, cy), 8, c, -1)
            cv2.circle(debug, (cx, cy), 8, (255, 255, 255), 1)
            tag = r.get("color_tag", "")[:1].upper()
            cv2.putText(debug, f"{r['id']}{tag}",
                        (cx + 10, cy + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                        (0, 0, 0), 3)
            cv2.putText(debug, f"{r['id']}{tag}",
                        (cx + 10, cy + 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, c, 1)
        cv2.imwrite(output_path, debug)
        print(f"[debug] {output_path}")