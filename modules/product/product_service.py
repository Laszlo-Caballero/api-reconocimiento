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
    
    def find_product_by_image_vector(self, image: UploadFile, user_id: int):
        image_opened = Image.open(image.file)
        
        vector_image = self.ia.to_vector_image(image_opened)
        
        images = self.repository.get_products_by_vector(vector_image.tolist())

        # Save to history if we have matching products
        if images:
            try:
                from modules.history.repository.history_repository import HistoryRepository
                from modules.history.models.history_model import SearchHistory
                
                top_product = images[0]
                hist_repo = HistoryRepository()
                
                tags = [top_product.categoria]
                if top_product.sub_categoria:
                    tags.append(top_product.sub_categoria)
                
                img_url = ""
                if top_product.imagenes:
                    img_url = top_product.imagenes[0].url
                
                entry = SearchHistory(
                    usuarioid=user_id,
                    title=top_product.nombre,
                    time="Hace unos momentos",
                    description=f"Identificación de producto por imagen: '{top_product.nombre}'",
                    tags=tags,
                    image=img_url,
                    category=top_product.categoria
                )
                hist_repo.create_history_entry(entry)
            except Exception as e:
                print(f"Error saving image search history: {e}")

        return JSONResponse(content={
                "data": jsonable_encoder(images),
                "message": "Productos encontrados exitosamente",
                "status": "success"
            }, status_code=200)
    
    def find_products_by_voice(self, query: str, user_id: int):
        vector_text = self.ia.to_vector_text(query)
        
        data = self.repository.get_product_by_text_vector(vector_text.tolist())
        
        # Save to history if we have matching products
        if data:
            try:
                from modules.history.repository.history_repository import HistoryRepository
                from modules.history.models.history_model import SearchHistory
                
                top_product = data[0]
                hist_repo = HistoryRepository()
                
                tags = [top_product.categoria]
                if top_product.sub_categoria:
                    tags.append(top_product.sub_categoria)
                
                img_url = ""
                if top_product.imagenes:
                    img_url = top_product.imagenes[0].url
                
                entry = SearchHistory(
                    usuarioid=user_id,
                    title=top_product.nombre,
                    time="Hace unos momentos",
                    description=f"Búsqueda por voz: '{query}'",
                    tags=tags,
                    image=img_url,
                    category=top_product.categoria
                )
                hist_repo.create_history_entry(entry)
            except Exception as e:
                print(f"Error saving voice search history: {e}")

        return JSONResponse(content={
                "data": jsonable_encoder(data),
                "message": "Productos encontrados exitosamente",
                "status": "success"
            }, status_code=200)

    def search_products(self, query: Optional[str], user_id: int, page: int = 1, limit: int = 12):
        try:
            products, total = self.repository.get_products_filtered(query, page, limit)
            
            # Save to history if query is not empty and we found products
            if query and products:
                try:
                    from modules.history.repository.history_repository import HistoryRepository
                    from modules.history.models.history_model import SearchHistory
                    
                    top_product = products[0]
                    hist_repo = HistoryRepository()
                    
                    tags = [top_product.categoria]
                    if top_product.sub_categoria:
                        tags.append(top_product.sub_categoria)
                    
                    img_url = ""
                    if top_product.imagenes:
                        img_url = top_product.imagenes[0].url
                    
                    entry = SearchHistory(
                        usuarioid=user_id,
                        title=top_product.nombre,
                        time="Hace unos momentos",
                        description=f"Búsqueda de catálogo: '{query}'",
                        tags=tags,
                        image=img_url,
                        category=top_product.categoria
                    )
                    hist_repo.create_history_entry(entry)
                except Exception as e:
                    print(f"Error saving text search history: {e}")
 
            return JSONResponse(content={
                "status": "success",
                "message": "Búsqueda de catálogo realizada con éxito",
                "data": {
                    "products": jsonable_encoder(products),
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "total_pages": (total + limit - 1) // limit if limit > 0 else 1
                }
            }, status_code=200)

        except Exception as e:
            return JSONResponse(content={
                "status": "error",
                "message": f"Error interno al realizar búsqueda de catálogo: {str(e)}",
                "data": None
            }, status_code=500)

    def create_product(self, dto: ProductCreateDTO):
        try:
            vector_nombre = self.ia.to_vector_text(dto.nombre).tolist()
            product = Product(
                nombre=dto.nombre,
                precios=dto.precios,
                vendido_por=dto.vendido_por,
                marca=dto.marca,
                url_venta=dto.url_venta,
                caracteristicas=dto.caracteristicas,
                categoria=dto.categoria,
                sub_categoria=dto.sub_categoria,
                especificaciones=dto.especificaciones,
                vector_nombre=vector_nombre
            )
            created = self.repository.create_product(product)
            return JSONResponse(content={
                "status": "success",
                "message": "Producto creado con éxito",
                "data": jsonable_encoder(created)
            }, status_code=201)
        except Exception as e:
            return JSONResponse(content={
                "status": "error",
                "message": f"Error al crear el producto: {str(e)}"
            }, status_code=500)

    def update_product(self, product_id: int, dto: ProductUpdateDTO):
        try:
            update_data = {k: v for k, v in dto.model_dump().items() if v is not None}
            if "nombre" in update_data:
                vector_nombre = self.ia.to_vector_text(update_data["nombre"]).tolist()
                update_data["vector_nombre"] = vector_nombre
                
            updated = self.repository.update_product(product_id, update_data)
            if not updated:
                return JSONResponse(content={
                    "status": "error",
                    "message": "El producto especificado no existe."
                }, status_code=404)
            return JSONResponse(content={
                "status": "success",
                "message": "Producto actualizado con éxito",
                "data": jsonable_encoder(updated)
            }, status_code=200)
        except Exception as e:
            return JSONResponse(content={
                "status": "error",
                "message": f"Error al actualizar el producto: {str(e)}"
            }, status_code=500)

    def delete_product(self, product_id: int):
        try:
            success = self.repository.delete_product(product_id)
            if not success:
                return JSONResponse(content={
                    "status": "error",
                    "message": "El producto especificado no existe."
                }, status_code=404)
            return JSONResponse(content={
                "status": "success",
                "message": "Producto eliminado con éxito"
            }, status_code=200)
        except Exception as e:
            return JSONResponse(content={
                "status": "error",
                "message": f"Error al eliminar el producto: {str(e)}"
            }, status_code=500)