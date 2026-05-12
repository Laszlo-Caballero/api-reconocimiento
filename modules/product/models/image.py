from sqlalchemy import Column, Integer, String, Float, Table, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
from pgvector.sqlalchemy import Vector
from typing import List, Optional, TYPE_CHECKING
from database.base import Base

if TYPE_CHECKING:
    from .product import Product


class ImageData(Base):
    __tablename__ = "imagenes"
    
    imagenid: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    vector: Mapped[Vector] = mapped_column(Vector(512), nullable=True)
    productoid: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("productos.productoid"), nullable=True)
    producto: Mapped["Product"] = relationship("Product", back_populates="imagenes")
    
    def __repr__(self):
        return f"<ImageData(imagenid={self.imagenid}, url={self.url})>"