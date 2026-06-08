"""
predictor.py — TFLite version (Render safe)
بدون TensorFlow
"""

import numpy as np
from PIL import Image
import io
import tflite_runtime.interpreter as tflite
import pickle

from api.config import DEFAULT_MODEL_PATH, DEFAULT_CLASSES_PATH, IMG_SIZE


class PlantDiseasePredictor:

    def __init__(self):
        print(f"Loading TFLite model: {DEFAULT_MODEL_PATH}")

        # ✔ تحميل TFLite بدل TensorFlow
        self.interpreter = tflite.Interpreter(
            model_path=str(DEFAULT_MODEL_PATH)
        )
        self.interpreter.allocate_tensors()

        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        print(f"Loading classes: {DEFAULT_CLASSES_PATH}")
        with open(DEFAULT_CLASSES_PATH, "rb") as f:
            self.classes = pickle.load(f)

        print(f"✅ Model ready — {len(self.classes)} classes")

    def predict(self, image_bytes: bytes) -> dict:

        # 🖼️ preprocessing
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize(IMG_SIZE)

        arr = np.array(img, dtype=np.float32) / 255.0
        arr = np.expand_dims(arr, axis=0)

        # ✔ inference
        self.interpreter.set_tensor(
            self.input_details[0]["index"],
            arr
        )

        self.interpreter.invoke()

        predictions = self.interpreter.get_tensor(
            self.output_details[0]["index"]
        )[0]

        class_idx = int(np.argmax(predictions))
        confidence = float(np.max(predictions))
        class_name = self.classes[class_idx]

        return {
            "class_name": class_name,
            "confidence": confidence,
            "class_index": class_idx,
        }


# Singleton
_predictor = None

def get_predictor() -> PlantDiseasePredictor:
    global _predictor
    if _predictor is None:
        _predictor = PlantDiseasePredictor()
    return _predictor
