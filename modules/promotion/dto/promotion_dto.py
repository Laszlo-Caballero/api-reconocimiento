from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class SurpriseCreateDTO(BaseModel):
    title: str
    description: Optional[str] = None


class SurpriseResponseDTO(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    qr_code_url: Optional[str] = None

    class Config:
        from_attributes = True


class PromotionCreateDTO(BaseModel):
    title: str
    description: Optional[str] = None
    discount_code: Optional[str] = None
    qr_data: Optional[str] = None
    surprises: Optional[List[SurpriseCreateDTO]] = []


class PromotionResponseDTO(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    discount_code: Optional[str] = None
    qr_code_url: str
    created_at: datetime
    surprises: List[SurpriseResponseDTO] = []

    class Config:
        from_attributes = True


class SurprisePromotionCreateDTO(BaseModel):
    title: str
    description: Optional[str] = None
    qr_data: Optional[str] = None
    promotion_id: int


class SurprisePromotionResponseDTO(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    qr_code_url: str
    promotion_id: int

    class Config:
        from_attributes = True
