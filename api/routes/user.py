# api/routes/user.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field
from bson import ObjectId

from api.db.database import db
from api.auth.deps import get_current_user
from api.auth.auth import hash_password, verify_password
from api.models.user import Role

router = APIRouter(prefix="/users", tags=["Users"])

# ----------------- Schemas -----------------

class PreferencesPut(BaseModel):
    denomination: Optional[str] = Field(
        default=None, description="User's denomination (free text or enum later)"
    )
    translation: Optional[str] = Field(
        default=None, description="Preferred Bible translation key (e.g., KJV, ESV)"
    )
    response_length: Optional[str] = Field(
        default="standard", description='One of: "short", "standard", "long"'
    )
    citation_style: Optional[str] = Field(
        default="inline", description='One of: "inline", "footnote"'
    )
    include_direct_quotes: Optional[bool] = True
    use_denomination_weighting: Optional[bool] = True
    tone_hint: Optional[str] = Field(
        default=None, description='Optional tone hint, e.g. "gentle", "bold", "pastoral", "teaching"'
    )
    timezone: Optional[str] = None
    locale: Optional[str] = None

class PreferencesPatch(BaseModel):
    denomination: Optional[str] = None
    translation: Optional[str] = None
    response_length: Optional[str] = None
    citation_style: Optional[str] = None
    include_direct_quotes: Optional[bool] = None
    use_denomination_weighting: Optional[bool] = None
    tone_hint: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None

class UserPatch(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    preferences: Optional[PreferencesPatch] = None

class AdminUserPatch(UserPatch):
    role: Optional[Role] = None
    trial_start_date: Optional[datetime] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class UserPublic(BaseModel):
    id: Optional[str] = None
    email: Optional[str] = None
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    role: Optional[str] = None
    trial_start_date: Optional[datetime] = None
    is_subscribed: Optional[bool] = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    preferences: Optional[Dict[str, Any]] = None

# ----------------- Helpers -----------------

def _oid(id_str: str) -> ObjectId:
    if not ObjectId.is_valid(id_str):
        raise HTTPException(status_code=400, detail="Invalid user id")
    return ObjectId(id_str)

def _to_public(user: Dict[str, Any]) -> UserPublic:
    if not user:
        return UserPublic()
    prefs = user.get("preferences") or {}
    return UserPublic(
        id=str(user.get("_id")) if user.get("_id") else None,
        email=user.get("email"),
        first_name=user.get("first_name") or "",
        last_name=user.get("last_name") or "",
        role=user.get("role"),
        trial_start_date=user.get("trial_start_date"),
        is_subscribed=(user.get("role") in (Role.ADMIN.value, Role.SUBSCRIBER.value)),
        created_at=user.get("created_at"),
        updated_at=user.get("updated_at"),
        preferences={
            "denomination": prefs.get("denomination"),
            "translation": prefs.get("translation"),
            "response_length": prefs.get("response_length", "standard"),
            "citation_style": prefs.get("citation_style", "inline"),
            "include_direct_quotes": prefs.get("include_direct_quotes", True),
            "use_denomination_weighting": prefs.get("use_denomination_weighting", True),
            "tone_hint": prefs.get("tone_hint"),
            "timezone": prefs.get("timezone"),
            "locale": prefs.get("locale"),
        },
    )

def _require_admin(current_user: Dict[str, Any]) -> None:
    if current_user.get("role") != Role.ADMIN.value:
        raise HTTPException(status_code=403, detail="Admin privileges required")

# ----------------- Me (self) endpoints -----------------

@router.get("/me", response_model=UserPublic)
async def me(current_user=Depends(get_current_user)):
    return _to_public(current_user)

@router.patch("/me", response_model=UserPublic)
async def update_me(payload: UserPatch, current_user=Depends(get_current_user)):
    updates: Dict[str, Any] = {}

    if payload.first_name is not None:
        updates["first_name"] = payload.first_name
    if payload.last_name is not None:
        updates["last_name"] = payload.last_name

    if payload.preferences is not None:
        pref_updates = {k: v for k, v in payload.preferences.model_dump(exclude_none=True).items()}
        updates["preferences"] = {**(current_user.get("preferences") or {}), **pref_updates}

    if not updates:
        return _to_public(current_user)

    updates["updated_at"] = datetime.utcnow()
    await db.users.update_one({"_id": current_user["_id"]}, {"$set": updates})
    refreshed = await db.users.find_one({"_id": current_user["_id"]})
    return _to_public(refreshed)

@router.put("/me/preferences", response_model=UserPublic)
async def replace_my_preferences(prefs: PreferencesPut, current_user=Depends(get_current_user)):
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"preferences": prefs.model_dump(), "updated_at": datetime.utcnow()}},
    )
    refreshed = await db.users.find_one({"_id": current_user["_id"]})
    return _to_public(refreshed)

