"""API Configuration (Cloud version)."""

import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "plant_disease_db")

# Hugging Face Model (IMPORTANT)
HF_REPO_ID = os.getenv("HF_REPO_ID")
HF_TOKEN = os.getenv("HF_TOKEN")

# Image Processing
IMG_SIZE = (256, 256)
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB

# API Configuration
API_PREFIX = "/api"
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
HOST = "0.0.0.0"
PORT = int(os.getenv("PORT", 5000))

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET", "change-this-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = int(os.getenv("JWT_EXPIRY_HOURS", 24))
