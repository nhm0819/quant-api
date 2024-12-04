from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/v1")


@router.get("/", response_class=JSONResponse)
async def index():
    """Index Page of the API."""
    return {"status": "healthy"}
