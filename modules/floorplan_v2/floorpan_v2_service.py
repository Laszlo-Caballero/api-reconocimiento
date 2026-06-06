import cv2
import numpy as np
import uuid
import os
from pathlib import Path
from PIL import Image
from fastapi import UploadFile
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from modules.floorplan_v2.floopan import FloorPan


class FloorpanV2Service:
    def __init__(self):
        self.images_dir = Path(__file__).resolve().parent.parent.parent / "images" / "floorplan"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.floorpan_tool = FloorPan()

    def analyze_floorplan(self, file: UploadFile):
        try:
            # 1. Cargar imagen y preprocess
            file_bytes = file.file.read()
            # Reset file pointer in case it's read again
            file.file.seek(0)
            
            # Cargar con PIL
            from io import BytesIO
            pil_img = Image.open(BytesIO(file_bytes))
            
            img_bgr, img_gray, processed = self.floorpan_tool.preprocess_image(pil_img)
            
            # 2. Detectar cuartos
            rooms_cv = self.floorpan_tool.detect_rooms(processed, img_bgr)
            
            # 3. Clasificar con IA
            rooms_ai = self.floorpan_tool.classify_rooms_with_ai(file_bytes, rooms_cv)
            
            # 4. Construir grafo
            G = self.floorpan_tool.build_floor_graph(rooms_cv, rooms_ai)
            
            # 5. Generar imagen anotada
            result_img = self.floorpan_tool.overlay_on_image(img_bgr, rooms_cv, G)
            
            viz_filename = f"result_v2_{uuid.uuid4().hex[:8]}.png"
            viz_path = self.images_dir / viz_filename
            cv2.imwrite(str(viz_path), result_img)
            
            # Convertir NetworkX G a formato serializable
            nodes = []
            for node_id, data in G.nodes(data=True):
                nodes.append({
                    "id": int(node_id),
                    "name": data.get("name"),
                    "type": data.get("type"),
                    "area": float(data.get("area")),
                    "centroid": [int(data.get("centroid")[0]), int(data.get("centroid")[1])],
                    "sqm": float(data.get("sqm", 0))
                })
                
            edges = []
            for u, v, data in G.edges(data=True):
                edges.append({
                    "source": int(u),
                    "target": int(v),
                    "weight": float(data.get("weight", 1)),
                    "connection_type": data.get("connection_type", "door")
                })
                
            summary = {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "rooms": sum(1 for n in nodes if n["type"] not in ["hallway", "other"]),
                "corridors": sum(1 for n in nodes if n["type"] == "hallway"),
                "open_spaces": sum(1 for n in nodes if n["type"] == "other")
            }
            
            response_data = {
                "nodes": nodes,
                "edges": edges,
                "summary": summary,
                "visualization_url": f"/images/floorplan/{viz_filename}"
            }
            
            return JSONResponse(
                content={
                    "status": "success",
                    "message": "Grafo V2 generado exitosamente con Qwen2.5-VL y OpenCV",
                    "data": jsonable_encoder(response_data)
                },
                status_code=200
            )
            
        except Exception as e:
            print(f"Error in FloorpanV2Service.analyze_floorplan: {e}")
            return JSONResponse(
                content={
                    "status": "error",
                    "message": f"Error procesando el plano: {str(e)}",
                    "data": None
                },
                status_code=500
            )
