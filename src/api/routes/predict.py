"""Prediction endpoints."""

from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from bson import ObjectId

from api.config import MAX_UPLOAD_SIZE
from api.database import get_db
from api.ml.predictor import get_predictor

predict_bp = Blueprint('predict', __name__)


@predict_bp.route('/predict', methods=['POST'])
def predict():
    """
    Predict plant disease from uploaded image
    ---
    tags:
      - Prediction
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: Image file of plant leaf (JPG, PNG)
      - name: language
        in: formData
        type: string
        required: false
        default: en
        description: Preferred language for response (en, ar, fr, etc.)
    responses:
      200:
        description: Successful prediction
        schema:
          type: object
          properties:
            plant_name:
              type: string
              example: Tomato
            plant_id:
              type: string
              example: 507f1f77bcf86cd799439011
            is_healthy:
              type: boolean
              example: false
            confidence:
              type: number
              format: float
              example: 0.95
            disease_name:
              type: string
              example: Early Blight
              nullable: true
            disease_id:
              type: string
              example: 507f1f77bcf86cd799439012
              nullable: true
            description:
              type: string
              example: Fungal disease affecting tomato leaves
              nullable: true
            symptoms:
              type: array
              items:
                type: string
              example: ["Dark spots on leaves", "Yellowing"]
              nullable: true
            cure:
              type: string
              example: Apply fungicide regularly
              nullable: true
            prevention:
              type: string
              example: Rotate crops, avoid overhead watering
              nullable: true
            care_instructions:
              type: string
              example: Water regularly, provide full sun
              nullable: true
      400:
        description: Bad request (no file, invalid format)
        schema:
          type: object
          properties:
            error:
              type: string
              example: No file provided
      404:
        description: Model class not found in database
        schema:
          type: object
          properties:
            error:
              type: string
            class_name:
              type: string
            confidence:
              type: number
      413:
        description: File too large (>10MB)
        schema:
          type: object
          properties:
            error:
              type: string
              example: File too large
      500:
        description: Internal server error
        schema:
          type: object
          properties:
            error:
              type: string
    """
    # Check if file is present
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    # Get language preference
    language = request.form.get('language', 'en')

    try:
        # Read image bytes
        image_bytes = file.read()

        if len(image_bytes) > MAX_UPLOAD_SIZE:
            return jsonify({'error': 'File too large'}), 413

        # Get prediction from model
        predictor = get_predictor()
        prediction = predictor.predict(image_bytes)

        # Get class name from prediction
        class_name = prediction['class_name']
        confidence = prediction['confidence']

        # Look up class in database
        db = get_db()
        model_class = db.model_classes.find_one({'class_name': class_name})

        if not model_class:
            return jsonify({
                'error': 'Model class not found in database',
                'class_name': class_name,
                'confidence': confidence
            }), 404

        # Get plant info
        plant = db.plants.find_one({'_id': model_class['plant_id']})
        if not plant:
            return jsonify({'error': 'Plant not found'}), 404

        # Build response
        response = {
            'plant_name': plant['names'].get(language, [plant['canonical_name']])[0],
            'plant_id': str(plant['_id']),
            'is_healthy': model_class.get('is_healthy', False),
            'confidence': confidence,
            'care_instructions': plant.get('care_instructions', {}).get(language)
        }

        # If not healthy, add disease info
        if not model_class.get('is_healthy') and model_class.get('disease_id'):
            disease = db.diseases.find_one({'_id': model_class['disease_id']})
            if disease:
                response.update({
                    'disease_name': disease['names'].get(language, [disease['canonical_name']])[0],
                    'disease_id': str(disease['_id']),
                    'description': disease.get('description', {}).get(language),
                    'symptoms': disease.get('symptoms', {}).get(language, []),
                    'cure': disease.get('cure', {}).get(language),
                    'prevention': disease.get('prevention', {}).get(language)
                })

        return jsonify(response), 200

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500
