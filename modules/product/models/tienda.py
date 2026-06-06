from sqlalchemy import Table, Column, Integer, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import List, TYPE_CHECKING
from database.base import Base

if TYPE_CHECKING:
    from .product import Product

# Tabla de asociación muchos a muchos
producto_tienda = Table(
    "producto_tienda",
    Base.metadata,
    Column("productoid", Integer, ForeignKey("productos.productoid", ondelete="CASCADE"), primary_key=True),
    Column("tiendaid", Integer, ForeignKey("tiendas.tiendaid", ondelete="CASCADE"), primary_key=True)
)


class Tienda(Base):
    __tablename__ = "tiendas"
    
    tiendaid: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(Text, nullable=False)
    latitud: Mapped[float] = mapped_column(Float, nullable=True)
    longitud: Mapped[float] = mapped_column(Float, nullable=True)
    nodo_id: Mapped[int] = mapped_column(Integer, nullable=True)
    grafo: Mapped[dict] = mapped_column(JSON, nullable=True)
    ancho: Mapped[int] = mapped_column(Integer, nullable=True)
    alto: Mapped[int] = mapped_column(Integer, nullable=True)
    
    productos: Mapped[List["Product"]] = relationship(
        "Product",
        secondary=producto_tienda,
        back_populates="tiendas"
    )
    
    def __repr__(self):
        return f"<Tienda(tiendaid={self.tiendaid}, nombre={self.nombre})>"
