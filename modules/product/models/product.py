from sqlalchemy import Column, Integer, String, JSON, Table, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
from typing import List, Optional, TYPE_CHECKING
from database.base import Base
from pgvector.sqlalchemy import Vector
from .tienda import producto_tienda

if TYPE_CHECKING:
    from .image import ImageData
    from .tienda import Tienda
    

class Product(Base):
    __tablename__ = "productos"
    
    productoid: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    precios: Mapped[list] = mapped_column(JSON, nullable=True)
    vendido_por: Mapped[str] = mapped_column(String(255), nullable=True)
    marca: Mapped[str] = mapped_column(String(255), nullable=True)
    url_venta: Mapped[str] = mapped_column(Text, nullable=True)
    caracteristicas: Mapped[list] = mapped_column(JSON, nullable=True)
    categoria: Mapped[str] = mapped_column(String(255), nullable=True)
    sub_categoria: Mapped[str] = mapped_column(String(255), nullable=True)
    especificaciones: Mapped[list] = mapped_column(JSON, nullable=True)
    vector_nombre: Mapped[Vector] = mapped_column(Vector(512), nullable=True)
    
    imagenes: Mapped[List["ImageData"]] = relationship("ImageData", back_populates="producto")
    tiendas: Mapped[List["Tienda"]] = relationship(
        "Tienda",
        secondary=producto_tienda,
        back_populates="productos"
    )
    
    def __repr__(self):
        return f"<Product(productoid={self.productoid}, nombre={self.nombre})>"