from fastapi import APIRouter, status, UploadFile, File, Form, Depends
from modules.promotion.services.promotion_service import PromotionService
from modules.promotion.dto.promotion_dto import PromotionCreateDTO
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

    @router.delete("/{id}", status_code=status.HTTP_200_OK)
    def delete_promotion(self, id: int, current_user: User = Depends(get_current_admin_user)):
        return self.service.delete_promotion(id)
