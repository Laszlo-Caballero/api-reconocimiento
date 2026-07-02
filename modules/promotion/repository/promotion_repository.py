from sqlalchemy.orm import Session
from database.db import PostgreDatabase
from modules.promotion.models.promotion_model import Promotion, SurprisePromotion
from typing import List, Optional


class PromotionRepository:
    def __init__(self):
        self.db = PostgreDatabase()

    def get_all_surprise_promotions(self) -> List[SurprisePromotion]:
        session = self.db.get_session()
        try:
            return session.query(SurprisePromotion).all()
        finally:
            session.close()

    def create_promotion(self, promotion: Promotion) -> Promotion:
        session = self.db.get_session()
        try:
            session.add(promotion)
            session.commit()
            session.refresh(promotion)
            return promotion
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_all_promotions(self) -> List[Promotion]:
        session = self.db.get_session()
        try:
            return session.query(Promotion).order_by(Promotion.created_at.desc()).all()
        finally:
            session.close()

    def get_promotion_by_id(self, promotion_id: int) -> Optional[Promotion]:
        session = self.db.get_session()
        try:
            return session.query(Promotion).filter(Promotion.id == promotion_id).first()
        finally:
            session.close()

    def get_promotion_by_code(self, discount_code: str) -> Optional[Promotion]:
        session = self.db.get_session()
        try:
            return session.query(Promotion).filter(Promotion.discount_code == discount_code).first()
        finally:
            session.close()

    def delete_promotion(self, promotion_id: int) -> bool:
        session = self.db.get_session()
        try:
            promotion = session.query(Promotion).filter(Promotion.id == promotion_id).first()
            if promotion:
                session.delete(promotion)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
