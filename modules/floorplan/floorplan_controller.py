from fastapi import APIRouter, UploadFile, status, Query
from modules.floorplan.floorplan_service import FloorplanService

router = APIRouter(
    prefix="/api/floorplan",
    tags=["floorplan"]
)


service = FloorplanService()


@router.post("/analyze", status_code=status.HTTP_200_OK)
def analyze_floorplan(
    file: UploadFile,
    open_space_threshold: int = Query(
        default=30,
        ge=5,
        le=200,
        description="Radio mínimo (px) para considerar un área como espacio abierto"
    ),
    min_node_distance: int = Query(
        default=20,
        ge=5,
        le=100,
        description="Distancia mínima (px) entre nodos para evitar duplicados"
    ),
    door_close_kernel: int = Query(
        default=0,
        ge=0,
        le=100,
        description="Tamaño del kernel para cerrar puertas en píxeles (0 para automático)"
    )
):
    """
    Analiza una imagen de plano de planta y genera un grafo de navegación.

    - **file**: Imagen del plano de planta (PNG, JPG, etc.)
    - **open_space_threshold**: Radio mínimo para detectar espacios abiertos (default: 30px)
    - **min_node_distance**: Distancia mínima entre nodos (default: 20px)
    - **door_close_kernel**: Tamaño del kernel en px para cerrar puertas (0 = automático)

    Retorna un grafo con nodos (intersecciones, extremos, espacios abiertos) y
    aristas (conexiones transitables), junto con una URL de visualización.
    """
    return service.analyze_floorplan(
        file=file,
        open_space_threshold=open_space_threshold,
        min_node_distance=min_node_distance,
        door_close_kernel=door_close_kernel
    )
