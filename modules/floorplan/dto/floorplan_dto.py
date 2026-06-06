from pydantic import BaseModel
from typing import List


class NodeDTO(BaseModel):
    """Representa un nodo en el grafo del plano."""
    id: int
    x: float
    y: float
    type: str  # "room", "corridor", "open_space"
    radius: float  # Radio inscrito máximo de la región


class EdgeDTO(BaseModel):
    """Representa una arista (conexión/puerta) entre dos nodos."""
    source: int
    target: int
    weight: float  # Distancia euclidiana entre centroides


class GraphSummaryDTO(BaseModel):
    """Resumen estadístico del grafo generado."""
    total_nodes: int
    total_edges: int
    rooms: int
    corridors: int
    open_spaces: int


class GraphDataDTO(BaseModel):
    """Datos completos del grafo."""
    nodes: List[NodeDTO]
    edges: List[EdgeDTO]
    summary: GraphSummaryDTO
    visualization_url: str


class GraphResponseDTO(BaseModel):
    """Respuesta completa del endpoint de análisis."""
    status: str
    message: str
    data: GraphDataDTO
