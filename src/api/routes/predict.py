import numpy as np
import tflite_runtime.interpreter as tflite
from PIL import Image
import io

from api.config import IMG_SIZE

class PlantDiseasePredictor:

    def __init__(self):
        print("Loading TFLite model...")

        self.interpreter = tflite.Interpreter(
            model_path="api/models/model_unquant.tflite"
        )
        self.interpreter.allocate_tensors()

        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        with open("api/models/labels.txt") as f:
            self.labels = [line.strip() for line in f]

        print("Model loaded successfully")

    def predict(self, image_bytes):
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize(IMG_SIZE)

        input_data = np.array(img, dtype=np.float32) / 255.0
        input_data = np.expand_dims(input_data, axis=0)

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


_predictor = None

def get_predictor():
    global _predictor
    if _predictor is None:
        _predictor = PlantDiseasePredictor()
    return _predictor
