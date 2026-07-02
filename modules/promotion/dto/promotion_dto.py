from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PromotionCreateDTO(BaseModel):
    title: str
    description: Optional[str] = None
    discount_code: Optional[str] = None
    qr_data: Optional[str] = None


class PromotionResponseDTO(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    discount_code: Optional[str] = None
    qr_code_url: str
    created_at: datetime

    class Config:
        from_attributes = True


class SurprisePromotionCreateDTO(BaseModel):
    title: str
    description: Optional[str] = None
    qr_data: Optional[str] = None


class SurprisePromotionResponseDTO(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    qr_code_url: str

    class Config:
        from_attributes = True

