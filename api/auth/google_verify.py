# api/auth/google_verify.py
import os
import anyio
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from fastapi import HTTPException

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
if not GOOGLE_CLIENT_ID:
    raise RuntimeError("GOOGLE_CLIENT_ID is not set")

def _verify_token_blocking(id_token_str: str) -> dict:
    req = google_requests.Request()
    # Raises ValueError if invalid
    return google_id_token.verify_oauth2_token(id_token_str, req, GOOGLE_CLIENT_ID)

async def verify_google_id_token(id_token_str: str) -> dict:
    try:
        return await anyio.to_thread.run_sync(_verify_token_blocking, id_token_str)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google ID token: {e}")
