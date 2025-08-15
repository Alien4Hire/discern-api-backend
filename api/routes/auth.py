# api/routes/auth.py

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime
from dotenv import load_dotenv
import os

from api.db.database import db
from api.auth.auth import hash_password, verify_password
from api.models.user import UserCreate, Role
from api.auth.deps import get_current_user
from api.auth.jwt import issue_jwt

load_dotenv()

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/create-account", status_code=status.HTTP_201_CREATED)
async def create_account(user: UserCreate):
    existing = await db.users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed = hash_password(user.password)

    user_doc = {
        "email": user.email,
        "hashed_password": hashed,
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "role": (user.role.value if isinstance(user.role, Role) else Role.UNSUBSCRIBED.value),
        "trial_start_date": user.trial_start_date or None,
        "auth_providers": {},  # keep room for linking google later
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    await db.users.insert_one(user_doc)
    return {"message": "Account created"}

@router.post("/login")
async def sign_in(form_data: OAuth2PasswordRequestForm = Depends()):
    email = form_data.username
    db_user = await db.users.find_one({"email": email})
    if not db_user or not verify_password(form_data.password, db_user.get("hashed_password", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = issue_jwt(email=db_user["email"], role=db_user.get("role", Role.UNSUBSCRIBED.value))
    return {"access_token": token, "token_type": "bearer"}

@router.get("/get-user-data")
async def get_user_data(user=Depends(get_current_user)):
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": str(user.get("_id")) if user.get("_id") else None,
        "email": user.get("email"),
        "first_name": user.get("first_name", ""),
        "last_name": user.get("last_name", ""),
        "role": user.get("role"),
        "trial_start_date": user.get("trial_start_date"),
        "is_subscribed": user.get("role") in ("admin", "subscriber"),
        "created_at": user.get("created_at"),
        "updated_at": user.get("updated_at"),
    }
