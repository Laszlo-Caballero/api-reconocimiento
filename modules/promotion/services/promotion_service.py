import os
import uuid
import requests
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi import UploadFile
from modules.promotion.repository.promotion_repository import PromotionRepository
from modules.promotion.models.promotion_model import Promotion
from modules.promotion.dto.promotion_dto import PromotionCreateDTO
from pathlib import Path


class PromotionService:
    def __init__(self):
        self.repository = PromotionRepository()
        
        # Absolute path to store images
        self.base_dir = Path(__file__).resolve().parent.parent.parent.parent
        self.promo_dir = self.base_dir / "images" / "promotions"
        os.makedirs(self.promo_dir, exist_ok=True)

    def list_promotions(self):
        try:
            promotions = self.repository.get_all_promotions()
            return JSONResponse(content={
                "status": "success",
                "message": "Promociones recuperadas con éxito",
                "data": jsonable_encoder(promotions)
            }, status_code=200)
        except Exception as e:
            return JSONResponse(content={
                "status": "error",
                "message": f"Error al recuperar promociones: {str(e)}"
            }, status_code=500)

    def create_promotion_with_qr_data(self, dto: PromotionCreateDTO):
        try:
            # Generate QR code if qr_data is provided, else empty string or a default
            qr_content = dto.qr_data if dto.qr_data else dto.title
            
            # Generate a unique name for the QR code image
            filename = f"qr_{uuid.uuid4().hex}.png"
            filepath = self.promo_dir / filename
            
            # Request QR code from free API
            qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={requests.utils.quote(qr_content)}"
            response = requests.get(qr_api_url)
            if response.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(response.content)
            else:
                raise Exception("Error al generar el código QR con el servicio externo.")

            # Construct public URL
            qr_code_url = f"/images/promotions/{filename}"

            from modules.promotion.models.promotion_model import SurprisePromotion

            promotion = Promotion(
                title=dto.title,
                description=dto.description,
                discount_code=dto.discount_code,
                qr_code_url=qr_code_url
            )
            if dto.surprises:
                promotion.surprises = [
                    SurprisePromotion(
                        title=s.title,
                        description=s.description,
                        qr_code_url=qr_code_url
                    )
                    for s in dto.surprises
                ]
            created = self.repository.create_promotion(promotion)
            return JSONResponse(content={
                "status": "success",
                "message": "Promoción creada y código QR generado con éxito",
                "data": jsonable_encoder(created)
            }, status_code=201)
        except Exception as e:
            return JSONResponse(content={
                "status": "error",
                "message": f"Error al crear promoción: {str(e)}"
            }, status_code=500)

    def create_promotion_with_upload(self, title: str, description: str = None, discount_code: str = None, file: UploadFile = None):
        try:
            if not file:
                return JSONResponse(content={
                    "status": "error",
                    "message": "Se requiere subir una imagen de código QR."
                }, status_code=400)

            # Generate unique filename for the uploaded file
            extension = file.filename.split(".")[-1]
            filename = f"custom_{uuid.uuid4().hex}.{extension}"
            filepath = self.promo_dir / filename

            # Read and save uploaded file
            contents = file.file.read()
            with open(filepath, "wb") as f:
                f.write(contents)

            # Construct public URL
            qr_code_url = f"/images/promotions/{filename}"

            promotion = Promotion(
                title=title,
                description=description,
                discount_code=discount_code,
                qr_code_url=qr_code_url
            )
            created = self.repository.create_promotion(promotion)
            return JSONResponse(content={
                "status": "success",
                "message": "Promoción con QR personalizado creada con éxito",
                "data": jsonable_encoder(created)
            }, status_code=201)
        except Exception as e:
            return JSONResponse(content={
                "status": "error",
                "message": f"Error al subir promoción: {str(e)}"
            }, status_code=500)

    def delete_promotion(self, id: int):
        try:
            # Optionally delete the file on disk
            promo = self.repository.get_promotion_by_id(id)
            if promo:
                filename = promo.qr_code_url.split("/")[-1]
                filepath = self.promo_dir / filename
                if os.path.exists(filepath):
                    os.remove(filepath)

            success = self.repository.delete_promotion(id)
            if not success:
                return JSONResponse(content={
                    "status": "error",
                    "message": "La promoción especificada no existe."
                }, status_code=404)

            return JSONResponse(content={
                "status": "success",
                "message": "Promoción eliminada con éxito"
            }, status_code=200)
        except Exception as e:
            return JSONResponse(content={
                "status": "error",
                "message": f"Error al eliminar promoción: {str(e)}"
            }, status_code=500)

    def redeem_promotion_code(self, code: str):
        try:
            promo = self.repository.get_promotion_by_code(code)
            if promo:
                if promo.surprises:
                    idx = sum(ord(c) for c in code) % len(promo.surprises)
                    chosen_surprise = promo.surprises[idx]
                    return JSONResponse(content={
                        "status": "success",
                        "message": "¡Bono especial sorpresa activado!",
                        "data": {
                            "id": chosen_surprise.id,
                            "title": chosen_surprise.title,
                            "description": chosen_surprise.description,
                            "discount_code": code,
                            "qr_code_url": promo.qr_code_url
                        }
                    }, status_code=200)

                return JSONResponse(content={
                    "status": "success",
                    "message": "¡Bono encontrado!",
                    "data": jsonable_encoder(promo)
                }, status_code=200)

            
            # Fetch surprise promos from database
            db_surprises = self.repository.get_all_surprise_promotions()
            if db_surprises:
                surprises = [
                    {
                        "id": s.id,
                        "title": s.title,
                        "description": s.description,
                        "discount_code": code,
                        "qr_code_url": s.qr_code_url
                    }
                    for s in db_surprises
                ]
            else:
                surprises = [
                    {
                        "id": -1,
                        "title": "Bono Misterioso 🎁",
                        "description": "¡Felicidades! Has desbloqueado un cupón misterioso del 15% de descuento en toda la tienda.",
                        "discount_code": code,
                        "qr_code_url": "/images/promotions/mystery_gift.png"
                    }
                ]
            
            idx = sum(ord(c) for c in code) % len(surprises)
            chosen_promo = surprises[idx]
            
            return JSONResponse(content={
                "status": "success",
                "message": "¡Bono especial sorpresa activado!",
                "data": chosen_promo
            }, status_code=200)
        except Exception as e:
            return JSONResponse(content={
                "status": "error",
                "message": f"Error al validar bono: {str(e)}"
            }, status_code=500)

    def list_surprise_promotions(self):
        try:
            surprises = self.repository.get_all_surprise_promotions()
            return JSONResponse(content={
                "status": "success",
                "message": "Promociones sorpresa recuperadas con éxito",
                "data": jsonable_encoder(surprises)
            }, status_code=200)
        except Exception as e:
            return JSONResponse(content={
                "status": "error",
                "message": f"Error al recuperar promociones sorpresa: {str(e)}"
            }, status_code=500)

    def create_surprise_promotion_with_qr_data(self, title: str, description: str = None, qr_data: str = None):
        try:
            qr_content = qr_data if qr_data else title
            filename = f"surprise_qr_{uuid.uuid4().hex}.png"
            filepath = self.promo_dir / filename
            
            qr_api_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={requests.utils.quote(qr_content)}"
            response = requests.get(qr_api_url)
            if response.status_code == 200:
                with open(filepath, "wb") as f:
                    f.write(response.content)
            else:
                raise Exception("Error al generar el código QR sorpresa.")

            qr_code_url = f"/images/promotions/{filename}"

            surprise = SurprisePromotion(
                title=title,
                description=description,
                qr_code_url=qr_code_url
            )
            created = self.repository.create_surprise_promotion(surprise)
            return JSONResponse(content={
                "status": "success",
                "message": "Promoción sorpresa creada con éxito",
                "data": jsonable_encoder(created)
            }, status_code=201)
        except Exception as e:
            return JSONResponse(content={
                "status": "error",
                "message": f"Error al crear promoción sorpresa: {str(e)}"
            }, status_code=500)

    def create_surprise_promotion_with_upload(self, title: str, description: str = None, file: UploadFile = None):
        try:
            if not file:
                return JSONResponse(content={
                    "status": "error",
                    "message": "Se requiere subir una imagen para el código QR sorpresa."
                }, status_code=400)

            extension = file.filename.split(".")[-1]
            filename = f"surprise_custom_{uuid.uuid4().hex}.{extension}"
            filepath = self.promo_dir / filename

            contents = file.file.read()
            with open(filepath, "wb") as f:
                f.write(contents)

            qr_code_url = f"/images/promotions/{filename}"

            surprise = SurprisePromotion(
                title=title,
                description=description,
                qr_code_url=qr_code_url
            )
            created = self.repository.create_surprise_promotion(surprise)
            return JSONResponse(content={
                "status": "success",
                "message": "Promoción sorpresa con QR personalizado creada con éxito",
                "data": jsonable_encoder(created)
            }, status_code=201)
        except Exception as e:
            return JSONResponse(content={
                "status": "error",
                "message": f"Error al subir promoción sorpresa: {str(e)}"
            }, status_code=500)

    def delete_surprise_promotion(self, id: int):
        try:
            surprise = self.repository.get_surprise_by_id(id)
            if surprise:
                filename = surprise.qr_code_url.split("/")[-1]
                filepath = self.promo_dir / filename
                if os.path.exists(filepath):
                    os.remove(filepath)

            success = self.repository.delete_surprise_promotion(id)
            if not success:
                return JSONResponse(content={
                    "status": "error",
                    "message": "La promoción sorpresa especificada no existe."
                }, status_code=404)

            return JSONResponse(content={
                "status": "success",
                "message": "Promoción sorpresa eliminada con éxito"
            }, status_code=200)
        except Exception as e:
            return JSONResponse(content={
                "status": "error",
                "message": f"Error al eliminar promoción sorpresa: {str(e)}"
            }, status_code=500)

