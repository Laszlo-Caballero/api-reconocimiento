import sys
from pathlib import Path

# Asegurar que el directorio raíz del proyecto está en sys.path
project_root = str(Path(__file__).resolve().parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import cv2
import uuid
import os
from io import BytesIO
from PIL import Image
from fastapi import UploadFile
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from modules.floorplan_v2.floopan import FloorPan
from database.db import PostgreDatabase
from modules.product.models.tienda import Tienda
from modules.product.models.product import Product


class FloorpanV2Service:
    def __init__(self):
        self.images_dir = Path(__file__).resolve().parent.parent.parent / "images" / "floorplan"
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.tool = FloorPan()

    def analyze_floorplan(self, file_path: str, original_filename: str) -> dict:
        try:
            # --- Leer bytes desde el archivo guardado en queqe ---
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            pil_img = Image.open(BytesIO(file_bytes))

            # 1. Preprocesar  (ahora devuelve 4 valores)
            img_bgr, img_gray, walls_mask, plan_type = self.tool.preprocess_image(pil_img)

            # 2. Detectar cuartos  (plan_type necesario para elegir algoritmo)
            rooms_cv = self.tool.detect_rooms(walls_mask, img_bgr, plan_type)

            # Guardar debug antes de llamar a la IA
            debug_path = str(self.images_dir / f"debug_{uuid.uuid4().hex[:6]}.png")
            self.tool.save_debug_image(img_bgr, rooms_cv, debug_path)

            # 3. Clasificar con IA
            rooms_ai = self.tool.classify_rooms_with_ai(file_bytes, rooms_cv)

            # 4. Construir grafo
            G = self.tool.build_floor_graph(rooms_cv, rooms_ai)

            # 5. Imagen anotada
            result_img   = self.tool.overlay_on_image(img_bgr, rooms_cv, G)
            viz_filename = f"result_v2_{uuid.uuid4().hex[:8]}.png"
            viz_path     = self.images_dir / viz_filename
            cv2.imwrite(str(viz_path), result_img)

            # Obtener dimensiones de la imagen
            w, h = pil_img.size

            # 6. Serializar grafo
            nodes = [
                {
                    "id":       int(nid),
                    "name":     d.get("name"),
                    "type":     d.get("type"),
                    "area":     float(d.get("area", 0)),
                    "centroid": [int(d["centroid"][0]), int(d["centroid"][1])],
                    "sqm":      float(d.get("sqm", 0)),
                }
                for nid, d in G.nodes(data=True)
            ]
            edges = [
                {
                    "source":          int(u),
                    "target":          int(v),
                    "weight":          float(d.get("weight", 1)),
                    "connection_type": d.get("connection_type", "proximity"),
                }
                for u, v, d in G.edges(data=True)
            ]
            summary = {
                "plan_type":    plan_type,
                "total_nodes":  len(nodes),
                "total_edges":  len(edges),
                "rooms":        sum(1 for n in nodes if n["type"] not in ["hallway","other","open_space"]),
                "corridors":    sum(1 for n in nodes if n["type"] == "hallway"),
                "open_spaces":  sum(1 for n in nodes if n["type"] in ["open_space","other"]),
            }

            response_data = {
                "nodes":              nodes,
                "edges":              edges,
                "summary":            summary,
                "visualization_url":  f"/images/floorplan/{viz_filename}",
                "debug_url":          f"/images/floorplan/{Path(debug_path).name}",
                "width":              int(w),
                "height":             int(h)
            }

            print("GUARDANDO")

            # Guardar en base de datos (PostgreSQL)
            try:

                db = PostgreDatabase()
                session = db.get_session()

                graph_json = {
                    "nodes": nodes,
                    "edges": edges,
                    "width": int(w),
                    "height": int(h),
                    "plan_type": plan_type
                }

                store_name = Path(original_filename).stem.replace("_", " ").replace("-", " ").strip()

                db_tienda = session.query(Tienda).filter_by(nombre=store_name).first()
                if not db_tienda:
                    db_tienda = Tienda(
                        nombre=store_name,
                        latitud=None,
                        longitud=None,
                        nodo_id=None,
                        grafo=graph_json,
                        ancho=int(w),
                        alto=int(h)
                    )
                    session.add(db_tienda)
                    session.flush()
                else:
                    db_tienda.latitud = None
                    db_tienda.longitud = None
                    db_tienda.nodo_id = None
                    db_tienda.grafo = graph_json
                    db_tienda.ancho = int(w)
                    db_tienda.alto = int(h)

                # Relacionar productos cuyo vendedor coincida con el nombre de la tienda
                products = session.query(Product).filter(
                    Product.vendido_por.ilike(store_name)
                ).all()
                for p in products:
                    if db_tienda not in p.tiendas:
                        p.tiendas.append(db_tienda)

                session.commit()
                session.close()
            except Exception as db_err:
                print(f"Error persisting tienda in V2: {db_err}")

            return { 
                    "status":  "success",
                    "message": f"Grafo V2 generado ({plan_type}) con Qwen2.5-VL + OpenCV",
                    "data":    jsonable_encoder(response_data),
                }

        except Exception as exc:
            import traceback
            print(traceback.format_exc())
            return {   "status":  "error",
                    "message": f"Error procesando el plano: {str(exc)}",
                    "data":    None,
                }
        finally:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error removing temp file {file_path}: {e}")
