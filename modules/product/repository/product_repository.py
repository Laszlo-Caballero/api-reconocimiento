from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from fastapi.encoders import jsonable_encoder
from database.db import PostgreDatabase
from modules.product.models.product import Product
from modules.product.models.image import ImageData
from typing import List, Optional
from ..schemas.schemas import ProductResponse


class ProductRepository:
    def __init__(self):
        self.db = PostgreDatabase()
    
    def create_product(self, product: Product) -> Product:
        """Crear un nuevo producto"""
        session = self.db.get_session()
        try:
            session.add(product)
            session.commit()
            session.refresh(product)
            return product
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Obtener un producto por ID"""
        session = self.db.get_session()
        try:
            product = session.query(Product).filter(Product.productoid == product_id).first()
            return product
        finally:
            session.close()
    
    def get_products_by_vector(self, array_vector: List[float], top_k: int = 5) -> List[ProductResponse]:
        """Obtener productos similares basados en un vector de características"""
        session = self.db.get_session()
        try:
            similarity_score = (
                (1- ImageData.vector.cosine_distance(array_vector)) * 100).label("similarity_score")
            # Usar pgvector para calcular similitud y obtener los top_k productos más similares
            products = session.query(Product, similarity_score).join(Product.imagenes).order_by(
                    similarity_score.desc()
            ).limit(top_k).options(
                    joinedload(Product.imagenes),
                    joinedload(Product.tiendas)
                ).all()
            
            products_res = []
            for product, score in products:
                product_response = ProductResponse.from_entity(product)
                product_response.similitud = score
                products_res.append(product_response)
            return products_res
        finally:
            session.close()
    
    def get_product_by_text_vector(self, array_vector: List[float], top_k: int = 5) -> List[ProductResponse]:
        """Obtener productos similares basados en un vector de texto"""
        session = self.db.get_session()
        try:
            similarity_score = (
                (1- Product.vector_nombre.cosine_distance(array_vector)) * 100).label("similarity_score")
            products = session.query(Product, similarity_score).order_by(
                    similarity_score.desc()
            ).limit(top_k).options(
                    joinedload(Product.imagenes),
                    joinedload(Product.tiendas)
                ).all()
            
            products_res = []
            for product, score in products:
                product_response = ProductResponse.from_entity(product)
                product_response.similitud = score
                products_res.append(product_response)
            return products_res
        finally:
            session.close()
    
    def create_image(self, image_data: ImageData) -> ImageData:
        """Crear una nueva imagen"""
        session = self.db.get_session()
        try:
            session.add(image_data)
            session.commit()
            session.refresh(image_data)
            return image_data
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_all_products(self) -> List[Product]:
        """Obtener todos los productos"""
        session = self.db.get_session()
        try:
            products = session.query(Product).all()
            return products
        finally:
            session.close()
    
    def update_product(self, product_id: int, product_data: dict) -> Optional[Product]:
        """Actualizar un producto"""
        session = self.db.get_session()
        try:
            product = session.query(Product).filter(Product.productoid == product_id).first()
            if product:
                for key, value in product_data.items():
                    if hasattr(product, key):
                        setattr(product, key, value)
                session.commit()
                session.refresh(product)
            return product
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def delete_product(self, product_id: int) -> bool:
        """Eliminar un producto"""
        session = self.db.get_session()
        try:
            product = session.query(Product).filter(Product.productoid == product_id).first()
            if product:
                session.delete(product)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def insert_image(self, image_data: ImageData) -> ImageData:
        """Insertar una nueva imagen en la base de datos"""
        session = self.db.get_session()
        try:
            session.add(image_data)
            session.commit()
            session.refresh(image_data)
            return image_data
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_products_filtered(self, query: Optional[str] = None) -> List[ProductResponse]:
        """Obtener productos filtrados por término de búsqueda en varios campos o listar todos"""
        session = self.db.get_session()
        try:
            q = session.query(Product).options(
                joinedload(Product.imagenes),
                joinedload(Product.tiendas)
            )
            if query:
                search_filter = f"%{query}%"
                q = q.filter(
                    Product.nombre.ilike(search_filter) |
                    Product.marca.ilike(search_filter) |
                    Product.categoria.ilike(search_filter) |
                    Product.sub_categoria.ilike(search_filter) |
                    Product.vendido_por.ilike(search_filter)
                )
            products = q.all()
            # Mapear a ProductResponse con similitud 100.0 por defecto
            products_res = []
            for p in products:
                prod_res = ProductResponse.from_entity(p)
                prod_res.similitud = 100.0
                products_res.append(prod_res)
            return products_res
        finally:
            session.close()