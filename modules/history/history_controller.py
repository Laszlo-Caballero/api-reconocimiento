from fastapi import APIRouter, Depends, status, Request
from modules.history.services.history_service import HistoryService
from utils.security import get_current_user
from modules.auth.models.user import User

router = APIRouter(
    tags=["history"]
)

service = HistoryService()


# Ruta para compatibilidad y para la inconsistencia de prefijos: GET /history
@router.get("/history", status_code=status.HTTP_200_OK)
def get_user_history_root(current_user: User = Depends(get_current_user)):
    return service.get_history(current_user.usuarioid)


# Ruta estandarizada: GET /api/history
@router.get("/api/history", status_code=status.HTTP_200_OK)
def get_user_history_api(current_user: User = Depends(get_current_user)):
    return service.get_history(current_user.usuarioid)


# Ruta estandarizada: DELETE /api/history
@router.delete("/api/history", status_code=status.HTTP_200_OK)
def delete_user_history_api(current_user: User = Depends(get_current_user)):
    return service.delete_history(current_user.usuarioid)
