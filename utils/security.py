import jwt
from fastapi import Header, HTTPException, status, Depends
from modules.auth.services.auth_service import SECRET_KEY, ALGORITHM
from modules.auth.repository.auth_repository import AuthRepository
from modules.auth.models.user import User

auth_repository = AuthRepository()


def get_current_user(authorization: str = Header(...)) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header de autorización inválido"
        )
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token no contiene identificador de usuario"
            )
        
        user = auth_repository.get_user_by_username(payload.get("username"))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuario no encontrado"
            )
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido"
        )


def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if not getattr(current_user, "has_dashboard_access", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario no tiene privilegios de acceso para administrar el dashboard."
        )
    return current_user
