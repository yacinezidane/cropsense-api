import numpy as np
from ai_edge_litert.interpreter import Interpreter  # ✅ بدل tflite_runtime
from PIL import Image
import io
from pathlib import Path
from api.config import IMG_SIZE
from api.config import DEFAULT_MODEL_PATH, DEFAULT_CLASSES_PATH

class PlantDiseasePredictor:
    def __init__(self):
        print("Loading TFLite model...")
        BASE_DIR = Path("/opt/render/project/src")
        

        print("MODEL PATH:", DEFAULT_MODEL_PATH)
        print("EXISTS:", DEFAULT_MODEL_PATH.exists())
        self.interpreter = Interpreter(
           model_path=str(DEFAULT_MODEL_PATH)
        )
        with open(DEFAULT_CLASSES_PATH, "r", encoding="utf-8") as f:
            self.labels = [line.strip() for line in f if line.strip()]
        print("MODEL SIZE:", MODEL_PATH.stat().st_size)

        # ✅ ai-edge-litert متوافق مع NumPy 2.x
        self.interpreter = Interpreter(model_path=str(MODEL_PATH))
        self.interpreter.allocate_tensors()

        self.input_details  = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        with open(LABELS_PATH, "r", encoding="utf-8") as f:
            self.labels = [line.strip() for line in f if line.strip()]

        print(f"Model loaded successfully - {len(self.labels)} classes")

    def predict(self, image_bytes):
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize(IMG_SIZE)

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
