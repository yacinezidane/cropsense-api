"""Disease management endpoints."""

from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime

from api.database import get_db
from api.models import Disease, UserContributedName

diseases_bp = Blueprint('diseases', __name__)


@diseases_bp.route('/diseases', methods=['GET'])
def get_diseases():
    """Get all diseases
    ---
    tags:
      - Diseases
    responses:
      200:
        description: List of all diseases
        schema:
          type: array
          items:
            type: object
            properties:
              _id:
                type: string
              canonical_name:
                type: string
              model_class:
                type: string
                description: Model output class name
              plant_id:
                type: string
              names:
                type: object
              user_contributed_names:
                type: array
              description:
                type: object
              symptoms:
                type: object
              cure:
                type: object
              prevention:
                type: object
    """
    db = get_db()
    diseases = list(db.diseases.find())

    # Convert ObjectId to string
    for disease in diseases:
        disease['_id'] = str(disease['_id'])
        disease['plant_id'] = str(disease['plant_id'])
        if disease.get('disease_id'):
            disease['disease_id'] = str(disease['disease_id'])

    return jsonify(diseases), 200


@diseases_bp.route('/diseases/<disease_id>', methods=['GET'])
def get_disease(disease_id):
    """Get disease by ID with optional language
    ---
    tags:
      - Diseases
    parameters:
      - name: disease_id
        in: path
        type: string
        required: true
        description: Disease ID
      - name: language
        in: query
        type: string
        required: false
        description: Language code (en, ar, fr, etc.)
        default: en
    responses:
      200:
        description: Disease details
        schema:
          type: object
          properties:
            _id:
              type: string
            canonical_name:
              type: string
            model_class:
              type: string
              description: Model output class name (e.g., "Tomato_Early_blight")
            plant_id:
              type: string
            names:
              type: object
              description: Multi-language names
            user_contributed_names:
              type: array
              items:
                type: object
                properties:
                  name:
                    type: string
                  language:
                    type: string
                  votes:
                    type: integer
                  added_by:
                    type: string
                  created_at:
                    type: string
                    format: date-time
            description:
              type: object
              description: Multi-language descriptions
            symptoms:
              type: object
              description: Multi-language symptoms list
            cure:
              type: object
              description: Multi-language cure instructions
            prevention:
              type: object
              description: Multi-language prevention tips
      404:
        description: Disease not found
      400:
        description: Invalid disease ID
    """
    try:
        language = request.args.get('language', 'en')

        db = get_db()
        disease = db.diseases.find_one({'_id': ObjectId(disease_id)})

        if not disease:
            return jsonify({'error': 'Disease not found'}), 404

        disease['_id'] = str(disease['_id'])
        disease['plant_id'] = str(disease['plant_id'])

        return jsonify(disease), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@diseases_bp.route('/diseases', methods=['POST'])
