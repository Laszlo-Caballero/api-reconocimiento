from pydantic import BaseModel


class FCMRegisterDTO(BaseModel):
    token: str
    platform: str

class FCMSendNotificationDTO(BaseModel):
    title: str
    body: str
    token: str = None  # None for broadcast to all devices
