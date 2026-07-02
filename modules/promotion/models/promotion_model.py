from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base
from datetime import datetime
from typing import List


class Promotion(Base):
    __tablename__ = "promociones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    discount_code: Mapped[str] = mapped_column(String(100), nullable=True)
    qr_code_url: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    surprises: Mapped[List["SurprisePromotion"]] = relationship(
        "SurprisePromotion", 
        back_populates="promotion", 
        cascade="all, delete-orphan",
        lazy="joined"
    )

    def __repr__(self):
        return f"<Promotion(id={self.id}, title={self.title}, discount_code={self.discount_code})>"


class SurprisePromotion(Base):
    __tablename__ = "promociones_sorpresa"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    qr_code_url: Mapped[str] = mapped_column(String(255), nullable=True)
    promotion_id: Mapped[int] = mapped_column(Integer, ForeignKey("promociones.id", ondelete="CASCADE"), nullable=False)

    promotion: Mapped["Promotion"] = relationship("Promotion", back_populates="surprises")

    def __repr__(self):
        return f"<SurprisePromotion(id={self.id}, title={self.title})>"
