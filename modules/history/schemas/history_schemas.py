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
        time_str = entity.time
        if hasattr(entity, 'created_at') and entity.created_at:
            try:
                from datetime import datetime
                now = datetime.utcnow()
                diff = now - entity.created_at
                diff_sec = diff.total_seconds()
                if diff_sec < 60:
                    time_str = "Hace unos momentos"
                else:
                    diff_min = diff_sec / 60
                    if diff_min < 60:
                        mins = int(diff_min)
                        time_str = f"Hace {mins} min"
                    else:
                        diff_hours = diff_min / 60
                        if diff_hours < 24:
                            hours = int(diff_hours)
                            time_str = f"Hace {hours} h"
                        else:
                            diff_days = diff_hours / 24
                            if diff_days < 7:
                                days = int(diff_days)
                                if days == 1:
                                    time_str = "Ayer"
                                else:
                                    time_str = f"Hace {days} d"
                            else:
                                time_str = entity.created_at.strftime("%d/%m/%Y")
            except Exception as e:
                print(f"Error calculating relative time: {e}")

        return cls(
            id=entity.id,
            title=entity.title,
            time=time_str,
            description=entity.description,
            tags=entity.tags if entity.tags else [],
            image=entity.image,
            category=entity.category
        )
