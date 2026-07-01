from database.db import PostgreDatabase
from modules.notification.models.fcm_model import FCMToken
from typing import Optional


class FCMRepository:
    def __init__(self):
        self.db = PostgreDatabase()

    def get_token_by_value(self, token: str) -> Optional[FCMToken]:
        session = self.db.get_session()
        try:
            return session.query(FCMToken).filter(FCMToken.token == token).first()
        finally:
            session.close()

    def register_or_update_token(self, user_id: int, token_value: str, platform: str) -> FCMToken:
        session = self.db.get_session()
        try:
            existing = session.query(FCMToken).filter(FCMToken.token == token_value).first()
            if existing:
                existing.usuarioid = user_id
                existing.platform = platform
                session.commit()
                session.refresh(existing)
                return existing
            else:
                new_token = FCMToken(
                    usuarioid=user_id,
                    token=token_value,
                    platform=platform
                )
                session.add(new_token)
                session.commit()
                session.refresh(new_token)
                return new_token
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_all_tokens(self) -> list[FCMToken]:
        session = self.db.get_session()
        try:
            return session.query(FCMToken).all()
        finally:
            session.close()
