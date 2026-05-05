from pydantic import BaseModel
from typing import List, Optional


class ImageDataResponse(BaseModel):
    imagenId: int
    url: str
    productos: Optional[List["ImageProductResponse"]] = []
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_entity(cls, entity):
        return cls(
            imagenId=entity.imagenid,
            url=entity.url,
            productos=[ImageProductResponse.from_entity(ip) for ip in entity.productos]
        )

class ImageProductResponse(BaseModel):
    producto_imagenId: int
    productoId: int
    imagenId: int
    producto: Optional["ProductResponse"] = None
    
    class Config:
        from_attributes = True
        
    @classmethod
    def from_entity(cls, entity):
        return cls(
            producto_imagenId=entity.producto_imagenid,
            productoId=entity.productoid,
            imagenId=entity.imagenid,
            producto=ProductResponse.from_entity(entity.producto) if entity.producto else None
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
    # imagenes: Optional[List[ImageProductResponse]] = []
    
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
            # imagenes=[ImageProductResponse.from_entity(ip) for ip in entity.imagenes]
        )