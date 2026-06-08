import numpy as np
from ai_edge_litert.interpreter import Interpreter
from PIL import Image
import io
from pathlib import Path


class PlantDiseasePredictor:
    def __init__(self):
        print("Loading TFLite model...")

        # ✅ مسار ديناميكي — يشتغل على Render وعلى جهازك
        # predictor.py موجود في: src/api/ml/predictor.py
        # المشروع root:          /opt/render/project/src/
        # models موجودة في:      /opt/render/project/src/models/
        BASE_DIR    = Path(__file__).resolve().parent.parent.parent.parent
        MODELS_DIR  = BASE_DIR / "models"
        MODEL_PATH  = MODELS_DIR / "model_unquant.tflite"
        LABELS_PATH = MODELS_DIR / "labels.txt"

        print("BASE_DIR:",    BASE_DIR)
        print("MODEL_PATH:",  MODEL_PATH)
        print("LABELS_PATH:", LABELS_PATH)
        print("Model exists:", MODEL_PATH.exists())
        print("Labels exist:", LABELS_PATH.exists())

        self.interpreter = Interpreter(model_path=str(MODEL_PATH))
        self.interpreter.allocate_tensors()

        self.input_details  = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        with open(LABELS_PATH, "r", encoding="utf-8") as f:
            self.labels = [line.strip() for line in f if line.strip()]

        print(f"✅ Model loaded — {len(self.labels)} classes")

    def predict(self, image_bytes: bytes) -> dict:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize((224, 224))  # غيّر الحجم حسب موديلك

        input_data = np.array(img, dtype=np.float32) / 255.0
        input_data = np.expand_dims(input_data, axis=0)

        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        output = self.interpreter.get_tensor(self.output_details[0]['index'])[0]

        idx = int(np.argmax(output))
        return {
            "class_name": self.labels[idx],
            "confidence": float(np.max(output))
        }


# Singleton
_predictor = None

def get_predictor():
    global _predictor
    if _predictor is None:
        _predictor = PlantDiseasePredictor()
    return _predictor
