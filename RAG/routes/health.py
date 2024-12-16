from fastapi import APIRouter

router = APIRouter()


@router.get("/health-check", status_code=200)
async def health_check():
    return {"success": True}
