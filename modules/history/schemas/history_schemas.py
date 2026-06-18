from pydantic import BaseModel
from typing import List, Optional


class HistoryResponse(BaseModel):
    id: int
    title: str
    time: str
    description: Optional[str] = None
    tags: Optional[List[str]] = []
    image: Optional[str] = None
    category: Optional[str] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_entity(cls, entity):
        return cls(
            id=entity.id,
            title=entity.title,
            time=entity.time,
            description=entity.description,
            tags=entity.tags if entity.tags else [],
            image=entity.image,
            category=entity.category
        )
