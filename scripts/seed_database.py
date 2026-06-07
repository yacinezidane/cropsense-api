#!/usr/bin/env python3
"""
Database seeding script for Plant Disease Detection API.

This script loads plant and disease data from seed_data.json and
populates the MongoDB database with the initial data.

Usage:
    python seed_database.py [--drop]

Options:
    --drop    Drop existing collections before seeding
"""

import json
import sys
from datetime import datetime
from pathlib import Path

from pymongo import MongoClient
from bson import ObjectId

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.config import MONGO_URI, MONGO_DB_NAME


def load_seed_data():
    """Load seed data from JSON file."""
    data_path = Path(__file__).parent.parent / "data" / "seed_data.json"
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)


def seed_database(drop_existing=False):
    """Seed the database with plants, diseases, and model class mappings."""

    # Connect to MongoDB
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB_NAME]

    print(f"Connected to MongoDB: {MONGO_DB_NAME}")

    # Drop existing collections if requested
    if drop_existing:
        print("Dropping existing collections...")
        db.plants.drop()
        db.diseases.drop()
        db.model_classes.drop()
        print("Collections dropped.")

    # Load seed data
    data = load_seed_data()

    # Track plant IDs for linking
    plant_ids = {}

    # Seed plants
    print("\nSeeding plants...")
    for plant_data in data["plants"]:
        plant_doc = {
            "canonical_name": plant_data["canonical_name"],
            "scientific_name": plant_data.get("scientific_name"),
            "names": plant_data.get("names", {}),
            "user_contributed_names": [],
            "care_instructions": plant_data.get("care_instructions", {}),
            "description": plant_data.get("description", {}),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # Check if plant already exists
        existing = db.plants.find_one({"canonical_name": plant_data["canonical_name"]})
        if existing:
            plant_ids[plant_data["canonical_name"]] = existing["_id"]
            print(f"  Plant already exists: {plant_data['canonical_name']}")
        else:
            result = db.plants.insert_one(plant_doc)
            plant_ids[plant_data["canonical_name"]] = result.inserted_id
            print(f"  Created plant: {plant_data['canonical_name']}")

    # Track disease IDs for model class mapping
    disease_ids = {}

    # Seed diseases
    print("\nSeeding diseases...")
    for disease_data in data["diseases"]:
        plant_id = plant_ids.get(disease_data["plant_canonical"])
        if not plant_id:
            print(f"  WARNING: Plant not found for disease: {disease_data['canonical_name']}")
            continue

        disease_doc = {
            "canonical_name": disease_data["canonical_name"],
            "model_class": disease_data["model_class"],
            "plant_id": plant_id,
            "names": disease_data.get("names", {}),
            "user_contributed_names": [],
            "description": disease_data.get("description", {}),
            "symptoms": disease_data.get("symptoms", {}),
            "cure": disease_data.get("cure", {}),
            "prevention": disease_data.get("prevention", {}),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }

        # Check if disease already exists
        existing = db.diseases.find_one({"model_class": disease_data["model_class"]})
        if existing:
            disease_ids[disease_data["model_class"]] = existing["_id"]
            print(f"  Disease already exists: {disease_data['canonical_name']}")
        else:
            result = db.diseases.insert_one(disease_doc)
            disease_ids[disease_data["model_class"]] = result.inserted_id
            print(f"  Created disease: {disease_data['canonical_name']}")

    # Seed model class mappings (for diseases)
    print("\nSeeding model class mappings for diseases...")
    for disease_data in data["diseases"]:
        plant_id = plant_ids.get(disease_data["plant_canonical"])
        disease_id = disease_ids.get(disease_data["model_class"])

        if not plant_id or not disease_id:
            continue

        model_class_doc = {
            "class_name": disease_data["model_class"],
            "plant_id": plant_id,
            "disease_id": disease_id,
            "is_healthy": False,
        }

        # Check if mapping already exists
        existing = db.model_classes.find_one({"class_name": disease_data["model_class"]})
        if existing:
            print(f"  Mapping already exists: {disease_data['model_class']}")
        else:
            db.model_classes.insert_one(model_class_doc)
            print(f"  Created mapping: {disease_data['model_class']}")

    # Seed model class mappings (for healthy plants)
    print("\nSeeding model class mappings for healthy plants...")
    for healthy_data in data["healthy_classes"]:
        plant_id = plant_ids.get(healthy_data["plant_canonical"])

        if not plant_id:
            print(f"  WARNING: Plant not found for healthy class: {healthy_data['model_class']}")
            continue

        model_class_doc = {
            "class_name": healthy_data["model_class"],
            "plant_id": plant_id,
            "disease_id": None,
            "is_healthy": True,
        }

        # Check if mapping already exists
        existing = db.model_classes.find_one({"class_name": healthy_data["model_class"]})
        if existing:
            print(f"  Mapping already exists: {healthy_data['model_class']}")
        else:
            db.model_classes.insert_one(model_class_doc)
            print(f"  Created mapping: {healthy_data['model_class']}")

    # Print summary
    print("\n" + "="*50)
    print("SEEDING COMPLETE")
    print("="*50)
    print(f"Plants in database: {db.plants.count_documents({})}")
    print(f"Diseases in database: {db.diseases.count_documents({})}")
    print(f"Model class mappings: {db.model_classes.count_documents({})}")

    # Close connection
    client.close()
    print("\nDatabase connection closed.")


def export_to_json():
    """Export current database content to JSON for backup."""
    client = MongoClient(MONGO_URI)
    db = client[MONGO_DB_NAME]

    export_data = {
        "plants": [],
        "diseases": [],
        "model_classes": [],
        "exported_at": datetime.utcnow().isoformat(),
    }

    # Export plants
    for plant in db.plants.find():
        plant["_id"] = str(plant["_id"])
        plant["created_at"] = plant.get("created_at", datetime.utcnow()).isoformat()
        plant["updated_at"] = plant.get("updated_at", datetime.utcnow()).isoformat()
        export_data["plants"].append(plant)

    # Export diseases
    for disease in db.diseases.find():
        disease["_id"] = str(disease["_id"])
        disease["plant_id"] = str(disease["plant_id"])
        disease["created_at"] = disease.get("created_at", datetime.utcnow()).isoformat()
        disease["updated_at"] = disease.get("updated_at", datetime.utcnow()).isoformat()
        export_data["diseases"].append(disease)

    # Export model classes
    for mc in db.model_classes.find():
        mc["_id"] = str(mc["_id"])
        mc["plant_id"] = str(mc["plant_id"])
        if mc.get("disease_id"):
            mc["disease_id"] = str(mc["disease_id"])
        export_data["model_classes"].append(mc)

    # Write to file
    export_path = Path(__file__).parent.parent / "data" / "database_export.json"
    with open(export_path, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    print(f"Database exported to: {export_path}")
    client.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Seed the Plant Disease database")
    parser.add_argument("--drop", action="store_true", help="Drop existing collections before seeding")
    parser.add_argument("--export", action="store_true", help="Export database to JSON instead of seeding")

    args = parser.parse_args()

    if args.export:
        export_to_json()
    else:
        seed_database(drop_existing=args.drop)
