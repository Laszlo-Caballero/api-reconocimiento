from typing import List, Optional
from modules.product.repository.product_repository import ProductRepository
from modules.product.models.product import Product
from modules.product.models.image import ImageData
from modules.product.dto.product_dto import ProductCreateDTO, ProductUpdateDTO, ProductDTO


class ProductService:
    def __init__(self):
        self.repository = ProductRepository()
    