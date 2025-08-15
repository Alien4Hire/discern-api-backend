# api/auth/deps.py

# put comments on the line above per your style rule

# imports
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError
from dotenv import load_dotenv
import os
import logging
from api.db.database import get_database

# load .env
load_dotenv()

# logger
logger = logging.getLogger("auth")
logger.setLevel(logging.INFO)

# must match your real sign-in path
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# read env
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

# fail fast if secret missing
if not JWT_SECRET:
    logger.error("JWT_SECRET missing in environment")
    raise RuntimeError("JWT_SECRET not set")

# shared 401
def _cred_exc(msg: str = "Could not validate credentials"):
    # log and return consistent 401
    logger.warning(f"auth failure: {msg}")
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

# dependency used by routes
async def get_current_user(token: str = Depends(oauth2_scheme)):
    # indicate we got a header
    logger.info("get_current_user: Authorization header received")

    try:
        # decode token
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        email = payload.get("sub")
        role = payload.get("role")
        logger.info(f"get_current_user: decoded sub={email}, role={role}")

        # validate sub
        if not email:
            raise _cred_exc("missing sub claim")

    except ExpiredSignatureError:
        # token expired
        raise HTTPException(status_code=401, detail="Token expired")
    except JWTError as e:
        # invalid token
        raise _cred_exc(f"JWT error: {e}")

    # fetch user
    db = await get_database()
    user = await db.users.find_one({"email": email})

    # handle missing user
    if not user:
        raise _cred_exc(f"no DB user for email={email}")

    # return doc for downstream access (role, _id, etc.)
    return user
