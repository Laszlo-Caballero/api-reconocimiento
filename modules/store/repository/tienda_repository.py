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

    def get_by_id(self, tienda_id: int) -> Optional[TiendaResponse]:
        session = self.db.get_session()
        try:
            tienda = session.query(Tienda).filter(Tienda.tiendaid == tienda_id).first()
            if tienda:
                return TiendaResponse.from_entity(tienda)
            return None
        finally:
            session.close()

    def create_tienda(self, nombre: str, latitud: float = None, longitud: float = None, ancho: int = None, alto: int = None) -> TiendaResponse:
        session = self.db.get_session()
        try:
            tienda = Tienda(
                nombre=nombre,
                latitud=latitud,
                longitud=longitud,
                ancho=ancho,
                alto=alto
            )
            session.add(tienda)
            session.commit()
            session.refresh(tienda)
            return TiendaResponse.from_entity(tienda)
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def update_tienda(self, tienda_id: int, nombre: str = None, latitud: float = None, longitud: float = None, ancho: int = None, alto: int = None) -> Optional[TiendaResponse]:
        session = self.db.get_session()
        try:
            tienda = session.query(Tienda).filter(Tienda.tiendaid == tienda_id).first()
            if not tienda:
                return None
            if nombre is not None:
                tienda.nombre = nombre
            if latitud is not None:
                tienda.latitud = latitud
            if longitud is not None:
                tienda.longitud = longitud
            if ancho is not None:
                tienda.ancho = ancho
            if alto is not None:
                tienda.alto = alto
            session.commit()
            session.refresh(tienda)
            return TiendaResponse.from_entity(tienda)
        except Exception as e:
            session.rollback()
            raise e
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

    def delete_tienda(self, tienda_id: int) -> bool:
        session = self.db.get_session()
        try:
            tienda = session.query(Tienda).filter(Tienda.tiendaid == tienda_id).first()
            if tienda:
                session.delete(tienda)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

