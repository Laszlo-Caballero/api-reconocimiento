from celery import Celery

celery_app = Celery("tasks", broker="redis://localhost:6379/0", backend="redis://localhost:6379/0")

celery_app.conf.worker_concurrency = 1
celery_app.conf.worker_prefetch_multiplier = 1

import modules.floorplan_v2.floopan_v2_controller