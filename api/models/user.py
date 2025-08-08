# api/models/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from enum import Enum
from datetime import datetime


# --- Enums ---

class Role(str, Enum):
    ADMIN = "admin"
    TRIAL = "trial"
    SUBSCRIBER = "subscriber"
    UNSUBSCRIBED = "unsubscribed"


class Denomination(str, Enum):
    NON_DENOMINATIONAL = "non_denominational"
    BAPTIST = "baptist"
    PENTECOSTAL = "pentecostal"
    METHODIST = "methodist"
    PRESBYTERIAN = "presbyterian"
    ANGLICAN = "anglican"
    LUTHERAN = "lutheran"
    CHURCH_OF_CHRIST = "church_of_christ"
    CATHOLIC = "catholic"
    ORTHODOX = "orthodox"
    EVANGELICAL = "evangelical"
    OTHER = "other"
    UNSET = "unset"


class BibleTranslation(str, Enum):
    KJV = "KJV"
    NKJV = "NKJV"
    ESV = "ESV"
    NIV = "NIV"
    NLT = "NLT"
    NASB = "NASB"
    CSB = "CSB"
    WEB = "WEB"   # World English Bible
    BBE = "BBE"   # Basic Bible English
    DEFAULT = "DEFAULT"  # let the system pick (fallback)


class CitationStyle(str, Enum):
    INLINE = "inline"        # e.g., (John 3:16)
    FOOTNOTE = "footnote"    # numbered notes at end
    NONE = "none"            # refs in prose only


class ResponseLength(str, Enum):
    SHORT = "short"
    STANDARD = "standard"
    LONG = "long"


# --- Nested models ---

class UserPreferences(BaseModel):
    denomination: Denomination = Denomination.UNSET
    translation: BibleTranslation = BibleTranslation.DEFAULT
    # If you want to nudge style without hard constraints:
    response_length: ResponseLength = ResponseLength.STANDARD
    citation_style: CitationStyle = CitationStyle.INLINE
    include_direct_quotes: bool = True
    # If you plan to weight passages/notes by denomination
    use_denomination_weighting: bool = True
    # Formatting/tone nudges
    tone_hint: Optional[Literal["gentle", "bold", "pastoral", "teaching"]] = None
    # For date/time things later (reminders, reading plans)
    timezone: Optional[str] = None
    locale: Optional[str] = None


# --- API models ---

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Role = Role.TRIAL
    trial_start_date: Optional[datetime] = None
    preferences: UserPreferences = Field(default_factory=UserPreferences)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserInDB(UserCreate):
    hashed_password: str


# What you return to clients (no secrets)
class UserPublic(BaseModel):
    id: Optional[str] = None  # str(ObjectId) when you serialize from Mongo
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Role
    trial_start_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    preferences: UserPreferences = Field(default_factory=UserPreferences)
