import sys
import os

# Add project root to sys.path so imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load .env file
from dotenv import load_dotenv
load_dotenv()

import asyncio
from datetime import datetime
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorClient
from api.models.user import Role
import jwt

# Create bcrypt hasher
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Connect to MongoDB using URI from .env
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URI)
db = client["discern"]

# Seeder logic
async def seed_users():
    users = [
        {
            "email": "admin@example.com",
            "first_name": "Admin",
            "last_name": "User",
            "role": Role.ADMIN,
            "hashed_password": pwd_context.hash("Myfirst1"),
        },
        {
            "email": "trial@example.com",
            "first_name": "Trial",
            "last_name": "User",
            "role": Role.TRIAL,
            "trial_start_date": datetime.utcnow(),
            "hashed_password": pwd_context.hash("Myfirst1"),
        },
        {
            "email": "subscriber@example.com",
            "first_name": "Subscribed",
            "last_name": "User",
            "role": Role.SUBSCRIBER,
            "hashed_password": pwd_context.hash("Myfirst1"),
        },
        {
            "email": "unsubscribed@example.com",
            "first_name": "Unsubscribed",
            "last_name": "User",
            "role": Role.UNSUBSCRIBED,
            "hashed_password": pwd_context.hash("Myfirst1"),
        }
    ]

    for user in users:
        existing = await db.users.find_one({"email": user["email"]})
        if not existing:
            await db.users.insert_one(user)
            print(f"✅ Seeded {user['role']} user: {user['email']}")
        else:
            print(f"ℹ️ User already exists: {user['email']}")

    # Optional: generate sample JWT for testing
    jwt_secret = os.getenv("JWT_SECRET")
    jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")

    if jwt_secret:
        token = jwt.encode({"email": "admin@example.com"}, jwt_secret, algorithm=jwt_algorithm)
        print("🔑 Sample admin JWT:", token)
    else:
        print("⚠️ JWT_SECRET not found in .env")

# Run the seeder
if __name__ == "__main__":
    asyncio.run(seed_users())
