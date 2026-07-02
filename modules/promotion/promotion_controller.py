from fastapi import APIRouter, status, UploadFile, File, Form, Depends
from modules.promotion.services.promotion_service import PromotionService
from modules.promotion.dto.promotion_dto import PromotionCreateDTO, SurprisePromotionCreateDTO
from fastapi_utils.cbv import cbv
from utils.security import get_current_user, get_current_admin_user
from modules.auth.models.user import User
from typing import Optional


router = APIRouter(
    prefix="/api/promotions",
    tags=["promotions"]
)


@cbv(router)
class PromotionController:
    def __init__(self):
        self.service = PromotionService()

    @router.get("/", status_code=status.HTTP_200_OK)
    def list_promotions(self, current_user: User = Depends(get_current_user)):
        return self.service.list_promotions()

    @router.post("/", status_code=status.HTTP_201_CREATED)
    def create_promotion(self, body: PromotionCreateDTO, current_user: User = Depends(get_current_admin_user)):
        return self.service.create_promotion_with_qr_data(body)

    @router.post("/upload", status_code=status.HTTP_201_CREATED)
    def create_promotion_upload(
        self,
        title: str = Form(...),
        description: Optional[str] = Form(None),
        discount_code: Optional[str] = Form(None),
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_admin_user)
    ):
        return self.service.create_promotion_with_upload(title, description, discount_code, file)

    @router.get("/redeem/{code}", status_code=status.HTTP_200_OK)
    def redeem_promotion(self, code: str, current_user: User = Depends(get_current_user)):
        return self.service.redeem_promotion_code(code)

    @router.delete("/{id}", status_code=status.HTTP_200_OK)
    def delete_promotion(self, id: int, current_user: User = Depends(get_current_admin_user)):
        return self.service.delete_promotion(id)

    @router.get("/surprises", status_code=status.HTTP_200_OK)
    def list_surprise_promotions(self, current_user: User = Depends(get_current_user)):
        return self.service.list_surprise_promotions()

    @router.post("/surprises", status_code=status.HTTP_201_CREATED)
    def create_surprise_promotion(self, body: SurprisePromotionCreateDTO, current_user: User = Depends(get_current_admin_user)):
        return self.service.create_surprise_promotion_with_qr_data(body.title, body.description, body.qr_data)

    @router.post("/surprises/upload", status_code=status.HTTP_201_CREATED)
    def create_surprise_promotion_upload(
        self,
        title: str = Form(...),
        description: Optional[str] = Form(None),
        file: UploadFile = File(...),
        current_user: User = Depends(get_current_admin_user)
    ):
        return self.service.create_surprise_promotion_with_upload(title, description, file)

    @router.delete("/surprises/{id}", status_code=status.HTTP_200_OK)
    def delete_surprise_promotion(self, id: int, current_user: User = Depends(get_current_admin_user)):
        return self.service.delete_surprise_promotion(id)

