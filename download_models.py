"""
Downloads ML model files from Hugging Face Hub during Render build.
"""

import os
import sys
from pathlib import Path
from huggingface_hub import hf_hub_download

# ─── Config ───────────────────────────────────────────────
MODELS_DIR = Path(os.getenv("MODELS_DIR", "models"))
HF_REPO_ID = os.getenv("HF_REPO_ID", "")
HF_TOKEN = os.getenv("HF_TOKEN", None)

MODEL_FILENAME = os.getenv("MODEL_FILENAME", "plant_disease_rtx3080_optimized.keras")
CLASSES_FILE = os.getenv("CLASSES_FILENAME", "label_classes.pkl")

if not HF_REPO_ID:
    print("ERROR: HF_REPO_ID not set")
    sys.exit(1)

MODELS_DIR.mkdir(parents=True, exist_ok=True)
print(f"Models directory: {MODELS_DIR.resolve()}")

# ─── Download ───────────────────────────────────────────────
try:
    files = [MODEL_FILENAME, CLASSES_FILE]

    for file in files:
        print(f"⬇ Downloading: {file}")

        hf_hub_download(
            repo_id=HF_REPO_ID,
            filename=f"models/{file}",   # 👈 مهم جدًا
            local_dir=str(MODELS_DIR),
            token=HF_TOKEN,
        )

        print(f"✔ Done: {file}")

    print("\n✅ All models ready!")

except Exception as e:
    print(f"\n❌ Download failed: {e}")
    sys.exit(1)
