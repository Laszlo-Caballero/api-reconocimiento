from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base


class User(Base):
    __tablename__ = "usuarios"
    
    usuarioid: Mapped[int] = mapped_column(Integer, primary_key=True, name="usuarioid")
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="USER", nullable=False)

    def __repr__(self):
        return f"<User(usuarioid={self.usuarioid}, username={self.username}, role={self.role})>"
