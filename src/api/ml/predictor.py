import numpy as np
from ai_edge_litert.interpreter import Interpreter
from PIL import Image
import io
import sys
import traceback
from pathlib import Path
from api.config import IMG_SIZE, DEFAULT_MODEL_PATH, DEFAULT_CLASSES_PATH

class PlantDiseasePredictor:
    def __init__(self):
        print("🔍 جاري تحميل نموذج TFLite...")
        try:
            # التحقق من وجود الملفات
            if not DEFAULT_MODEL_PATH.exists():
                raise FileNotFoundError(f"❌ ملف النموذج غير موجود: {DEFAULT_MODEL_PATH}")
            if not DEFAULT_CLASSES_PATH.exists():
                raise FileNotFoundError(f"❌ ملف التصنيفات غير موجود: {DEFAULT_CLASSES_PATH}")

            # تحميل النموذج
            self.interpreter = Interpreter(model_path=str(DEFAULT_MODEL_PATH))
            self.interpreter.allocate_tensors()

            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()

            # قراءة التصنيفات
            with open(DEFAULT_CLASSES_PATH, "r", encoding="utf-8") as f:
                self.labels = [line.strip() for line in f if line.strip()]

            expected_shape = self.input_details[0]['shape']
            print(f"✅ تم تحميل النموذج بنجاح")
            print(f"📌 حجم المدخلات المتوقع: {expected_shape}")
            print(f"📌 عدد التصنيفات: {len(self.labels)}")
        except Exception as e:
            print("❌ فشل تحميل النموذج:")
            traceback.print_exc()
            raise  # إعادة رفع الاستثناء ليمنع تشغيل الخادم

    def predict(self, image_bytes):
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            img = img.resize(IMG_SIZE)
            input_data = np.array(img, dtype=np.float32) / 255.0
            input_data = np.expand_dims(input_data, axis=0)

            self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
            self.interpreter.invoke()
            output = self.interpreter.get_tensor(self.output_details[0]['index'])[0]

            idx = int(np.argmax(output))
            confidence = float(np.max(output))
            return {
                "class_name": self.labels[idx],
                "confidence": confidence
            }
        except Exception as e:
            print("❌ فشل أثناء التنبؤ:")
            traceback.print_exc()
            raise

_predictor = None
def get_predictor():
    global _predictor
    if _predictor is None:
        _predictor = PlantDiseasePredictor()
    return _predictor
