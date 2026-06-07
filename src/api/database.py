"""MongoDB database connection and initialization."""

from pymongo import MongoClient, ASCENDING
from pymongo.database import Database
from api.config import MONGO_URI, MONGO_DB_NAME

_client: MongoClient = None
_db: Database = None


def get_db() -> Database:
    """Get MongoDB database instance."""
    global _client, _db

    if _db is None:
        _client = MongoClient(MONGO_URI)
        _db = _client[MONGO_DB_NAME]

        # ── Existing indexes ──────────────────────────────────
        _db.plants.create_index("canonical_name")
        _db.diseases.create_index("model_class")
        _db.diseases.create_index("plant_id")
        _db.model_classes.create_index("class_name", unique=True)

        # ── Users indexes (NEW) ───────────────────────────────
        _db.users.create_index(
            [("email", ASCENDING)],
            unique=True,
            name="idx_users_email_unique"
        )
        _db.users.create_index(
            [("role", ASCENDING)],
            name="idx_users_role"
        )

    return _db


def close_db():
    """Close MongoDB connection."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None