from typing import List, Optional
from modules.product.repository.product_repository import ProductRepository
from modules.product.models.product import Product
from modules.product.models.image import ImageData
from modules.product.dto.product_dto import ProductCreateDTO, ProductUpdateDTO, ProductDTO
from fastapi import UploadFile
from fastapi.responses import JSONResponse
from PIL import Image
from utils.ia import IA
from fastapi.encoders import jsonable_encoder
class ProductService:
    def __init__(self):
        self.repository = ProductRepository()
        self.ia = IA()
    
    def find_product_by_image_vector(self, image: UploadFile):
        image = Image.open(image.file)
        
        vector_image = self.ia.to_vector_image(image)
        
        images = self.repository.get_products_by_vector(vector_image.tolist())

        return JSONResponse(content={
                "data": jsonable_encoder(images),
                "message": "Productos encontrados exitosamente",
                "status": "success"
            }, status_code=200)
    
    def find_products_by_voice(self, query: str):
        vector_text = self.ia.to_vector_text(query)
        
        
        data = self.repository.get_product_by_text_vector(vector_text.tolist())
        
        return JSONResponse(content={
                "data": jsonable_encoder(data),
                "message": "Productos encontrados exitosamente",
                "status": "success"
            }, status_code=200)