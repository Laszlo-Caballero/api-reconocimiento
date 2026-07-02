from pydantic import BaseModel
from typing import List, Optional
from modules.product.schemas.schemas import ProductResponse

class ChatMessage(BaseModel):
    role: str  # 'user', 'assistant', 'system'
    content: str

class ChatRequestDTO(BaseModel):
    messages: List[ChatMessage]

class ChatResponseDTO(BaseModel):
    response: str
    products: Optional[List[ProductResponse]] = []
