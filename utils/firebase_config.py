import os
import logging
import firebase_admin
from firebase_admin import credentials

logger = logging.getLogger("fastapi-app")

_firebase_app = None
firebase_initialized = False

def init_firebase():
    global _firebase_app, firebase_initialized
    if firebase_initialized:
        return True
    
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
    
    if not os.path.exists(cred_path):
        logger.warning(
            f"[FIREBASE] No se encontró el archivo de credenciales en '{cred_path}'. "
            "Las notificaciones push reales no funcionarán (se usará simulación)."
        )
        return False
    
    try:
        cred = credentials.Certificate(cred_path)
        _firebase_app = firebase_admin.initialize_app(cred)
        firebase_initialized = True
        logger.info(f"[FIREBASE] Inicializado con éxito usando '{cred_path}'")
        return True
    except Exception as e:
        logger.error(f"[FIREBASE] Error al inicializar el SDK de Firebase: {e}")
        return False

# Initialize at module load time
init_firebase()
