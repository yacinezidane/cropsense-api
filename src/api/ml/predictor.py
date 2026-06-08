import numpy as np
import tflite_runtime.interpreter as tflite
from PIL import Image
import io
from pathlib import Path

from api.config import IMG_SIZE


class PlantDiseasePredictor:

    def __init__(self):
        print("Loading TFLite model...")

        # 📌 تحديد المسار الصحيح بشكل ديناميكي (مهم لـ Render)
        BASE_DIR = Path("/opt/render/project/src")

        MODEL_PATH = BASE_DIR / "models" / "model_unquant.tflite"
        LABELS_PATH = BASE_DIR / "models" / "labels.txt"

        # 🔍 Debug (اختياري لكن مهم)
        print("MODEL PATH:", MODEL_PATH)
        print("EXISTS:", MODEL_PATH.exists())

        # ❗ تحميل النموذج
        self.interpreter = tflite.Interpreter(
            model_path=str(MODEL_PATH)
        )
        self.interpreter.allocate_tensors()
       print("MODEL SIZE:", MODEL_PATH.stat().st_size)
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        # 📌 تحميل labels
        with open(LABELS_PATH, "r", encoding="utf-8") as f:
            self.labels = [line.strip() for line in f]

        print(f"Model loaded successfully - {len(self.labels)} classes")

    def predict(self, image_bytes):
        # 📌 قراءة الصورة
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize(IMG_SIZE)

        # 📌 preprocessing
        input_data = np.array(img, dtype=np.float32) / 255.0
        input_data = np.expand_dims(input_data, axis=0)

        # 📌 inference
        self.interpreter.set_tensor(
            self.input_details[0]['index'],
            input_data
        )

        self.interpreter.invoke()

        output = self.interpreter.get_tensor(
            self.output_details[0]['index']
        )[0]

        idx = int(np.argmax(output))

        return {
            "class_name": self.labels[idx],
            "confidence": float(np.max(output))
        }


# ─────────────────────────────
# Singleton (لا يتم تحميل النموذج كل مرة)
# ─────────────────────────────
_predictor = None

def get_predictor():
    global _predictor
    if _predictor is None:
        _predictor = PlantDiseasePredictor()
    return _predictor
