# api/routes/auth_dev.py
# Creates a dev-only endpoint to login or create a user by email

from fastapi import APIRouter, HTTPException, status
# Imports os to read environment variables
import os
# Imports typing for optional fields
from typing import Optional
# Imports datetime for timestamps
from datetime import datetime
# Imports pydantic for request body validation
from pydantic import BaseModel, EmailStr

# Imports your database handle
from api.db.database import db
# Imports your JWT helper
from api.auth.jwt import issue_jwt

# Reads environment to gate the route
APP_ENV = os.getenv("APP_ENV", "development")

# Creates the router
router = APIRouter(prefix="/auth/dev", tags=["Auth - Dev"])

# Defines the request body
class DevLoginRequest(BaseModel):
    # Uses a required email to find/create user
    email: EmailStr
    # Allows optional name fields for local testing
    first_name: Optional[str] = None
    # Allows optional name fields for local testing
    last_name: Optional[str] = None
    # Allows override but defaults to unsubscribed for safety
    role: Optional[str] = "unsubscribed"

# Guards the route so it only works in dev
def ensure_dev():
    # Raises 404 to avoid advertising the route in non-dev environments
    if APP_ENV != "development":
        raise HTTPException(status_code=404, detail="Not found")

# Implements POST /auth/dev/login
@router.post("/login", status_code=status.HTTP_200_OK)
async def dev_login(body: DevLoginRequest):
    # Ensures the route is only available in dev
    ensure_dev()

    # Normalizes email
    email = body.email.lower().strip()
    # Sets timestamps
    now = datetime.utcnow()

    # Tries to find user by email
    user_doc = await db.users.find_one({"email": email})

    # Creates if missing
    if not user_doc:
        # Builds the new user document
        user_doc = {
            "email": email,
            "hashed_password": "",  # no password for dev login
            "first_name": (body.first_name or "").strip(),
            "last_name": (body.last_name or "").strip(),
            "role": (body.role or "unsubscribed"),
            "trial_start_date": None,
            "auth_providers": {},   # no google link for dev login
            "created_at": now,
            "updated_at": now,
        }
        # Inserts the user
        await db.users.insert_one(user_doc)
    else:
        # Updates basic fields for convenience
        updates = {
            "first_name": (body.first_name or user_doc.get("first_name", "")),
            "last_name": (body.last_name or user_doc.get("last_name", "")),
            "role": (body.role or user_doc.get("role", "unsubscribed")),
            "updated_at": now,
        }
        # Applies the update
        await db.users.update_one({"_id": user_doc["_id"]}, {"$set": updates})
        # Re-fetches the user
        user_doc = await db.users.find_one({"_id": user_doc["_id"]})

    # Issues a normal JWT
    token = issue_jwt(email=user_doc["email"], role=user_doc.get("role", "unsubscribed"))

    # Returns same shape as your google sign-in
    return {
        "access_token": token,
        "token_type": "bearer",
        "new_user": False,
        "role": user_doc.get("role", "unsubscribed"),
        "profile": {
            "email": user_doc["email"],
            "first_name": user_doc.get("first_name", ""),
            "last_name": user_doc.get("last_name", ""),
            "avatar": "",
            "email_verified": False,
        },
    }
