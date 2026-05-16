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
from sqlalchemy.orm.attributes import flag_modified


load_dotenv(
    dotenv_path= PROJECT_ROOT / ".env"
)

ia = IA()
database = PostgreDatabase()


async def migrate_json_to_db():
    
    session = database.get_session()
    
    all_products = session.query(Product).all()
    
    for product in all_products:
        if not product.vector_nombre:
            print(f"Actualizando producto {product.productoid}")

            vector_nombre = ia.to_vector_text(product.nombre)

            product.vector_nombre = vector_nombre.tolist()

            flag_modified(product, "vector_nombre")

            session.commit()


if __name__ == "__main__":
    asyncio.run(migrate_json_to_db())
    
    