def create_disease():
    """Create new disease
    ---
    tags:
      - Diseases
    consumes:
      - application/json
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - canonical_name
            - model_class
            - plant_id
          properties:
            canonical_name:
              type: string
              example: "Early Blight"
            model_class:
              type: string
              example: "Tomato_Early_blight"
              description: Must match model output class
            plant_id:
              type: string
              example: "507f1f77bcf86cd799439011"
              description: MongoDB ObjectId of the plant
            names:
              type: object
              description: Multi-language names
              example: {"en": ["Early Blight"], "ar": ["Early_Blight_in_Arabic"]}
            description:
              type: object
              description: Multi-language descriptions
              example: {"en": "Fungal disease affecting tomatoes"}
            symptoms:
              type: object
              description: Multi-language symptoms list
              example: {"en": ["Dark spots on leaves", "Yellowing"]}
            cure:
              type: object
              description: Multi-language cure instructions
              example: {"en": "Apply copper fungicide"}
            prevention:
              type: object
              description: Multi-language prevention tips
              example: {"en": "Rotate crops annually"}
    responses:
      201:
        description: Disease created successfully
        schema:
          type: object
          properties:
            id:
              type: string
      400:
        description: Invalid request data
    """
    try:
        data = request.json
        disease = Disease(**data)

        db = get_db()
        result = db.diseases.insert_one(disease.model_dump(by_alias=True, exclude=['id']))

        return jsonify({'id': str(result.inserted_id)}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@diseases_bp.route('/diseases/<disease_id>', methods=['PUT'])
def update_disease(disease_id):
    """Update disease
    ---
    tags:
      - Diseases
    consumes:
      - application/json
    parameters:
      - name: disease_id
        in: path
        type: string
        required: true
        description: Disease ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            canonical_name:
              type: string
            model_class:
              type: string
            plant_id:
              type: string
            names:
              type: object
            description:
              type: object
            symptoms:
              type: object
            cure:
              type: object
            prevention:
              type: object
    responses:
      200:
        description: Disease updated successfully
        schema:
          type: object
          properties:
            message:
              type: string
      404:
        description: Disease not found
      400:
        description: Invalid request data
    """
    try:
        data = request.json
        data['updated_at'] = datetime.utcnow()

        # Convert plant_id string to ObjectId if present
        if 'plant_id' in data and isinstance(data['plant_id'], str):
            data['plant_id'] = ObjectId(data['plant_id'])

        db = get_db()
        result = db.diseases.update_one(
            {'_id': ObjectId(disease_id)},
            {'$set': data}
        )

        if result.matched_count == 0:
            return jsonify({'error': 'Disease not found'}), 404

        return jsonify({'message': 'Disease updated'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@diseases_bp.route('/diseases/<disease_id>', methods=['DELETE'])
def delete_disease(disease_id):
    """Delete disease
    ---
    tags:
      - Diseases
    parameters:
      - name: disease_id
        in: path
        type: string
        required: true
        description: Disease ID
    responses:
      200:
        description: Disease deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
      404:
        description: Disease not found
      400:
        description: Invalid disease ID
    """
    try:
        db = get_db()
        result = db.diseases.delete_one({'_id': ObjectId(disease_id)})

        if result.deleted_count == 0:
            return jsonify({'error': 'Disease not found'}), 404

        return jsonify({'message': 'Disease deleted'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@diseases_bp.route('/diseases/<disease_id>/names', methods=['POST'])
def add_disease_name(disease_id):
    """Add user-contributed disease name
    ---
    tags:
      - Diseases
    consumes:
      - application/json
    parameters:
      - name: disease_id
        in: path
        type: string
        required: true
        description: Disease ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - name
          properties:
            name:
              type: string
              example: "Leaf Blight"
              description: User-contributed name for the disease
            language:
              type: string
              example: "en"
              description: Language code (en, ar, fr, etc.)
            added_by:
              type: string
              example: "user_123"
              description: User ID who added the name
    responses:
      200:
        description: Name added successfully
        schema:
          type: object
          properties:
            message:
              type: string
      404:
        description: Disease not found
      400:
        description: Invalid request data
    """
    try:
        data = request.json
        contributed_name = UserContributedName(
            name=data['name'],
            language=data.get('language', 'en'),
            added_by=data.get('added_by')
        )

        db = get_db()
        result = db.diseases.update_one(
            {'_id': ObjectId(disease_id)},
            {
                '$push': {'user_contributed_names': contributed_name.model_dump()},
                '$set': {'updated_at': datetime.utcnow()}
            }
        )

        if result.matched_count == 0:
            return jsonify({'error': 'Disease not found'}), 404

        return jsonify({'message': 'Name added successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@diseases_bp.route('/diseases/<disease_id>/names/<name_index>/vote', methods=['POST'])
def vote_disease_name(disease_id, name_index):
    """Vote on user-contributed disease name
    ---
    tags:
      - Diseases
    consumes:
      - application/json
    parameters:
      - name: disease_id
        in: path
        type: string
        required: true
        description: Disease ID
      - name: name_index
        in: path
        type: integer
        required: true
        description: Index of the contributed name in the array
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - vote
          properties:
            vote:
              type: integer
              example: 1
              description: Vote value (1 for upvote, -1 for downvote)
              enum: [1, -1]
    responses:
      200:
        description: Vote recorded successfully
        schema:
          type: object
          properties:
            message:
              type: string
      404:
        description: Disease not found
      400:
        description: Invalid vote value or disease ID
    """
    try:
        vote = request.json.get('vote', 1)
        if vote not in [-1, 1]:
            return jsonify({'error': 'Invalid vote value'}), 400

        db = get_db()
        result = db.diseases.update_one(
            {'_id': ObjectId(disease_id)},
            {'$inc': {f'user_contributed_names.{name_index}.votes': vote}}
        )

        if result.matched_count == 0:
            return jsonify({'error': 'Disease not found'}), 404

        return jsonify({'message': 'Vote recorded'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@diseases_bp.route('/diseases/by-class/<class_name>', methods=['GET'])
def get_disease_by_class(class_name):
    """Get disease by model class name
    ---
    tags:
      - Diseases
    parameters:
      - name: class_name
        in: path
        type: string
        required: true
        description: Model output class name (e.g., "Tomato_Early_blight")
      - name: language
        in: query
        type: string
        required: false
        description: Language code (en, ar, fr, etc.)
        default: en
    responses:
      200:
        description: Disease details for the given model class
        schema:
          type: object
          properties:
            _id:
              type: string
            canonical_name:
              type: string
            model_class:
              type: string
            plant_id:
              type: string
            names:
              type: object
            user_contributed_names:
              type: array
              items:
                type: object
                properties:
                  name:
                    type: string
                  language:
                    type: string
                  votes:
                    type: integer
                  added_by:
                    type: string
                  created_at:
                    type: string
                    format: date-time
            description:
              type: object
            symptoms:
              type: object
            cure:
              type: object
            prevention:
              type: object
      404:
        description: Disease not found for the given class name
      400:
        description: Invalid request
    """
    try:
        language = request.args.get('language', 'en')

        db = get_db()
        disease = db.diseases.find_one({'model_class': class_name})

        if not disease:
            return jsonify({'error': 'Disease not found'}), 404

        disease['_id'] = str(disease['_id'])
        disease['plant_id'] = str(disease['plant_id'])

        return jsonify(disease), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400
