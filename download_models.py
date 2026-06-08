"""
download_models.py — يحمّل الموديل من HF Hub محلياً
"""
import os
import sys
from pathlib import Path
from huggingface_hub import hf_hub_download

REPO_ID    = "walid0726/plant-disease-ai"
MODELS_DIR = Path(os.getenv("MODELS_DIR", "models"))
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# الملفات داخل مجلد models/ في الـ repo
FILES = [
    "models/plant_disease_rtx3080_optimized.keras",
    "models/label_classes.pkl",
]

print(f"Downloading from: {REPO_ID}")

for hf_path in FILES:
    filename = Path(hf_path).name
    dest = MODELS_DIR / filename

    if dest.exists():
        print(f"✓ Already exists: {filename}")
        continue

    print(f"⬇  Downloading: {filename} ...")
    # local_dir = parent of MODELS_DIR  →  يحفظ في MODELS_DIR/filename
    hf_hub_download(
        repo_id=REPO_ID,
        filename=hf_path,
        local_dir=str(MODELS_DIR.parent),
    )
    print(f"✓ Done: {filename}  ({dest.stat().st_size / 1e6:.1f} MB)")

print("\n✅ Models ready!")
