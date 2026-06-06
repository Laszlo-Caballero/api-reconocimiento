from pydantic import BaseModel
from typing import List, Optional
import json


class ImageDataResponse(BaseModel):
    imagenId: int
    url: str
    # producto: Optional["ProductResponse"] = None
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_entity(cls, entity):
        return cls(
            imagenId=entity.imagenid,
            url=entity.url,
            # producto=ProductResponse.from_entity(entity.producto) if entity.producto else None
        )


class TiendaResponse(BaseModel):
    tiendaId: int
    nombre: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    nodo_id: Optional[int] = None
    grafo: Optional[dict] = None
    ancho: Optional[int] = None
    alto: Optional[int] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_entity(cls, entity):
        # Robustly parse the grafo field if it is a JSON string
        grafo_parsed = None
        if entity.grafo:
            if isinstance(entity.grafo, str):
                try:
                    grafo_parsed = json.loads(entity.grafo)
                except Exception:
                    grafo_parsed = {"raw": entity.grafo}
            else:
                grafo_parsed = entity.grafo

        return cls(
            tiendaId=entity.tiendaid,
            nombre=entity.nombre,
            latitud=entity.latitud,
            longitud=entity.longitud,
            nodo_id=entity.nodo_id,
            grafo=grafo_parsed,
            ancho=getattr(entity, 'ancho', None),
            alto=getattr(entity, 'alto', None)
        )


class ProductResponse(BaseModel):
    productoId: int
    nombre: str
    precios: List[float]
    vendido_por: str
    marca: str
    url_venta: str
    caracteristicas: List[str]
    categoria: str
    sub_categoria: str
    especificaciones: List[str]
    imagenes: Optional[List[ImageDataResponse]] = []
    tiendas: Optional[List[TiendaResponse]] = []
    similitud: Optional[float] = None
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_entity(cls, entity):
        return cls(
            productoId=entity.productoid,
            nombre=entity.nombre,
            precios=entity.precios,
            vendido_por=entity.vendido_por,
            marca=entity.marca,
            url_venta=entity.url_venta,
            caracteristicas=entity.caracteristicas,
            categoria=entity.categoria,
            sub_categoria=entity.sub_categoria,
            especificaciones=entity.especificaciones,
            imagenes=[ImageDataResponse.from_entity(ip) for ip in entity.imagenes],
            tiendas=[TiendaResponse.from_entity(t) for t in entity.tiendas] if hasattr(entity, 'tiendas') and entity.tiendas else []
        )