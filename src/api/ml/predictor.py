"""Model loading and inference."""

import pickle
import numpy as np
import cv2
from typing import Tuple, Dict
from pathlib import Path

from api.config import DEFAULT_MODEL_PATH, DEFAULT_CLASSES_PATH, IMG_SIZE


class ModelPredictor:
    """Handles model loading and prediction."""

    def __init__(self, model_path: Path = None, classes_path: Path = None):
        """Initialize predictor with model and class labels."""
        self.model_path = model_path or DEFAULT_MODEL_PATH
        self.classes_path = classes_path or DEFAULT_CLASSES_PATH
        self.model = None
        self.class_names = None
        self._load_model()

    def _load_model(self):
        """Load trained model and class names."""
        # Lazy import to avoid loading TensorFlow until needed
        from tensorflow import keras

        if not self.model_path.exists():
            raise FileNotFoundError(f"Model not found: {self.model_path}")

        if not self.classes_path.exists():
            raise FileNotFoundError(f"Classes file not found: {self.classes_path}")

        self.model = keras.models.load_model(str(self.model_path))

        with open(self.classes_path, "rb") as f:
            self.class_names = pickle.load(f)

    def predict(self, image_bytes: bytes) -> Dict[str, any]:
        """
        Predict plant disease from image bytes.

        Args:
            image_bytes: Image file bytes

        Returns:
            dict with 'class_name', 'confidence', 'all_probabilities'
        """
        # Decode image from bytes
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("Failed to decode image")

        # Preprocess image (same as trainer)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_resized = cv2.resize(img_rgb, IMG_SIZE)
        img_normalized = img_resized.astype('float32') / 255.0
        img_batch = np.expand_dims(img_normalized, axis=0)

        # Predict
        predictions = self.model.predict(img_batch, verbose=0)
        predicted_idx = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_idx])
        predicted_class = self.class_names[predicted_idx]

        return {
            'class_name': predicted_class,
            'confidence': confidence,
            'all_probabilities': predictions[0].tolist()
        }


# Global predictor instance (singleton pattern)
_predictor: ModelPredictor = None


def get_predictor() -> ModelPredictor:
    """Get or create global predictor instance."""
    global _predictor
    if _predictor is None:
        _predictor = ModelPredictor()
    return _predictor
