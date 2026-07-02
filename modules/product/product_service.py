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

    def chat_product_search(self, messages: list, user_id: int):
        import os
        from openai import OpenAI
        import json
        import re
        
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL", "https://integrate.api.nvidia.com/v1")
        model = os.getenv("OPENAI_MODEL", "deepseek-ai/deepseek-v4-flash")
        
        if not api_key:
            return JSONResponse(content={
                "status": "error",
                "message": "OPENAI_API_KEY no configurado en el servidor",
                "data": None
            }, status_code=500)
            
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        # Paso 1: Usar DeepSeek para analizar la conversación y determinar si el usuario busca un producto.
        history_formatted = ""
        for msg in messages:
            role_str = "Usuario" if msg.role == "user" else "Asistente" if msg.role == "assistant" else "Sistema"
            history_formatted += f"{role_str}: {msg.content}\n"
            
        prompt_extraction = (
            "Analiza el siguiente historial de chat entre un Usuario y un Asistente.\n"
            "Tu tarea es identificar si en el último mensaje el usuario está buscando un producto para comprar o curiosear.\n"
            "Si es así, extrae un término de búsqueda simple y limpio en español para consultar la base de datos (máximo 4 palabras, sin preposiciones innecesarias, ej: 'zapatillas nike', 'polo rojo', 'laptop dell').\n"
            "Si no está buscando un producto (por ejemplo, si es un saludo, una pregunta general, o una despedida), devuelve un JSON vacío.\n\n"
            "Responde estrictamente en formato JSON con la siguiente estructura:\n"
            "{\n"
            "  \"buscar\": true/false,\n"
            "  \"termino\": \"<termino_extraido>\" (o null si buscar es false)\n"
            "}\n"
            "No incluyas explicaciones, markdown ni código. Solo el JSON puro."
        )
        
        search_query = None
        try:
            extraction_response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": prompt_extraction},
                    {"role": "user", "content": f"Historial de conversación:\n{history_formatted}"}
                ],
                temperature=0.1,
                max_tokens=100
            )
            content = extraction_response.choices[0].message.content.strip()
            content_clean = re.sub(r"^```json\s*|\s*```$", "", content, flags=re.MULTILINE).strip()
            res_json = json.loads(content_clean)
            if res_json.get("buscar") and res_json.get("termino"):
                search_query = res_json.get("termino")
        except Exception as e:
            print(f"Error extracting search term: {e}")
            user_msgs = [m.content for m in messages if m.role == "user"]
            if user_msgs:
                search_query = user_msgs[-1]
                
        # Buscar productos en la base de datos si tenemos un término de búsqueda
        products_found = []
        if search_query:
            try:
                # 1. Búsqueda vectorial con CLIP
                vector_text = self.ia.to_vector_text(search_query)
                vector_products = self.repository.get_product_by_text_vector(vector_text.tolist(), top_k=4)
                
                # 2. Búsqueda textual
                text_products, _ = self.repository.get_products_filtered(search_query, page=1, limit=4)
                
                # Unificar productos duplicados por productoId
                seen_ids = set()
                for p in vector_products + text_products:
                    pid = getattr(p, "productoId", getattr(p, "productoid", None))
                    if pid and pid not in seen_ids:
                        seen_ids.add(pid)
                        products_found.append(p)
            except Exception as e:
                print(f"Error performing product search: {e}")
                
        # Paso 2: Generar la respuesta final usando DeepSeek
        products_context = ""
        if products_found:
            products_list = []
            for p in products_found:
                price_str = f"${p.precios[0]}" if p.precios else "N/A"
                products_list.append(
                    f"- ID: {p.productoId}, Nombre: {p.nombre}, Marca: {p.marca}, Precio: {price_str}, Categoría: {p.categoria}, URL: {p.url_venta}"
                )
            products_context = "Productos encontrados en la tienda:\n" + "\n".join(products_list)
        else:
            if search_query:
                products_context = f"No se encontraron productos en la base de datos para la búsqueda: '{search_query}'"
            else:
                products_context = "No se ha realizado ninguna búsqueda de producto para este mensaje."
                
        system_prompt = (
            "Eres un asistente virtual amigable de una tienda, integrado en un chatbot.\n"
            "Tu objetivo es ayudar al usuario a encontrar los productos que busca y responder sus consultas.\n"
            "Te proporcionaremos la lista de productos encontrados en el inventario/base de datos relacionados con su consulta.\n"
            "Usa esta información para recomendarle productos específicos y responder con precisión.\n"
            "Si no hay productos relevantes en el contexto, explícaselo amablemente.\n\n"
            f"Contexto del inventario actual:\n{products_context}\n\n"
            "IMPORTANTE:\n"
            "- Responde de manera amigable, servicial y concisa.\n"
            "- Habla siempre en español.\n"
            "- No inventes productos que no estén en el contexto del inventario suministrado."
        )
        
        api_messages = [{"role": "system", "content": system_prompt}]
        for m in messages:
            api_messages.append({"role": m.role, "content": m.content})
            
        try:
            chat_response = client.chat.completions.create(
                model=model,
                messages=api_messages,
                temperature=0.7,
                max_tokens=1000
            )
            assistant_reply = chat_response.choices[0].message.content.strip()
            
            # Guardar en el historial de búsquedas si hubo búsqueda y productos encontrados
            if search_query and products_found:
                try:
                    from modules.history.repository.history_repository import HistoryRepository
                    from modules.history.models.history_model import SearchHistory
                    
                    top_product = products_found[0]
                    hist_repo = HistoryRepository()
                    tags = [top_product.categoria]
                    if top_product.sub_categoria:
                        tags.append(top_product.sub_categoria)
                    img_url = top_product.imagenes[0].url if top_product.imagenes else ""
                    
                    entry = SearchHistory(
                        usuarioid=user_id,
                        title=top_product.nombre,
                        time="Hace unos momentos",
                        description=f"Búsqueda por Chatbot: '{search_query}'",
                        tags=tags,
                        image=img_url,
                        category=top_product.categoria
                    )
                    hist_repo.create_history_entry(entry)
                except Exception as ex:
                    print(f"Error saving chatbot search to database history: {ex}")
            
            return JSONResponse(content={
                "status": "success",
                "message": "Respuesta de chatbot generada con éxito",
                "data": {
                    "response": assistant_reply,
                    "products": jsonable_encoder(products_found)
                }
            }, status_code=200)
            
        except Exception as e:
            return JSONResponse(content={
                "status": "error",
                "message": f"Error al generar respuesta del chatbot: {str(e)}",
                "data": None
            }, status_code=500)
