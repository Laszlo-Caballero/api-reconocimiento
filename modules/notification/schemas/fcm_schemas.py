from pydantic import BaseModel


class FCMRegisterDTO(BaseModel):
    token: str
    platform: str
