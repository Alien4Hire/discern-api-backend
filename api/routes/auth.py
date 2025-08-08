# api/routes/auth.py

# import libs
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import jwt
from dotenv import load_dotenv
import os

# import db and auth helpers
from api.db.database import db
from api.auth.auth import hash_password, verify_password
from api.models.user import UserCreate, Role
from api.auth.deps import get_current_user

# load environment variables
load_dotenv()

# read jwt config
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

# validate secret is present
if not JWT_SECRET:
    # raise early if missing so we don't silently fail token ops
    raise RuntimeError("JWT_SECRET is not set. Check your .env or container environment.")

# create router
router = APIRouter(prefix="/auth", tags=["Auth"])

# create-account endpoint
@router.post("/create-account", status_code=status.HTTP_201_CREATED)
async def create_account(user: UserCreate):
    # check if user exists
    existing = await db.users.find_one({"email": user.email})
    if existing:
        # duplicate email
        raise HTTPException(status_code=400, detail="User already exists")

    # hash password
    hashed = hash_password(user.password)

    # build user document
    user_doc = {
        "email": user.email,
        "hashed_password": hashed,
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "role": user.role.value if isinstance(user.role, Role) else str(user.role or Role.UNSUBSCRIBED.value),
        "trial_start_date": user.trial_start_date or datetime.utcnow(),
        # optional app-facing flags you may want later
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    # insert user
    await db.users.insert_one(user_doc)

    # return simple confirmation
    return {"message": "Account created"}

# sign-in endpoint using OAuth2PasswordRequestForm so Swagger can auto-authorize
@router.post("/sign-in")
async def sign_in(form_data: OAuth2PasswordRequestForm = Depends()):
    # map oauth2 "username" to our email
    email = form_data.username

    # fetch user
    db_user = await db.users.find_one({"email": email})
    if not db_user or not verify_password(form_data.password, db_user["hashed_password"]):
        # invalid credentials
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # build token claims
    claims = {
        "sub": db_user["email"],
        "role": db_user.get("role", Role.TRIAL.value),
        "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    }

    # sign token
    token = jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # return token with bearer type so Swagger knows to use it
    return {"access_token": token, "token_type": "bearer"}

# get-user-data endpoint
@router.get("/get-user-data")
async def get_user_data(user=Depends(get_current_user)):
    """
    Returns the logged-in user's details (without sensitive fields)
    """
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # remove sensitive data
    safe_user = {
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
    return safe_user
