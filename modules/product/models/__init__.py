"""
Configuración centralizada de SQLAlchemy
"""
from sqlalchemy.orm import declarative_base
from modules.product.models.product import Product
from modules.product.models.image import ImageData
from modules.product.models.image_product import ImageProduct

# Base declarativa que incluye todos los modelos
Base = declarative_base()
