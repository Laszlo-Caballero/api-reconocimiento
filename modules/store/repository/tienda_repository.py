from database.db import PostgreDatabase
from modules.product.models.tienda import Tienda
from modules.product.schemas.schemas import TiendaResponse
from typing import List, Optional


class TiendaRepository:
    def __init__(self):
        self.db = PostgreDatabase()

    def get_all_tiendas(self, seller_name: str = None) -> List[TiendaResponse]:
        session = self.db.get_session()
        try:
            q = session.query(Tienda)
            if seller_name:
                q = q.filter(Tienda.nombre.ilike(f"%{seller_name}%"))
            tiendas = q.all()
            return [TiendaResponse.from_entity(t) for t in tiendas]
        finally:
            session.close()

    def update_location(self, tienda_id: int, latitud: float, longitud: float) -> Optional[TiendaResponse]:
        session = self.db.get_session()
        try:
            tienda = session.query(Tienda).filter(Tienda.tiendaid == tienda_id).first()
            if tienda:
                tienda.latitud = latitud
                tienda.longitud = longitud
                session.commit()
                session.refresh(tienda)
                return TiendaResponse.from_entity(tienda)
            return None
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
