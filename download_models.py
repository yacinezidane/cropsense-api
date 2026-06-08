import os
import sys
from pathlib import Path
from huggingface_hub import hf_hub_download

REPO_ID    = "walid0726/plant-disease-ai"
MODELS_DIR = Path(os.getenv("MODELS_DIR", "/opt/render/project/models"))
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# الملفات التي يحتاجها تطبيقك (نماذج TFLite والتصنيفات)
FILES = [
    "model_unquant.tflite",      # اسم الملف داخل مستودع Hugging Face
    "labels.txt",                 # ملف التصنيفات
]

print(f"Downloading from: {REPO_ID}")

for filename in FILES:
    dest = MODELS_DIR / filename

    if dest.exists():
        print(f"✓ Already exists: {filename}")
        continue

    print(f"⬇  Downloading: {filename} ...")
    hf_hub_download(
        repo_id=REPO_ID,
        filename=filename,
        local_dir=str(MODELS_DIR),
        local_dir_use_symlinks=False
    )
    print(f"✓ Done: {filename}  ({dest.stat().st_size / 1e6:.1f} MB)")

print("\n✅ Models ready!")
