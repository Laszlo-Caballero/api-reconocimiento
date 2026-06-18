import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al path de Python para evitar ModuleNotFoundError
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from celery import Celery

celery_app = Celery("tasks", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0")

celery_app.conf.worker_concurrency = 1
celery_app.conf.worker_prefetch_multiplier = 1

import modules.floorplan_v2.floopan_v2_controller