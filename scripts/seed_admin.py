#!/usr/bin/env python3
"""
Standalone seed script - no project imports needed.
Just run: python seed_admin.py
"""
from datetime import datetime
import bcrypt
from pymongo import MongoClient

# ── Config: عدّل هذه القيم إذا لزم ─────────────────────────────
MONGO_URI  = "mongodb://localhost:27017/"
DB_NAME    = "plant_disease_db"

ADMIN_NAME     = "Admin"
ADMIN_EMAIL    = "admin@plantdisease.com"
ADMIN_PASSWORD = "admin123"
# ────────────────────────────────────────────────────────────────

def seed_admin():
    client = MongoClient(MONGO_URI)
    db     = client[DB_NAME]

    if db.users.find_one({"email": ADMIN_EMAIL}):
        print(f"⚠️  Admin '{ADMIN_EMAIL}' already exists. Skipping.")
        client.close()
        return

    hashed = bcrypt.hashpw(ADMIN_PASSWORD.encode(), bcrypt.gensalt())
    now    = datetime.utcnow()

    db.users.insert_one({
        "name":       ADMIN_NAME,
        "email":      ADMIN_EMAIL,
        "password":   hashed,
        "role":       "admin",
        "is_active":  True,
        "created_at": now,
        "updated_at": now,
    })

    client.close()
    print("✅  Admin created successfully!")
    print(f"    Email:    {ADMIN_EMAIL}")
    print(f"    Password: {ADMIN_PASSWORD}")
    print("    ⚠️  Change the password after first login!")

if __name__ == "__main__":
    seed_admin()