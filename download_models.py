"""
download_models.py
------------------
Downloads ML model files from Hugging Face Hub during Render build.
Run this ONCE during build: python download_models.py
"""

import os
import sys
from pathlib import Path

# ─── Config ───────────────────────────────────────────────────────────────────
MODELS_DIR     = Path(os.getenv("MODELS_DIR", "models"))
HF_REPO_ID     = os.getenv("HF_REPO_ID", "")          # e.g. "YacineBou/cropsense-models"
HF_TOKEN       = os.getenv("HF_TOKEN", None)           # needed if repo is private
MODEL_FILENAME = os.getenv("MODEL_FILENAME", "plant_disease_rtx3080_optimized.keras")
CLASSES_FILE   = os.getenv("CLASSES_FILENAME", "label_classes.pkl")

# ─── Validate ─────────────────────────────────────────────────────────────────
if not HF_REPO_ID:
    print("ERROR: HF_REPO_ID environment variable is not set.")
    print("Set it to your Hugging Face repo, e.g.: YourUsername/cropsense-models")
    sys.exit(1)

# ─── Create models directory ──────────────────────────────────────────────────
MODELS_DIR.mkdir(parents=True, exist_ok=True)
print(f"Models directory: {MODELS_DIR.resolve()}")

# ─── Download ─────────────────────────────────────────────────────────────────
try:
    from huggingface_hub import hf_hub_download

    for filename in [MODEL_FILENAME, CLASSES_FILE]:
        dest = MODELS_DIR / Path(filename).name
        if dest.exists():
            print(f"✓ Already exists: {filename}  ({dest.stat().st_size / 1e6:.1f} MB)")
            continue

        print(f"⬇  Downloading: {filename} ...")
        hf_hub_download(
            repo_id=HF_REPO_ID,
            filename=filename,
            local_dir=str(MODELS_DIR),
            token=HF_TOKEN,
        )
        size_mb = (MODELS_DIR / Path(filename).name).stat().st_size / 1e6
        print(f"✓ Downloaded: {filename}  ({size_mb:.1f} MB)")

    print("\n✅ All models ready!")

except Exception as e:
    print(f"\n❌ Download failed: {e}")
    sys.exit(1)
