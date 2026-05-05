from pydantic import BaseModel
from typing import List, Optional


class ImageDataDTO(BaseModel):
    imagenId: Optional[int] = None
    url: str
    vector: Optional[List[float]] = None
    
    class Config:
        from_attributes = True


class ImageProductDTO(BaseModel):
    producto_imagenId: Optional[int] = None
    productoId: int
    imagenId: int
    
    class Config:
        from_attributes = True


class ProductDTO(BaseModel):
    productoId: Optional[int] = None
    nombre: str
    precios: List[float]
    vendido_por: str
    marca: str
    url_venta: str
    caracteristicas: List[str]
    categoria: str
    sub_categoria: str
    especificaciones: List[str]
    imagenes: Optional[List[ImageProductDTO]] = []
    
    class Config:
        from_attributes = True


class ProductCreateDTO(BaseModel):
    nombre: str
    precios: List[float]
    vendido_por: str
    marca: str
    url_venta: str
    caracteristicas: List[str]
    categoria: str
    sub_categoria: str
    especificaciones: List[str]


class ProductUpdateDTO(BaseModel):
    nombre: Optional[str] = None
    precios: Optional[List[float]] = None
    vendido_por: Optional[str] = None
    marca: Optional[str] = None
    url_venta: Optional[str] = None
    caracteristicas: Optional[List[str]] = None
    categoria: Optional[str] = None
    sub_categoria: Optional[str] = None
    especificaciones: Optional[List[str]] = None
