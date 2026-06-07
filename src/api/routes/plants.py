"""Plant management endpoints."""

from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime

from api.database import get_db
from api.models import Plant, UserContributedName

plants_bp = Blueprint('plants', __name__)


@plants_bp.route('/plants', methods=['GET'])
def get_plants():
    """Get all plants
    ---
    tags:
      - Plants
    responses:
      200:
        description: List of all plants
        schema:
          type: array
          items:
            type: object
            properties:
              _id:
                type: string
              canonical_name:
                type: string
              scientific_name:
                type: string
              names:
                type: object
              user_contributed_names:
                type: array
              care_instructions:
                type: object
              description:
                type: object
    """
    db = get_db()
    plants = list(db.plants.find())

    # Convert ObjectId to string
    for plant in plants:
        plant['_id'] = str(plant['_id'])

    return jsonify(plants), 200


@plants_bp.route('/plants/<plant_id>', methods=['GET'])
def get_plant(plant_id):
    """Get plant by ID
    ---
    tags:
      - Plants
    parameters:
      - name: plant_id
        in: path
        type: string
        required: true
        description: Plant ID
    responses:
      200:
        description: Plant details
        schema:
          type: object
          properties:
            _id:
              type: string
            canonical_name:
              type: string
            scientific_name:
              type: string
            names:
              type: object
              description: Multi-language names
              example: {"en": ["Tomato"], "ar": ["Tomato_in_Arabic"]}
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
            care_instructions:
              type: object
              description: Multi-language care instructions
            description:
              type: object
              description: Multi-language descriptions
      404:
        description: Plant not found
      400:
        description: Invalid plant ID
    """
    try:
        db = get_db()
        plant = db.plants.find_one({'_id': ObjectId(plant_id)})

        if not plant:
            return jsonify({'error': 'Plant not found'}), 404

        plant['_id'] = str(plant['_id'])
        return jsonify(plant), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@plants_bp.route('/plants', methods=['POST'])
def create_plant():
    """Create new plant
    ---
    tags:
      - Plants
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
          properties:
            canonical_name:
              type: string
              example: "Tomato"
            scientific_name:
              type: string
              example: "Solanum lycopersicum"
            names:
              type: object
              description: Multi-language names
              example: {"en": ["Tomato"], "ar": ["Tomato_in_Arabic"], "fr": ["Tomate"]}
            care_instructions:
              type: object
              description: Multi-language care instructions
              example: {"en": "Water regularly", "ar": "Water_regularly_in_Arabic"}
            description:
              type: object
              description: Multi-language descriptions
              example: {"en": "Common garden vegetable"}
    responses:
      201:
        description: Plant created successfully
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
        plant = Plant(**data)

        db = get_db()
        result = db.plants.insert_one(plant.model_dump(by_alias=True, exclude=['id']))

        return jsonify({'id': str(result.inserted_id)}), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@plants_bp.route('/plants/<plant_id>', methods=['PUT'])
def update_plant(plant_id):
    """Update plant
    ---
    tags:
      - Plants
    consumes:
      - application/json
    parameters:
      - name: plant_id
        in: path
        type: string
        required: true
        description: Plant ID
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            canonical_name:
              type: string
            scientific_name:
              type: string
            names:
              type: object
            care_instructions:
              type: object
            description:
              type: object
    responses:
      200:
        description: Plant updated successfully
        schema:
          type: object
          properties:
            message:
              type: string
      404:
        description: Plant not found
      400:
        description: Invalid request data
    """
    try:
        data = request.json
        data['updated_at'] = datetime.utcnow()

        db = get_db()
        result = db.plants.update_one(
            {'_id': ObjectId(plant_id)},
            {'$set': data}
        )

        if result.matched_count == 0:
            return jsonify({'error': 'Plant not found'}), 404

        return jsonify({'message': 'Plant updated'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@plants_bp.route('/plants/<plant_id>', methods=['DELETE'])
def delete_plant(plant_id):
    """Delete plant
    ---
    tags:
      - Plants
    parameters:
      - name: plant_id
        in: path
        type: string
        required: true
        description: Plant ID
    responses:
      200:
        description: Plant deleted successfully
        schema:
          type: object
          properties:
            message:
              type: string
      404:
        description: Plant not found
      400:
        description: Invalid plant ID
    """
    try:
        db = get_db()
        result = db.plants.delete_one({'_id': ObjectId(plant_id)})

        if result.deleted_count == 0:
            return jsonify({'error': 'Plant not found'}), 404

        return jsonify({'message': 'Plant deleted'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@plants_bp.route('/plants/<plant_id>/names', methods=['POST'])
def add_plant_name(plant_id):
    """Add user-contributed plant name
    ---
    tags:
      - Plants
    consumes:
      - application/json
    parameters:
      - name: plant_id
        in: path
        type: string
        required: true
        description: Plant ID
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
              example: "Love Apple"
              description: User-contributed name for the plant
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
        description: Plant not found
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
        result = db.plants.update_one(
            {'_id': ObjectId(plant_id)},
            {
                '$push': {'user_contributed_names': contributed_name.model_dump()},
                '$set': {'updated_at': datetime.utcnow()}
            }
        )

        if result.matched_count == 0:
            return jsonify({'error': 'Plant not found'}), 404

        return jsonify({'message': 'Name added successfully'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400


@plants_bp.route('/plants/<plant_id>/names/<name_index>/vote', methods=['POST'])
def vote_plant_name(plant_id, name_index):
    """Vote on user-contributed plant name
    ---
    tags:
      - Plants
    consumes:
      - application/json
    parameters:
      - name: plant_id
        in: path
        type: string
        required: true
        description: Plant ID
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
        description: Plant not found
      400:
        description: Invalid vote value or plant ID
    """
    try:
        vote = request.json.get('vote', 1)
        if vote not in [-1, 1]:
            return jsonify({'error': 'Invalid vote value'}), 400

        db = get_db()
        result = db.plants.update_one(
            {'_id': ObjectId(plant_id)},
            {'$inc': {f'user_contributed_names.{name_index}.votes': vote}}
        )

        if result.matched_count == 0:
            return jsonify({'error': 'Plant not found'}), 404

        return jsonify({'message': 'Vote recorded'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400
