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

    def list_tokens(self):
        try:
            tokens = self.repository.get_all_tokens()
            data = [
                {
                    "token_id": t.token_id,
                    "usuarioid": t.usuarioid,
                    "token": t.token,
                    "platform": t.platform
                }
                for t in tokens
            ]
            return JSONResponse(content={
                "status": "success",
                "message": "Tokens recuperados con éxito",
                "data": data
            }, status_code=200)
        except Exception as e:
            return JSONResponse(content={
                "status": "error",
                "message": f"Error al recuperar tokens: {str(e)}"
            }, status_code=500)

    def send_notification(self, title: str, body: str, token: str = None):
        try:
            if token:
                tok_obj = self.repository.get_token_by_value(token)
                tokens = [tok_obj] if tok_obj else []
                if not tokens:
                    return JSONResponse(content={
                        "status": "error",
                        "message": "El token especificado no está registrado."
                    }, status_code=404)
            else:
                tokens = self.repository.get_all_tokens()

            sent_count = len(tokens)
            print(f"[FCM SERVICE] Simulación de envío: '{title}' - '{body}' a {sent_count} dispositivos.")
            for t in tokens:
                print(f" -> Notificando a usuario {t.usuarioid} ({t.platform}) al token: {t.token[:12]}...")

            return JSONResponse(content={
                "status": "success",
                "message": f"Notificación enviada con éxito a {sent_count} dispositivos.",
                "data": {
                    "title": title,
                    "body": body,
                    "devices_notified": sent_count
                }
            }, status_code=200)
        except Exception as e:
            return JSONResponse(content={
                "status": "error",
                "message": f"Error al enviar notificación: {str(e)}"
            }, status_code=500)
