from sqlalchemy import Column, Integer, String, Float, Table, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.ext.declarative import declarative_base
from pgvector.sqlalchemy import Vector
from typing import List, Optional
from .image_product import ImageProduct
from database.base import Base



class ImageData(Base):
    __tablename__ = "imagenes"
    
    imagenid: Mapped[int] = mapped_column(Integer, primary_key=True)
    url: Mapped[str] = mapped_column(String(255), nullable=False)
    vector: Mapped[Vector] = mapped_column(Vector(512), nullable=True)
    
    productos: Mapped[List["ImageProduct"]] = relationship("ImageProduct", back_populates="imagen")
    
    def __repr__(self):
        return f"<ImageData(imagenid={self.imagenid}, url={self.url})>"