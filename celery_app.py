import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al path de Python para evitar ModuleNotFoundError
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import os
from celery import Celery

redis_url = os.getenv("REDIS_URL")
if not redis_url:
    redis_user = os.getenv("REDIS_USER", "")
    redis_password = os.getenv("REDIS_PASSWORD", "")
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = os.getenv("REDIS_PORT", "6379")
    redis_db = os.getenv("REDIS_DB", "0")
    
    if redis_password:
        if redis_user:
            redis_url = f"redis://{redis_user}:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
        else:
            redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
    else:
        redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"

celery_app = Celery("tasks", broker=redis_url, backend=redis_url)

celery_app.conf.worker_concurrency = 1
celery_app.conf.worker_prefetch_multiplier = 1

import modules.floorplan_v2.floopan_v2_controller