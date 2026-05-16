from pydantic import BaseModel

class VoiceQueryDTO(BaseModel):
    query: str