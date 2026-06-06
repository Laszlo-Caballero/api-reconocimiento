import cv2
import numpy as np
import uuid
from pathlib import Path
from fastapi import UploadFile
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from modules.floorplan.graph_builder import GraphBuilder


class FloorplanService:

    def __init__(self):
        self.images_dir = Path(__file__).resolve().parent.parent.parent / "images" / "floorplan"
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def analyze_floorplan(self, file: UploadFile, open_space_threshold: int = 30,
                           min_node_distance: int = 20, door_close_kernel: int = 0):
        file_bytes = file.file.read()
        nparr = np.frombuffer(file_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            return JSONResponse(
                content={"status": "error",
                         "message": "No se pudo leer la imagen.",
                         "data": None},
                status_code=400
            )

        # Debug dir para ver pasos intermedios
        debug_dir = str(self.images_dir / "debug")

        builder = GraphBuilder(
            open_space_threshold=open_space_threshold,
            min_node_distance=min_node_distance,
            door_close_kernel=door_close_kernel,
            debug_dir=debug_dir
        )
        result = builder.build_graph(image)

        viz_filename = f"result_{uuid.uuid4().hex[:8]}.png"
        viz_path = self.images_dir / viz_filename
        self._generate_visualization(image, result, str(viz_path))

        response_data = {
            "nodes": result["nodes"],
            "edges": result["edges"],
            "summary": result["summary"],
            "visualization_url": f"/images/floorplan/{viz_filename}"
        }

        return JSONResponse(
            content={"status": "success",
                     "message": "Grafo generado exitosamente",
                     "data": jsonable_encoder(response_data)},
            status_code=200
        )

    def _generate_visualization(self, original: np.ndarray, graph_data: dict, output_path: str):
        """Grafo superpuesto sobre el plano. Sin leyendas."""
        vis = original.copy()

        COLOR_ROOM = (0, 220, 255)
        COLOR_CORRIDOR = (0, 255, 100)
        COLOR_OPEN_SPACE = (255, 180, 0)
        COLOR_EDGE = (50, 50, 255)

        nodes = graph_data["nodes"]
        edges = graph_data["edges"]
        node_map = {n["id"]: n for n in nodes}

        # Aristas
        for edge in edges:
            src = node_map.get(edge["source"])
            tgt = node_map.get(edge["target"])
            if src and tgt:
                cv2.line(vis, (int(src["x"]), int(src["y"])),
                         (int(tgt["x"]), int(tgt["y"])),
                         COLOR_EDGE, 3, cv2.LINE_AA)

        # Nodos
        for node in nodes:
            x, y = int(node["x"]), int(node["y"])
            t = node["type"]

            if t == "open_space":
                r = min(max(int(node["radius"]), 15), 60)
                overlay = vis.copy()
                cv2.circle(overlay, (x, y), r, COLOR_OPEN_SPACE, -1)
                cv2.addWeighted(overlay, 0.25, vis, 0.75, 0, vis)
                cv2.circle(vis, (x, y), r, COLOR_OPEN_SPACE, 2, cv2.LINE_AA)
            elif t == "corridor":
                cv2.circle(vis, (x, y), 10, COLOR_CORRIDOR, -1, cv2.LINE_AA)
                cv2.circle(vis, (x, y), 10, (0, 0, 0), 2, cv2.LINE_AA)
            else:
                cv2.circle(vis, (x, y), 10, COLOR_ROOM, -1, cv2.LINE_AA)
                cv2.circle(vis, (x, y), 10, (0, 0, 0), 2, cv2.LINE_AA)

            # ID del nodo
            cv2.putText(vis, str(node["id"]), (x + 12, y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 3, cv2.LINE_AA)
            cv2.putText(vis, str(node["id"]), (x + 12, y - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

        cv2.imwrite(output_path, vis)
