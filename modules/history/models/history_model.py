from sqlalchemy import Integer, String, Text, JSON, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from database.base import Base
from datetime import datetime


class SearchHistory(Base):
    __tablename__ = "historial_busquedas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    usuarioid: Mapped[int] = mapped_column(Integer, ForeignKey("usuarios.usuarioid", ondelete="CASCADE"), name="usuarioid", nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    time: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    tags: Mapped[list] = mapped_column(JSON, nullable=True)
    image: Mapped[str] = mapped_column(String(255), nullable=True)
    category: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SearchHistory(id={self.id}, title={self.title}, usuarioid={self.usuarioid})>"
