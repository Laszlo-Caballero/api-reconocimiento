import os
import logging
import firebase_admin
from firebase_admin import credentials

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fastapi-app")

_firebase_app = None
firebase_initialized = False

def init_firebase():
    global _firebase_app, firebase_initialized
    if firebase_initialized:
        return True
    
    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-credentials.json")
    
    logger.info(f"[FIREBASE] Credenciales: {cred_path}")
    # Try to load from file first
    if os.path.exists(cred_path):
        try:
            cred = credentials.Certificate(cred_path)
        except Exception as e:
            logger.error(f"[FIREBASE] Error loading credentials from file: {e}")
            return False
    else:
        # Fallback: read JSON string from environment variable
        json_str = os.getenv("FIREBASE_CREDENTIALS_JSON")
        if not json_str:
            logger.warning(
                f"[FIREBASE] No se encontró el archivo de credenciales en '{cred_path}' y la variable FIREBASE_CREDENTIALS_JSON no está definida. "
                "Las notificaciones push reales no funcionarán (se usará simulación)."
            )
            return False
        try:
            import json
            # Strip surrounding quotes if present (common when using .env)
            if (json_str.startswith('\'') and json_str.endswith('\'') ) or (json_str.startswith('"') and json_str.endswith('"')):
                json_str = json_str[1:-1]
            cred_dict = json.loads(json_str)
            cred = credentials.Certificate(cred_dict)
        except Exception as e:
            logger.error(f"[FIREBASE] Error parsing credentials from env var: {e}")
            return False
    
    _firebase_app = firebase_admin.initialize_app(cred)
    firebase_initialized = True
    logger.info(f"[FIREBASE] Inicializado con éxito usando credenciales {'de archivo' if os.path.exists(cred_path) else 'de variable de entorno'}")
    return True

# Initialize at module load time
init_firebase()
