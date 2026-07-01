from fastapi import APIRouter, Depends, status
from modules.notification.services.fcm_service import FCMService
from modules.notification.schemas.fcm_schemas import FCMRegisterDTO, FCMSendNotificationDTO
from utils.security import get_current_user, get_current_admin_user
from modules.auth.models.user import User

router = APIRouter(
    prefix="/api/notifications",
    tags=["notifications"]
)

service = FCMService()


@router.post("/register-token", status_code=status.HTTP_200_OK)
def register_token(body: FCMRegisterDTO, current_user: User = Depends(get_current_user)):
    return service.register_token(current_user.usuarioid, body.token, body.platform)

@router.get("/tokens", status_code=status.HTTP_200_OK)
def list_tokens(current_user: User = Depends(get_current_admin_user)):
    return service.list_tokens()

@router.post("/send", status_code=status.HTTP_200_OK)
def send_notification(body: FCMSendNotificationDTO, current_user: User = Depends(get_current_admin_user)):
    return service.send_notification(body.title, body.body, body.token)
