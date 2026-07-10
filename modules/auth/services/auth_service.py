import jwt
from datetime import datetime, timedelta
import hashlib
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from modules.auth.repository.auth_repository import AuthRepository
from modules.auth.models.user import User
from modules.auth.schemas.auth_schemas import UserRegisterDTO, UserLoginDTO, UserResponse

SECRET_KEY = "SUPER_SECRET_KEY_FOR_JWT_TOKEN"
ALGORITHM = "HS256"


class AuthService:
    def __init__(self):
        self.repository = AuthRepository()

    def _hash_password(self, password: str) -> str:
        # Simple SHA256 hashing for convenience
        return hashlib.sha256(password.encode()).hexdigest()

    def _generate_token(self, user_id: int, username: str) -> str:
        payload = {
            "sub": str(user_id),
            "username": username,
            "exp": datetime.utcnow() + timedelta(days=7)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    def register(self, dto: UserRegisterDTO):
        try:
            if len(dto.password) < 6:
                return JSONResponse(content={
                    "status": "error",
                    "message": "La contraseña debe tener al menos 6 caracteres."
                }, status_code=400)

            # Verificar si existe usuario
            existing_user = self.repository.get_user_by_username(dto.username)
            if existing_user:
                return JSONResponse(content={
                    "status": "error",
                    "message": "Datos inválidos o el usuario ya existe."
                }, status_code=400)

            existing_email = self.repository.get_user_by_email(dto.email)
            if existing_email:
                return JSONResponse(content={
                    "status": "error",
                    "message": "Datos inválidos o el correo ya existe."
                }, status_code=400)

            # Crear usuario
            hashed_pwd = self._hash_password(dto.password)
            new_user = User(
                username=dto.username,
                email=dto.email,
                password_hash=hashed_pwd,
                role="USER"
            )
            saved_user = self.repository.create_user(new_user)
            
            token = self._generate_token(saved_user.usuarioid, saved_user.username)
            
            user_res = UserResponse(
                userId=saved_user.usuarioid,
                username=saved_user.username,
                email=saved_user.email,
                role=saved_user.role
            )
            
            return JSONResponse(content={
                "status": "success",
                "message": "Registro de usuario exitoso",
                "data": {
                    "accessToken": token,
                    "user": jsonable_encoder(user_res)
                }
            }, status_code=200)
        except Exception as e:
            return JSONResponse(content={
                "status": "error",
                "message": f"Error interno del servidor: {str(e)}"
            }, status_code=500)

    def login(self, dto: UserLoginDTO):
        try:
            user = self.repository.get_user_by_username(dto.username)
            if not user:
                return JSONResponse(content={
                    "status": "error",
                    "message": "Usuario o contraseña incorrectos."
                }, status_code=401)

            hashed_pwd = self._hash_password(dto.password)
            if user.password_hash != hashed_pwd:
                return JSONResponse(content={
                    "status": "error",
                    "message": "Usuario o contraseña incorrectos."
                }, status_code=401)

            token = self._generate_token(user.usuarioid, user.username)
            
            user_res = UserResponse(
                userId=user.usuarioid,
                username=user.username,
                email=user.email,
                role=user.role
            )

            return JSONResponse(content={
                "status": "success",
                "message": "Inicio de sesión exitoso",
                "data": {
                    "accessToken": token,
                    "user": jsonable_encoder(user_res)
                }
            }, status_code=200)
        except Exception as e:
            return JSONResponse(content={
                "status": "error",
                "message": f"Error interno del servidor: {str(e)}"
            }, status_code=500)
