"""
api/ml/predictor.py
تحميل نموذج TFLite والتنبؤ بمرض النبات من الصورة
"""
import numpy as np
from ai_edge_litert.interpreter import Interpreter
from PIL import Image
import io
from pathlib import Path
from api.config import IMG_SIZE, DEFAULT_MODEL_PATH, DEFAULT_CLASSES_PATH

class PlantDiseasePredictor:
    def __init__(self):
        print("🔍 جاري تحميل نموذج TFLite...")
        
        # التحقق من وجود ملف النموذج
        if not DEFAULT_MODEL_PATH.exists():
            raise FileNotFoundError(f"❌ ملف النموذج غير موجود: {DEFAULT_MODEL_PATH}")
        # التحقق من وجود ملف التصنيفات
        if not DEFAULT_CLASSES_PATH.exists():
            raise FileNotFoundError(f"❌ ملف التصنيفات غير موجود: {DEFAULT_CLASSES_PATH}")
        
        # تحميل النموذج باستخدام ai_edge_litert (بديل tflite_runtime)
        self.interpreter = Interpreter(model_path=str(DEFAULT_MODEL_PATH))
        self.interpreter.allocate_tensors()
        
        # تفاصيل المدخلات والمخرجات
        self.input_details = self.interpreter.get_input_details()
        self.output_details = self.interpreter.get_output_details()
        
        # قراءة التصنيفات من ملف labels.txt (كل سطر يمثل فئة)
        with open(DEFAULT_CLASSES_PATH, "r", encoding="utf-8") as f:
            self.labels = [line.strip() for line in f if line.strip()]
        
        # إظهار معلومات الحجم المتوقع للصورة (للتأكد)
        expected_shape = self.input_details[0]['shape']  # مثلاً (1, 224, 224, 3)
        print(f"✅ تم تحميل النموذج بنجاح")
        print(f"📌 حجم المدخلات المتوقع: {expected_shape}")
        print(f"📌 عدد التصنيفات: {len(self.labels)}")
        print(f"📌 حجم ملف النموذج: {DEFAULT_MODEL_PATH.stat().st_size / (1024*1024):.2f} MB")

    def predict(self, image_bytes):
        """
        تستقبل الصورة على شكل bytes، وتعيد التنبؤ
        :param image_bytes: محتوى الصورة الخام (bytes)
        :return: dict: {"class_name": str, "confidence": float}
        """
        try:
            # 1. فتح الصورة وتحويلها إلى RGB
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
            
            # 2. تغيير الحجم إلى المقاس الذي يتوقعه النموذج (مأخوذ من config)
            img = img.resize(IMG_SIZE)
            
            # 3. تحويل الصورة إلى مصفوفة numpy وتطبيعها (0-1)
            input_data = np.array(img, dtype=np.float32) / 255.0
            
            # 4. إضافة بُعد الدفعة (batch dimension) -> (1, H, W, C)
            input_data = np.expand_dims(input_data, axis=0)
            
            # 5. تعيين بيانات الإدخال في النموذج
            self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
            
            # 6. تشغيل التنبؤ
            self.interpreter.invoke()
            
            # 7. استخراج النتيجة (المخرجات)
            output = self.interpreter.get_tensor(self.output_details[0]['index'])[0]
            
            # 8. تحديد الفئة الأكثر احتمالاً
            idx = int(np.argmax(output))
            confidence = float(np.max(output))
            
            return {
                "class_name": self.labels[idx],
                "confidence": confidence
            }
        except Exception as e:
            # في حال حدوث خطأ، نعيد رفعه مع تفاصيل للتسجيل
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"فشل التنبؤ: {str(e)}") from e

# نمط Singleton (نسخة واحدة فقط من النموذج)
_predictor = None

def get_predictor():
    """
    دالة تحميل النموذج (مرة واحدة فقط)
    """
    global _predictor
    if _predictor is None:
        _predictor = PlantDiseasePredictor()
    return _predictor
