# api/routes/auth_google.py
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from api.db.database import db
from api.auth.deps import get_current_user
from api.auth.jwt import issue_jwt
from api.auth.google_verify import verify_google_id_token

router = APIRouter(prefix="/auth/google", tags=["Auth - Google"])

class GoogleSignInRequest(BaseModel):
    id_token: str
    access_token: Optional[str] = None  # optional (not stored by default)

@router.post("/login", status_code=status.HTTP_200_OK)
async def google_sign_in(body: GoogleSignInRequest):
    payload = await verify_google_id_token(body.id_token)

    sub = payload.get("sub")       # google stable user id
    email = payload.get("email")
    email_verified = payload.get("email_verified", False)
    given_name = payload.get("given_name", "")
    family_name = payload.get("family_name", "")
    picture = payload.get("picture", "")

    if not email or not sub:
        raise HTTPException(status_code=400, detail="Google token missing email/sub")

    # Try find by google sub first, else by email
    user_doc = await db.users.find_one({"auth_providers.google.sub": sub}) or await db.users.find_one({"email": email})

    now = datetime.utcnow()
    new_user = False

    if not user_doc:
        # create as unsubscribed (your requirement)
        user_doc = {
            "email": email,
            "hashed_password": "",  # no local password
            "first_name": given_name or "",
            "last_name": family_name or "",
            "role": "unsubscribed",
            "trial_start_date": None,
            "auth_providers": {
                "google": {
                    "sub": sub,
                    "email_verified": bool(email_verified),
                    "picture": picture,
                    "last_login_at": now,
                }
            },
            "created_at": now,
            "updated_at": now,
        }
        await db.users.insert_one(user_doc)
        new_user = True
    else:
        updates = {
            "updated_at": now,
            "auth_providers.google.sub": sub,
            "auth_providers.google.email_verified": bool(email_verified),
            "auth_providers.google.picture": picture,
            "auth_providers.google.last_login_at": now,
        }
        await db.users.update_one({"_id": user_doc["_id"]}, {"$set": updates})
        user_doc = await db.users.find_one({"_id": user_doc["_id"]})

    token = issue_jwt(email=user_doc["email"], role=user_doc.get("role", "unsubscribed"))

    return {
        "access_token": token,
        "token_type": "bearer",
        "new_user": new_user,
        "role": user_doc.get("role", "unsubscribed"),
        "profile": {
            "email": user_doc["email"],
            "first_name": user_doc.get("first_name", ""),
            "last_name": user_doc.get("last_name", ""),
            "avatar": picture,
            "email_verified": email_verified,
        },
    }

@router.post("/link", status_code=status.HTTP_200_OK)
async def google_link_account(body: GoogleSignInRequest, user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    payload = await verify_google_id_token(body.id_token)
    sub = payload.get("sub")
    email = payload.get("email")
    email_verified = payload.get("email_verified", False)
    picture = payload.get("picture", "")

    if not sub or not email:
        raise HTTPException(status_code=400, detail="Google token missing email/sub")

    # ensure not linked to someone else
    already = await db.users.find_one({"auth_providers.google.sub": sub, "_id": {"$ne": user["_id"]}})
    if already:
        raise HTTPException(status_code=409, detail="This Google account is already linked to another user")

    updates = {
        "auth_providers.google.sub": sub,
        "auth_providers.google.email_verified": bool(email_verified),
        "auth_providers.google.picture": picture,
        "auth_providers.google.last_login_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    await db.users.update_one({"_id": user["_id"]}, {"$set": updates})
    return {"message": "Google account linked"}
