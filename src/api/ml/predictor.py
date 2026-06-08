import numpy as np
from ai_edge_litert.interpreter import Interpreter
from PIL import Image
import io
from pathlib import Path


class PlantDiseasePredictor:
    def __init__(self):
        print("Loading TFLite model...")

        BASE_DIR    = Path(__file__).resolve().parent.parent.parent.parent
        MODELS_DIR  = BASE_DIR / "models"
        MODEL_PATH  = MODELS_DIR / "model_unquant.tflite"
        LABELS_PATH = MODELS_DIR / "labels.txt"

        self.interpreter = Interpreter(model_path=str(MODEL_PATH))
        self.interpreter.allocate_tensors()

        self.input_details  = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()

        # ✅ حجم الصورة من الموديل نفسه (مش hardcoded)
        input_shape  = self.input_details[0]['shape']  # [1, H, W, 3]
        self.img_size = (input_shape[1], input_shape[2])

        # ✅ عدد الـ classes من الموديل نفسه
        output_shape   = self.output_details[0]['shape']  # [1, N]
        self.n_classes = output_shape[1]

        # ✅ قراءة labels.txt
        raw_lines = LABELS_PATH.read_text(encoding="utf-8").splitlines()
        # بعض الملفات فيها أرقام في البداية مثل "0 Tomato___healthy"
        self.labels = []
        for line in raw_lines:
            line = line.strip()
            if not line:
                continue
            # احذف الرقم لو موجود في البداية
            parts = line.split(None, 1)
            if len(parts) == 2 and parts[0].isdigit():
                self.labels.append(parts[1])
            else:
                self.labels.append(line)

        print(f"Model input size:  {self.img_size}")
        print(f"Model output size: {self.n_classes} classes")
        print(f"Labels loaded:     {len(self.labels)}")
        print(f"Labels: {self.labels}")

        # ✅ تحقق من التوافق
        if len(self.labels) != self.n_classes:
            print(f"⚠️  WARNING: labels ({len(self.labels)}) != model classes ({self.n_classes})")

        print("✅ Model ready!")

    def predict(self, image_bytes: bytes) -> dict:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img = img.resize(self.img_size)

        input_data = np.array(img, dtype=np.float32) / 255.0
        input_data = np.expand_dims(input_data, axis=0)

        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        output = self.interpreter.get_tensor(self.output_details[0]['index'])[0]

        idx        = int(np.argmax(output))
        confidence = float(np.max(output))

        # ✅ لو الـ index خارج النطاق — اعطِ اسم افتراضي
        if idx < len(self.labels):
            class_name = self.labels[idx]
        else:
            class_name = f"class_{idx}"

        return {
            "class_name": class_name,
            "confidence": confidence
        }


_predictor = None

def get_predictor():
    global _predictor
    if _predictor is None:
        _predictor = PlantDiseasePredictor()
    return _predictor
