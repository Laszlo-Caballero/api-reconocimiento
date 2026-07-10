from database.db import PostgreDatabase
from modules.history.models.history_model import SearchHistory
from typing import List


class HistoryRepository:
    def __init__(self):
        self.db = PostgreDatabase()

    def get_user_history(self, user_id: int) -> List[SearchHistory]:
        session = self.db.get_session()
        try:
            return session.query(SearchHistory).filter(SearchHistory.usuarioid == user_id).order_by(SearchHistory.id.desc()).all()
        finally:
            session.close()

    def create_history_entry(self, entry: SearchHistory) -> SearchHistory:
        session = self.db.get_session()
        try:
            session.add(entry)
            session.commit()
            session.refresh(entry)
            return entry
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_user_history(self, user_id: int) -> bool:
        session = self.db.get_session()
        try:
            session.query(SearchHistory).filter(SearchHistory.usuarioid == user_id).delete()
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
