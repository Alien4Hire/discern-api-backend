# api/routes/scripture.py
from fastapi import APIRouter, Depends, HTTPException, Query
from api.auth.deps import get_current_user
import os, requests

router = APIRouter(prefix="/scripture", tags=["Scripture"])
ES = os.getenv("ELASTIC_HOST", "http://elasticsearch:9200").rstrip("/")
INDEX = os.getenv("ELASTIC_INDEX", "bible_verses")

@router.get("/search")
async def search(
    q: str = Query(..., min_length=1),
    translation: str | None = None,
    size: int = 20,
    user=Depends(get_current_user)
):
    # prefer user’s default if not provided
    t = translation or user.get("preferences", {}).get("translation") or "DEFAULT"
    query = {
        "bool": {
            "must": [{"multi_match": {"query": q, "fields": ["text^2","reference","book"]}}],
            "filter": [{"term": {"translation": t}}] if t not in ("DEFAULT", None) else []
        }
    }
    r = requests.post(f"{ES}/{INDEX}/_search", json={"query": query, "size": size})
    if not r.ok:
        raise HTTPException(status_code=502, detail=r.text[:300])
    hits = r.json().get("hits", {}).get("hits", [])
    return [h["_source"] for h in hits]
