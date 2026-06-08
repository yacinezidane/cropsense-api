"""Cloud-based model inference using Hugging Face API (NO TensorFlow)."""

import os
import requests
import numpy as np
import cv2
from typing import Dict

from api.config import IMG_SIZE


class ModelPredictor:
    """Handles prediction via Hugging Face API."""

    def __init__(self):
        self.api_url = "https://api-inference.huggingface.co/models/walid0726/plant-disease-ai"
        self.headers = {
            "Authorization": f"Bearer {os.getenv('HF_TOKEN')}"
        }

    def predict(self, image_bytes: bytes) -> Dict[str, any]:
        """
        Send image to Hugging Face and get prediction.

        Args:
            image_bytes: image file bytes

        Returns:
            dict: prediction result
        """

        response = requests.post(
            self.api_url,
            headers=self.headers,
            data=image_bytes
        )

        if response.status_code != 200:
            raise Exception(f"Hugging Face API error: {response.text}")

        result = response.json()

        # Expected format:
        # [{"label": "healthy", "score": 0.98}, ...]

        if not isinstance(result, list):
            raise Exception(f"Invalid response: {result}")

        top_prediction = max(result, key=lambda x: x["score"])

        return {
            "class_name": top_prediction["label"],
            "confidence": float(top_prediction["score"]),
            "all_probabilities": result
        }


# ─────────────────────────────────────────────
# Singleton instance
# ─────────────────────────────────────────────
_predictor = None


def get_predictor() -> ModelPredictor:
    """Return global predictor instance."""
    global _predictor

    if _predictor is None:
        _predictor = ModelPredictor()

    return _predictor
