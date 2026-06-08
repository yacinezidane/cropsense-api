"""
predictor.py — يحمّل الموديل محلياً ويشغّله على Render
بدون استدعاء أي API خارجي
"""
import pickle
import numpy as np
from pathlib import Path
from PIL import Image
import io
import tensorflow as tf

from api.config import DEFAULT_MODEL_PATH, DEFAULT_CLASSES_PATH, IMG_SIZE


class PlantDiseasePredictor:

    def __init__(self):
        print(f"Loading model from: {DEFAULT_MODEL_PATH}")
        # ✅ يحمّل الموديل من الملف المحلي (اللي نزّله download_models.py)
        self.model = tf.keras.models.load_model(str(DEFAULT_MODEL_PATH))

        print(f"Loading classes from: {DEFAULT_CLASSES_PATH}")
        with open(DEFAULT_CLASSES_PATH, "rb") as f:
            self.classes = pickle.load(f)

        print(f"✅ Model ready — {len(self.classes)} classes")

    def predict(self, image_bytes: bytes) -> dict:
        # معالجة الصورة
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize(IMG_SIZE)
        arr = np.array(img, dtype=np.float32) / 255.0
        arr = np.expand_dims(arr, axis=0)  # (1, H, W, 3)

        # تشغيل الموديل محلياً
        predictions = self.model.predict(arr, verbose=0)[0]

        class_idx  = int(np.argmax(predictions))
        confidence = float(np.max(predictions))
        class_name = self.classes[class_idx]

        return {
            "class_name": class_name,
            "confidence": confidence,
            "class_index": class_idx,
        }


# Singleton — يُحمَّل مرة واحدة عند أول طلب
_predictor = None

def get_predictor() -> PlantDiseasePredictor:
    global _predictor
    if _predictor is None:
        _predictor = PlantDiseasePredictor()
    return _predictor
