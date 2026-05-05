from fastapi import FastAPI, UploadFile
from database.db import PostgreDatabase
from utils.ia import IA
from dotenv import load_dotenv
from PIL import Image
from excepts.handle import register_exception_handlers
from modules.product.product_controller import router as product_router

load_dotenv()
app = FastAPI()

db = PostgreDatabase()
ia = IA()

register_exception_handlers(app)


# Registrar rutas de productos
app.include_router(product_router)

# @app.post("/identificar")
# def identificar_producto(file: UploadFile):
#     image = Image.open(file.file)
#     vector_image = ia.to_vector_image(image)
    
#     return {"message": "Producto identificado", "vector": vector_image.tolist()}
    