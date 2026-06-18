from fastapi.responses import JSONResponse
from modules.notification.repository.fcm_repository import FCMRepository


class FCMService:
    def __init__(self):
        self.repository = FCMRepository()

    def register_token(self, user_id: int, token: str, platform: str):
        try:
            if not token:
                return JSONResponse(content={
                    "status": "error",
                    "message": "El token provisto es nulo o inválido."
                }, status_code=400)

            self.repository.register_or_update_token(user_id, token, platform)
            return JSONResponse(content={
                "status": "success",
                "message": "Token registrado correctamente en el servidor",
                "data": []
            }, status_code=200)
        except Exception as e:
            return JSONResponse(content={
                "status": "error",
                "message": f"Error interno al guardar token en base de datos: {str(e)}"
            }, status_code=500)
