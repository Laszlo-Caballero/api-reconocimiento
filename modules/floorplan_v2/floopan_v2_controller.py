from fastapi import APIRouter, UploadFile, status
from modules.floorplan_v2.floorpan_v2_service import FloorpanV2Service

router = APIRouter(
    prefix="/api/v2/floorplan",
    tags=["floorplan_v2"]
)

service = FloorpanV2Service()


@router.post("/analyze", status_code=status.HTTP_200_OK)
def analyze_floorplan(file: UploadFile):
    return service.analyze_floorplan(file)
