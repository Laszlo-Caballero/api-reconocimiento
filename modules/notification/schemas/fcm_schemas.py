from pydantic import BaseModel
from typing import Optional


class FCMRegisterDTO(BaseModel):
    token: str
    platform: str

class FCMSendNotificationDTO(BaseModel):
    title: str
    body: str
    token: Optional[str] = None  # None for broadcast to all devices
