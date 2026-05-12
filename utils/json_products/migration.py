import asyncio
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from database.db import PostgreDatabase
from modules.product.repository.product_repository import ProductRepository
from utils.ia import IA
from utils.json_products.product import Product as ProductoDto
from PIL import Image
from modules.product.models.product import Product
from modules.product.models.image import ImageData
from dotenv import load_dotenv


load_dotenv(
    dotenv_path= PROJECT_ROOT / ".env"
)

database = PostgreDatabase()
repository = ProductRepository()
ia = IA()


async def migrate_json_to_db():
    with open("utils/json_products/products_detailed.json", "r", encoding="utf-8") as f:
        products_data = json.load(f)
    
    products = [ProductoDto(**product) for product in products_data]
    aux = 0
    
    for product in products:
        aux += 1
        print(f"Migrando producto {aux}/{len(products)}: {product.name}")
        
        try:
            vectors = []
        
            for image_path in product.images:
                image = Image.open(f"utils/json_products/{image_path}")
                vector = ia.to_vector_image(image)
                
                vectors.append({
                    "image_path": image_path,
                    "vector": vector.tolist()
                })
                
            new_product = Product(
                nombre=product.name,
                precios=product.price,
                vendido_por=product.buy_by,
                marca=product.brand,
                url_venta=product.url,
                caracteristicas=product.caracteristics,
                especificaciones=product.spects,
                categoria=product.category,
                sub_categoria=product.sub_category,
            )
            
            save_product = repository.create_product(new_product)
            
            for vector_data in vectors:
                
                new_image = ImageData(
                    url=vector_data["image_path"],
                    vector=vector_data["vector"],
                    producto=save_product
                )
                
                repository.create_image(new_image)
            
        except Exception as e:
            print(f"Error al migrar producto {product.name}: {e}")    
        
        
if __name__ == "__main__":
    asyncio.run(migrate_json_to_db())