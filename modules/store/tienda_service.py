from modules.store.repository.tienda_repository import TiendaRepository
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


class TiendaService:
    def __init__(self):
        self.repository = TiendaRepository()

    def list_tiendas(self, seller_name: str = None):
        try:
            tiendas = self.repository.get_all_tiendas(seller_name)
            return JSONResponse(content={
                "data": jsonable_encoder(tiendas),
                "message": "Tiendas listadas exitosamente",
                "status": "success"
            }, status_code=200)
        except Exception as e:
            return JSONResponse(content={
                "status": "error",
                "message": f"Error al listar tiendas: {str(e)}",
                "data": None
            }, status_code=500)

    def update_tienda_location(self, tienda_id: int, latitud: float, longitud: float):
        try:
            tienda = self.repository.update_location(tienda_id, latitud, longitud)
            if not tienda:
                return JSONResponse(content={
                    "status": "error",
                    "message": f"Tienda con ID {tienda_id} no encontrada",
                    "data": None
                }, status_code=404)
            return JSONResponse(content={
                "data": jsonable_encoder(tienda),
                "message": "Ubicación de la tienda actualizada exitosamente",
                "status": "success"
            }, status_code=200)
        except Exception as e:
            return JSONResponse(content={
                "status": "error",
                "message": f"Error al actualizar ubicación de la tienda: {str(e)}",
                "data": None
            }, status_code=500)
