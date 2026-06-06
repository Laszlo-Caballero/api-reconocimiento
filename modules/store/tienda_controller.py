from fastapi import APIRouter, status
from modules.store.tienda_service import TiendaService
from fastapi_utils.cbv import cbv
from pydantic import BaseModel


router = APIRouter(
    prefix="/api/stores",
    tags=["stores"]
)


class UpdateTiendaLocationDTO(BaseModel):
    latitud: float
    longitud: float


@cbv(router)
class TiendaController:
    def __init__(self):
        self.service = TiendaService()

    @router.get("/", status_code=status.HTTP_200_OK)
    def list_stores(self):
        return self.service.list_tiendas()

    @router.patch("/{store_id}/location", status_code=status.HTTP_200_OK)
    def update_store_location(self, store_id: int, body: UpdateTiendaLocationDTO):
        return self.service.update_tienda_location(store_id, body.latitud, body.longitud)
