from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from modules.history.repository.history_repository import HistoryRepository
from modules.history.schemas.history_schemas import HistoryResponse


class HistoryService:
    def __init__(self):
        self.repository = HistoryRepository()

    def get_history(self, user_id: int):
        try:
            history_items = self.repository.get_user_history(user_id)
            data = [HistoryResponse.from_entity(item) for item in history_items]
            # Devolver listado puro según requerimiento del frontend
            return JSONResponse(content=jsonable_encoder(data), status_code=200)
        except Exception as e:
            return JSONResponse(content={
                "success": False,
                "message": f"Error interno del servidor al recuperar historial: {str(e)}"
            }, status_code=500)

    def delete_history(self, user_id: int):
        try:
            self.repository.delete_user_history(user_id)
            return JSONResponse(content={
                "success": True,
                "message": "Historial eliminado exitosamente"
            }, status_code=200)
        except Exception as e:
            return JSONResponse(content={
                "success": False,
                "message": f"Error al eliminar registros del historial: {str(e)}"
            }, status_code=500)
