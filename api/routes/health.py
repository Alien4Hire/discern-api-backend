from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("/", tags=["Status"])
async def health():
    return {"status": "ok"}
