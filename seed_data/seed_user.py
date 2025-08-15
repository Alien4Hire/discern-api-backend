# scripts/seed_users.py
import sys
import os
from datetime import datetime
import asyncio

# Ensure project root on path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient
from jose import jwt  # keep consistent with API

from api.models.user import (
    Role,
    UserPreferences,
    Denomination,
    BibleTranslation,
    ResponseLength,
    CitationStyle,
)

# ----- Config -----
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB_NAME", "discern")

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def default_preferences() -> dict:
    # Mirror your Pydantic defaults
    prefs = UserPreferences(
        denomination=Denomination.UNSET,
        translation=BibleTranslation.DEFAULT,
        response_length=ResponseLength.STANDARD,
        citation_style=CitationStyle.INLINE,
        include_direct_quotes=True,
        use_denomination_weighting=True,
        tone_hint=None,
        timezone=None,
        locale=None,
    )
    return prefs.model_dump()


async def ensure_indexes(db):
    # Helpful indexes for auth and Google linking
    await db.users.create_index("email", unique=True)
    await db.users.create_index("auth_providers.google.sub", unique=True, sparse=True)


async def seed_users(db):
    now = datetime.utcnow()
    base = {
        "created_at": now,
        "updated_at": now,
        "preferences": default_preferences(),
        "auth_providers": {},  # room to link Google later
        "trial_start_date": None,
    }

    users = [
        {
            **base,
            "email": "admin@example.com",
            "first_name": "Admin",
            "last_name": "User",
            "role": Role.ADMIN.value,  # store as string
            "hashed_password": pwd_context.hash("Myfirst1"),
        },
        {
            **base,
            "email": "trial@example.com",
            "first_name": "Trial",
            "last_name": "User",
            "role": Role.TRIAL.value,
            "trial_start_date": now,
            "hashed_password": pwd_context.hash("Myfirst1"),
        },
        {
            **base,
            "email": "subscriber@example.com",
            "first_name": "Subscribed",
            "last_name": "User",
            "role": Role.SUBSCRIBER.value,
            "hashed_password": pwd_context.hash("Myfirst1"),
        },
        {
            **base,
            "email": "unsubscribed@example.com",
            "first_name": "Unsubscribed",
            "last_name": "User",
            "role": Role.UNSUBSCRIBED.value,
            "hashed_password": pwd_context.hash("Myfirst1"),
        },
        # (Optional) Google-linked sample user (no local password)
        # {
        #     **base,
        #     "email": "google_user@example.com",
        #     "first_name": "Google",
        #     "last_name": "User",
        #     "role": Role.UNSUBSCRIBED.value,
        #     "hashed_password": "",  # no local password for Google-only accounts
        #     "auth_providers": {
        #         "google": {
        #             "sub": "google-sub-id-for-local-testing",
        #             "email_verified": True,
        #             "picture": "https://picsum.photos/100",
        #             "last_login_at": now,
        #         }
        #     },
        # },
    ]

    for user in users:
        existing = await db.users.find_one({"email": user["email"]})
        if existing:
            print(f"ℹ️ User already exists: {user['email']}")
            # keep updated_at fresh & ensure new fields exist
            await db.users.update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "updated_at": datetime.utcnow(),
                    "preferences": existing.get("preferences", default_preferences()),
                    "auth_providers": existing.get("auth_providers", {}),
                }}
            )
            continue

        await db.users.insert_one(user)
        print(f"✅ Seeded {user['role']} user: {user['email']}")

    if JWT_SECRET:
        admin = await db.users.find_one({"email": "admin@example.com"})
        if admin:
            token = jwt.encode(
                {"sub": admin["email"], "role": admin.get("role", Role.ADMIN.value)},
                JWT_SECRET,
                algorithm=JWT_ALGORITHM
            )
            print("🔑 Sample admin JWT:", token)
    else:
        print("⚠️ JWT_SECRET not set; skipping sample JWT")


async def main():
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    await ensure_indexes(db)
    await seed_users(db)
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
