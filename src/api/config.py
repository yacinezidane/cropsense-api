"""API Configuration."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Workspace root directory (3 levels up from api/src/api/)
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "plant_disease_db")

# ML Model Configuration
MODELS_DIR = WORKSPACE_ROOT / "models"
DEFAULT_MODEL_PATH = MODELS_DIR / os.getenv("MODEL_FILENAME", "plant_disease_model.keras")
DEFAULT_CLASSES_PATH = MODELS_DIR / os.getenv("CLASSES_FILENAME", "label_classes.pkl")

# Image Processing
IMG_SIZE = (256, 256)  # Match trainer config
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

# API Configuration
API_PREFIX = "/api"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 5000))

# ─── JWT Configuration (NEW) ────────────────────────────────────
JWT_SECRET       = os.getenv("JWT_SECRET", "change-this-secret-in-production")
JWT_ALGORITHM    = "HS256"
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", 24))  # Token valid for 24h

