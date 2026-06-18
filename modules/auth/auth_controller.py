from fastapi import APIRouter, status
from modules.auth.services.auth_service import AuthService
from modules.auth.schemas.auth_schemas import UserRegisterDTO, UserLoginDTO
from fastapi_utils.cbv import cbv

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)


@cbv(router)
class AuthController:
    def __init__(self):
        self.service = AuthService()

    @router.post("/register", status_code=status.HTTP_200_OK)
    def register(self, body: UserRegisterDTO):
        return self.service.register(body)

    @router.post("/login", status_code=status.HTTP_200_OK)
    def login(self, body: UserLoginDTO):
        return self.service.login(body)
