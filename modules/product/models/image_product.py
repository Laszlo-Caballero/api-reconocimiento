from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
from database.base import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .image import ImageData
    from .product import Product


class ImageProduct(Base):
    __tablename__ = "producto_imagen"
    
    producto_imagenid: Mapped[int] = mapped_column(Integer, primary_key=True)
    productoid: Mapped[int] = mapped_column(Integer, ForeignKey("productos.productoid"), nullable=False)
    imagenid: Mapped[int] = mapped_column(Integer, ForeignKey("imagenes.imagenid"), nullable=False)
    
    imagen: Mapped["ImageData"] = relationship("ImageData", back_populates="productos")
    producto: Mapped["Product"] = relationship("Product", back_populates="imagenes")
    
    def __repr__(self):
        return f"<ImageProduct(producto_imagenid={self.producto_imagenid}, productoid={self.productoid}, imagenid={self.imagenid})>"