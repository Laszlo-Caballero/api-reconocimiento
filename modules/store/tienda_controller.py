from fastapi import APIRouter, status, Depends
from modules.store.tienda_service import TiendaService
from fastapi_utils.cbv import cbv
from pydantic import BaseModel
from typing import Optional
from utils.security import get_current_admin_user
from modules.auth.models.user import User


router = APIRouter(
    prefix="/api/stores",
    tags=["stores"]
)


class CreateTiendaDTO(BaseModel):
    nombre: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    ancho: Optional[int] = None
    alto: Optional[int] = None


class UpdateTiendaDTO(BaseModel):
    nombre: Optional[str] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    ancho: Optional[int] = None
    alto: Optional[int] = None


class UpdateTiendaLocationDTO(BaseModel):
    latitud: float
    longitud: float


@cbv(router)
class TiendaController:
    def __init__(self):
        self.service = TiendaService()

    @router.get("/", status_code=status.HTTP_200_OK)
    def list_stores(self, seller_name: str = None):
        return self.service.list_tiendas(seller_name)

    @router.get("/{store_id}", status_code=status.HTTP_200_OK)
    def get_store(self, store_id: int):
        return self.service.get_tienda(store_id)

    @router.post("/", status_code=status.HTTP_201_CREATED)
    def create_store(self, body: CreateTiendaDTO, current_user: User = Depends(get_current_admin_user)):
        return self.service.create_tienda(body.nombre, body.latitud, body.longitud, body.ancho, body.alto)

    @router.put("/{store_id}", status_code=status.HTTP_200_OK)
    def update_store(self, store_id: int, body: UpdateTiendaDTO, current_user: User = Depends(get_current_admin_user)):
        return self.service.update_tienda(store_id, body.nombre, body.latitud, body.longitud, body.ancho, body.alto)

    @router.patch("/{store_id}/location", status_code=status.HTTP_200_OK)
    def update_store_location(self, store_id: int, body: UpdateTiendaLocationDTO):
        return self.service.update_tienda_location(store_id, body.latitud, body.longitud)

    @router.delete("/{store_id}", status_code=status.HTTP_200_OK)
    def delete_store(self, store_id: int, current_user: User = Depends(get_current_admin_user)):
        return self.service.delete_tienda(store_id)