@router.patch("/me/preferences", response_model=UserPublic)
async def patch_my_preferences(prefs: PreferencesPatch, current_user=Depends(get_current_user)):
    pref_updates = {k: v for k, v in prefs.model_dump(exclude_none=True).items()}
    if pref_updates:
        await db.users.update_one(
            {"_id": current_user["_id"]},
            {
                "$set": {
                    **{f"preferences.{k}": v for k, v in pref_updates.items()},
                    "updated_at": datetime.utcnow(),
                }
            },
        )
    refreshed = await db.users.find_one({"_id": current_user["_id"]})
    return _to_public(refreshed)

@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(body: PasswordChange, current_user=Depends(get_current_user)):
    if not verify_password(body.current_password, current_user["hashed_password"]):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    new_hash = hash_password(body.new_password)
    await db.users.update_one(
        {"_id": current_user["_id"]},
        {"$set": {"hashed_password": new_hash, "updated_at": datetime.utcnow()}},
    )
    return

# ----------------- Admin endpoints -----------------

@router.get("/", response_model=List[UserPublic])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    q: Optional[str] = Query(None, description="Email contains (case-insensitive)"),
    current_user=Depends(get_current_user),
):
    _require_admin(current_user)
    flt: Dict[str, Any] = {}
    if q:
        flt["email"] = {"$regex": q, "$options": "i"}

    cursor = db.users.find(flt).skip(skip).limit(limit).sort("created_at", 1)
    users = await cursor.to_list(length=limit)
    return [_to_public(u) for u in users]

@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: str, current_user=Depends(get_current_user)):
    if current_user.get("role") != Role.ADMIN.value and str(current_user["_id"]) != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    user = await db.users.find_one({"_id": _oid(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _to_public(user)

@router.patch("/{user_id}", response_model=UserPublic)
async def admin_update_user(user_id: str, payload: AdminUserPatch, current_user=Depends(get_current_user)):
    _require_admin(current_user)
    updates: Dict[str, Any] = {}

    if payload.first_name is not None:
        updates["first_name"] = payload.first_name
    if payload.last_name is not None:
        updates["last_name"] = payload.last_name
    if payload.role is not None:
        updates["role"] = payload.role.value
    if payload.trial_start_date is not None:
        updates["trial_start_date"] = payload.trial_start_date
    if payload.preferences is not None:
        pref_updates = {k: v for k, v in payload.preferences.model_dump(exclude_none=True).items()}
        # Merge with current preferences
        current = await db.users.find_one({"_id": _oid(user_id)}, projection={"preferences": 1})
        merged = {**(current.get("preferences") or {}), **pref_updates} if current else pref_updates
        updates["preferences"] = merged

    if not updates:
        user = await db.users.find_one({"_id": _oid(user_id)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return _to_public(user)

    updates["updated_at"] = datetime.utcnow()
    result = await db.users.update_one({"_id": _oid(user_id)}, {"$set": updates})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    user = await db.users.find_one({"_id": _oid(user_id)})
    return _to_public(user)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str, current_user=Depends(get_current_user)):
    _require_admin(current_user)
    res = await db.users.delete_one({"_id": _oid(user_id)})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return
