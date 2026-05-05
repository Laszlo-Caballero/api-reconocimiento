from fastapi import APIRouter, HTTPException, status, UploadFile
from modules.product.product_service import ProductService
from modules.product.dto.product_dto import ProductCreateDTO, ProductUpdateDTO, ProductDTO
from typing import List
from fastapi_utils.cbv import cbv

router = APIRouter(
    prefix="/api/products",
    tags=["products"]
)

@cbv(router)
class ProductController:
    def __init__(self):
        self.service = ProductService()
    
    @router.post("/identify", status_code=status.HTTP_200_OK)
    def identify_product_by_image(self, file: UploadFile):
            return self.service.find_product_by_image_vector(file)


