#!/usr/bin/env python3
"""Export OpenAPI specification to YAML file for Flutter code generation."""

import sys
import json
import yaml
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from api.app import create_app


def export_openapi_spec(output_file="openapi.yaml"):
    """
    Export OpenAPI specification from Flask app to YAML file.

    Args:
        output_file: Path to output YAML file
    """
    # Create Flask app
    app = create_app()

    # Get OpenAPI spec from Flasgger
    with app.test_client() as client:
        # Flasgger generates spec at /apispec.json
        response = client.get('/apispec.json')

        if response.status_code != 200:
            print(f"Error: Failed to get OpenAPI spec (status {response.status_code})")
            sys.exit(1)

        spec = response.get_json()

    # Write to YAML file
    output_path = Path(__file__).parent / output_file
    with open(output_path, 'w') as f:
        yaml.dump(spec, f, default_flow_style=False, sort_keys=False)

    print(f"✓ OpenAPI specification exported to: {output_path}")
    print(f"✓ API Title: {spec['info']['title']}")
    print(f"✓ API Version: {spec['info']['version']}")
    print(f"✓ Endpoints: {len(spec.get('paths', {}))}")
    print("\nFlutter developer can now use this file with openapi-generator:")
    print("  openapi-generator-cli generate \\")
    print("    -i openapi.yaml \\")
    print("    -g dart \\")
    print("    -o flutter_client")


if __name__ == '__main__':
    export_openapi_spec()
