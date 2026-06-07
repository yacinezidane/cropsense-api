"""
WebSocket real-time plant disease detection — OpenCV blur check only.

Architecture
────────────
  Flutter ──JPEG bytes──▶ /ws/predict ──blur check──▶ predictor ──▶ JSON result
                 ▲___________WebSocket (persistent)___________________|

NOTE: preprocessing is intentionally minimal — only blur rejection.
Crop / contrast were removed because the model was NOT trained with them,
and they caused confusion between similar classes (e.g. Early vs Late Blight).
The predictor.predict() handles resize + normalize internally, identical to
the HTTP /predict endpoint.

Install
───────
  pip install flask-sock opencv-python-headless
"""

import json
import logging

import cv2
import numpy as np
from flask_sock import Sock

from api.database import get_db
from api.ml.predictor import get_predictor

logger = logging.getLogger(__name__)

# ── tunables ──────────────────────────────────────────────────────────────────
# رفع القيمة → أكثر صرامة في رفض الصور الضبابية
# خفضها → يقبل صور أقل حدة (مفيد في إضاءة منخفضة)
_BLUR_THRESHOLD = 55.0

# Shared Sock instance – must be init_app()'d in create_app()
sock = Sock()


# ─── OpenCV preprocessing ─────────────────────────────────────────────────────

def _preprocess(raw_bytes: bytes) -> tuple[bytes | None, float]:
    """
    فحص الضبابية فقط بـ Laplacian — بدون crop أو تعديل ألوان.
    الصورة تُمرَّر للنموذج كما هي تماماً مثل HTTP /predict.

    Returns
    -------
    (jpeg_bytes, blur_score)
      jpeg_bytes = None  →  الصورة ضبابية أو تالفة، تجاهلها
    """
    arr   = np.frombuffer(raw_bytes, np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        return None, 0.0

    # ── فحص الضبابية على الـ grayscale ────────────────────────────────────
    gray       = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())

    if blur_score < _BLUR_THRESHOLD:
        return None, blur_score

    # ── أعد encode بجودة عالية بدون أي تعديل ─────────────────────────────
    ok, encoded = cv2.imencode(
        ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 92]
    )
    return (encoded.tobytes() if ok else None), blur_score


# ─── WebSocket handler ────────────────────────────────────────────────────────

@sock.route("/ws/predict")
def ws_predict(ws):
    """
    WebSocket endpoint — real-time plant disease prediction.

    Wire protocol (text / binary mixed)
    ────────────────────────────────────
    Client → Server  [text]   {"type":"config","language":"en"}
    Client → Server  [binary] <raw JPEG bytes>

    Server → Client  [text]   {"type":"result", "plant_name":…, "confidence":…, …}
    Server → Client  [text]   {"type":"blurry",  "score": 42.1}
    Server → Client  [text]   {"type":"unknown", "class_name":…, "confidence":…}
    Server → Client  [text]   {"type":"error",   "message":…}
    """
    predictor = get_predictor()
    db = get_db()
    language = "en"          # per-connection state

    logger.debug("WS /ws/predict — client connected")

    while True:
        try:
            data = ws.receive()
        except Exception:
            break
        if data is None:
            break

        # ── Config message (text) ──────────────────────────────────────────
        if isinstance(data, str):
            try:
                msg = json.loads(data)
                if msg.get("type") == "config":
                    language = msg.get("language", "en")
                    ws.send(json.dumps({"type": "config_ack", "language": language}))
            except Exception as exc:
                ws.send(json.dumps({"type": "error", "message": f"bad config: {exc}"}))
            continue

        # ── Binary frame ──────────────────────────────────────────────────
        try:
            processed, blur_score = _preprocess(bytes(data))

            if processed is None:
                ws.send(json.dumps({
                    "type":  "blurry",
                    "score": round(blur_score, 1),
                }))
                continue

            # ML inference
            prediction = predictor.predict(processed)
            class_name = prediction["class_name"]
            confidence = prediction["confidence"]

            # DB look-up
            model_class = db.model_classes.find_one({"class_name": class_name})
            if not model_class:
                ws.send(json.dumps({
                    "type":       "unknown",
                    "class_name": class_name,
                    "confidence": confidence,
                }))
                continue

            plant = db.plants.find_one({"_id": model_class["plant_id"]})
            if not plant:
                ws.send(json.dumps({"type": "error", "message": "plant not found"}))
                continue

            result: dict = {
                "type":             "result",
                "plant_name":       plant["names"].get(language, [plant["canonical_name"]])[0],
                "plant_id":         str(plant["_id"]),
                "is_healthy":       bool(model_class.get("is_healthy", False)),
                "confidence":       round(confidence, 4),
                "care_instructions": plant.get("care_instructions", {}).get(language),
            }

            if not model_class.get("is_healthy") and model_class.get("disease_id"):
                disease = db.diseases.find_one({"_id": model_class["disease_id"]})
                if disease:
                    result.update({
                        "disease_name": disease["names"].get(
                            language, [disease["canonical_name"]]
                        )[0],
                        "disease_id":  str(disease["_id"]),
                        "description": disease.get("description", {}).get(language),
                        "symptoms":    disease.get("symptoms",    {}).get(language, []),
                        "cure":        disease.get("cure",        {}).get(language),
                        "prevention":  disease.get("prevention",  {}).get(language),
                    })

            ws.send(json.dumps(result))

        except Exception as exc:
            logger.exception("ws_predict error")
            ws.send(json.dumps({"type": "error", "message": str(exc)}))

    logger.debug("WS /ws/predict — client disconnected")