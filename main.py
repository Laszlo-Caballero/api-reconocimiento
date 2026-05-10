from fastapi import FastAPI
from database.db import PostgreDatabase
from utils.ia import IA
from dotenv import load_dotenv
from excepts.handle import register_exception_handlers
from modules.product.product_controller import router as product_router
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

load_dotenv()
app = FastAPI()

db = PostgreDatabase()
ia = IA()

BASE_DIR = Path(__file__).resolve().parent

register_exception_handlers(app)

app.mount(
    "/images",
    StaticFiles(directory=BASE_DIR / "images"),
    name="images"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(product_router)

    