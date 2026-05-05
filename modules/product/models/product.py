from sqlalchemy import Column, Integer, String, JSON, Table, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
from typing import List
from .image_product import ImageProduct
from database.base import Base


class Product(Base):
    __tablename__ = "productos"
    
    productoid: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(255), nullable=False)
    precios: Mapped[list] = mapped_column(JSON, nullable=True)
    vendido_por: Mapped[str] = mapped_column(String(255), nullable=True)
    marca: Mapped[str] = mapped_column(String(255), nullable=True)
    url_venta: Mapped[str] = mapped_column(String(255), nullable=True)
    caracteristicas: Mapped[list] = mapped_column(JSON, nullable=True)
    categoria: Mapped[str] = mapped_column(String(255), nullable=True)
    sub_categoria: Mapped[str] = mapped_column(String(255), nullable=True)
    especificaciones: Mapped[list] = mapped_column(JSON, nullable=True)
    
    imagenes: Mapped[List["ImageProduct"]] = relationship("ImageProduct", back_populates="producto")
    
    def __repr__(self):
        return f"<Product(productoid={self.productoid}, nombre={self.nombre})>"