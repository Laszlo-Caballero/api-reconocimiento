from database.db import PostgreDatabase
from modules.auth.models.user import User
from typing import Optional


class AuthRepository:
    def __init__(self):
        self.db = PostgreDatabase()

    def get_user_by_username(self, username: str) -> Optional[User]:
        session = self.db.get_session()
        try:
            return session.query(User).filter(User.username == username).first()
        finally:
            session.close()

    def get_user_by_email(self, email: str) -> Optional[User]:
        session = self.db.get_session()
        try:
            return session.query(User).filter(User.email == email).first()
        finally:
            session.close()

    def create_user(self, user: User) -> User:
        session = self.db.get_session()
        try:
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
