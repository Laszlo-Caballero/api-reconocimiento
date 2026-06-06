from fastapi import APIRouter, UploadFile, status
from modules.floorplan_v2.floorpan_v2_service import FloorpanV2Service
from utils.celery_app import celery_app
import uuid
from pathlib import Path
import redis
import json

router = APIRouter(
    prefix="/api/v2/floorplan",
    tags=["floorplan_v2"]
)

service = FloorpanV2Service()

r = redis.Redis(host='localhost', port=6379, db=0)

@celery_app.task
def analyze_floorplan_service(file_path: str, original_filename: str):
    return service.analyze_floorplan(file_path, original_filename)


@router.post("/analyze", status_code=status.HTTP_200_OK)
def analyze_floorplan(file: UploadFile):
    try:
        # 1. Crear carpeta queqe si no existe
        queqe_dir = Path(__file__).resolve().parent.parent.parent / "images" / "floorplan" / "queqe"
        queqe_dir.mkdir(parents=True, exist_ok=True)

        # 2. Guardar archivo temporalmente
        file_bytes = file.file.read()
        temp_filename = f"{uuid.uuid4().hex}_{file.filename}"
        file_path = queqe_dir / temp_filename

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        # 3. Enviar ruta a Celery
        task = analyze_floorplan_service.delay(str(file_path), file.filename)
        return {
            "status": "processing",
            "message": "El análisis del plano se está procesando en segundo plano.",
            "task_id": task.id
        }
    except Exception as exc:
        import traceback
        print(traceback.format_exc())
        return {
            "status": "error",
            "message": f"Error al enviar la tarea de análisis del plano: {str(exc)}",
            "task_id": None
        }

@router.get("/result/{task_id}", status_code=status.HTTP_200_OK)
def get_analysis_result(task_id: str):
    try:
        task_result = celery_app.AsyncResult(task_id)
        if task_result.state == "PENDING":
            return {
                "status": "processing",
                "message": "El análisis del plano aún se está procesando.",
                "data": None
            }
        elif task_result.state == "SUCCESS":
            return {
                "status": "success",
                "message": "El análisis del plano se ha completado.",
                "data": task_result.result
            }
    except Exception as exc:
        import traceback
        print(traceback.format_exc())
        return {
            "status": "error",
            "message": f"Error al obtener el resultado del análisis del plano: {str(exc)}",
            "data": None
        }

@router.get("/all_tasks", status_code=status.HTTP_200_OK)
def get_all_tasks():
    tasks = []
    
    # Celery guarda tareas con el prefijo 'celery-task-meta-'
    keys = r.keys("celery-task-meta-*")
    
    for key in keys:
        raw = r.get(key)
        if raw:
            data = json.loads(raw)
            tasks.append({
                "task_id": key.decode().replace("celery-task-meta-", ""),
                "status": data.get("status"),
                "result": data.get("result"),
                "traceback": data.get("traceback"),
            })
    
    return {"tasks": tasks, "total": len(tasks)}