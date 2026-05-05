from fastapi import APIRouter, HTTPException, status
from modules.product.product_service import ProductService
from modules.product.dto.product_dto import ProductCreateDTO, ProductUpdateDTO, ProductDTO
from typing import List

router = APIRouter(
    prefix="/products",
    tags=["products"]
)


