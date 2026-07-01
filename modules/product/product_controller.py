from fastapi import APIRouter, HTTPException, status, UploadFile, Depends
from modules.product.product_service import ProductService
from modules.product.dto.product_dto import ProductCreateDTO, ProductUpdateDTO, ProductDTO
from typing import List
from fastapi_utils.cbv import cbv
from .dto.voice_dto import VoiceQueryDTO
from utils.security import get_current_user, get_current_admin_user
from modules.auth.models.user import User

router = APIRouter(
    prefix="/api/products",
    tags=["products"]
)

@cbv(router)
class ProductController:
    def __init__(self):
        self.service = ProductService()
    
    @router.post("/identify", status_code=status.HTTP_200_OK)
    def identify_product_by_image(self, file: UploadFile, current_user: User = Depends(get_current_user)):
            return self.service.find_product_by_image_vector(file, current_user.usuarioid)
            
    @router.post("/voice", status_code=status.HTTP_200_OK)
    def get_products_by_voice(self, body: VoiceQueryDTO, current_user: User = Depends(get_current_user)):
            return self.service.find_products_by_voice(body.query, current_user.usuarioid)

    @router.get("/", status_code=status.HTTP_200_OK)
    def list_and_search_products(self, query: str = None, page: int = 1, limit: int = 12, current_user: User = Depends(get_current_user)):
        return self.service.search_products(query, current_user.usuarioid, page, limit)


    @router.post("/", status_code=status.HTTP_201_CREATED)
    def create_product(self, body: ProductCreateDTO, current_user: User = Depends(get_current_admin_user)):
        return self.service.create_product(body)

    @router.put("/{product_id}", status_code=status.HTTP_200_OK)
    def update_product(self, product_id: int, body: ProductUpdateDTO, current_user: User = Depends(get_current_admin_user)):
        return self.service.update_product(product_id, body)

    @router.delete("/{product_id}", status_code=status.HTTP_200_OK)
    def delete_product(self, product_id: int, current_user: User = Depends(get_current_admin_user)):
        return self.service.delete_product(product_id)


