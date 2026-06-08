import numpy as np
from ai_edge_litert.interpreter import Interpreter
from PIL import Image
import io
from pathlib import Path
from api.config import IMG_SIZE, DEFAULT_MODEL_PATH, DEFAULT_CLASSES_PATH

class PlantDiseasePredictor:
    def __init__(self):
        print("Loading TFLite model...")
        
        # التحقق من وجود الملفات
        if not DEFAULT_MODEL_PATH.exists():
            raise FileNotFoundError(f"Model not found at {DEFAULT_MODEL_PATH}")
        if not DEFAULT_CLASSES_PATH.exists():
            raise FileNotFoundError(f"Labels not found at {DEFAULT_CLASSES_PATH}")
        
        # تحميل النموذج
        self.interpreter = Interpreter(model_path=str(DEFAULT_MODEL_PATH))
        self.interpreter.allocate_tensors()
        
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        # تحميل التصنيفات من ملف txt
        with open(DEFAULT_CLASSES_PATH, "r", encoding="utf-8") as f:
            self.labels = [line.strip() for line in f if line.strip()]
        
        print(f"Model loaded successfully - {len(self.labels)} classes")
        print(f"Model size: {DEFAULT_MODEL_PATH.stat().st_size / (1024*1024):.2f} MB")

    def predict(self, image_bytes):
    try:
        print("1️⃣ Received image bytes, length:", len(image_bytes))
        
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        print("2️⃣ Image opened, size:", img.size)
        
        img = img.resize(IMG_SIZE)
        print("3️⃣ Image resized to:", img.size)
        
        input_data = np.array(img, dtype=np.float32) / 255.0
        input_data = np.expand_dims(input_data, axis=0)
        print("4️⃣ Input data shape:", input_data.shape)
        
        print("5️⃣ Setting input tensor...")
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        
        print("6️⃣ Invoking interpreter...")
        self.interpreter.invoke()
        
        print("7️⃣ Getting output tensor...")
        output = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
        print("8️⃣ Output shape:", output.shape)
        
        idx = int(np.argmax(output))
        confidence = float(np.max(output))
        print(f"9️⃣ Prediction: idx={idx}, confidence={confidence}")
        
        return {
            "class_name": self.labels[idx],
            "confidence": confidence
        }
    except Exception as e:
        import traceback
        print("❌ Prediction failed:")
        traceback.print_exc()
        raise  # إعادة رفع الاستثناء ليظهر كـ 500

# Singleton
_predictor = None

def get_predictor():
    global _predictor
    if _predictor is None:
        _predictor = PlantDiseasePredictor()
    return _predictor
