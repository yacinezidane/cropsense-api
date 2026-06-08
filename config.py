"""API Configuration."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Workspace root directory (3 levels up from api/src/api/)
WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# ─── ML Model Configuration ───────────────────────────────────────────────────
# MODELS_DIR can be overridden via environment variable (required for Render)
# On Render, set: MODELS_DIR=/opt/render/project/src/models
if os.getenv("MODELS_DIR"):
    MODELS_DIR = Path(os.getenv("MODELS_DIR"))
else:
    MODELS_DIR = WORKSPACE_ROOT / "models"

    EFAULT_MODEL_PATH = MODELS_DIR / "model_unquant.tflite"
    DEFAULT_CLASSES_PATH = MODELS_DIR / "labels.txt"
# MongoDB Configuration
MONGO_URI    = os.getenv("MONGO_URI",    "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "plant_disease_db")

# Image Processing
IMG_SIZE        = (256, 256)          # Match trainer config
MAX_UPLOAD_SIZE = 10 * 1024 * 1024   # 10 MB

# API Configuration
API_PREFIX = "/api"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
HOST  = os.getenv("HOST", "0.0.0.0")
PORT  = int(os.getenv("PORT", 5000))

# JWT Configuration
JWT_SECRET       = os.getenv("JWT_SECRET",       "change-this-secret-in-production")
JWT_ALGORITHM    = "HS256"
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", 24))
