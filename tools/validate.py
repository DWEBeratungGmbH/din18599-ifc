import json
import argparse
import sys
import os
from jsonschema import validate, ValidationError

def load_schema(schema_path):
    try:
        with open(schema_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Schema file not found at {schema_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Schema file is not valid JSON at {schema_path}")
        sys.exit(1)

def validate_file(json_path, schema):
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Input file not found at {json_path}")
        return False
    except json.JSONDecodeError:
        print(f"Error: Input file is not valid JSON at {json_path}")
        return False

    try:
        validate(instance=data, schema=schema)
        print(f"✅ Validation successful: {json_path}")
        return True
    except ValidationError as e:
        print(f"❌ Validation failed: {json_path}")
        print(f"   Error: {e.message}")
        print(f"   Path: {' -> '.join(str(p) for p in e.path)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Validate a JSON file against the DIN 18599 Sidecar Schema.")
    parser.add_argument("file", help="Path to the .din18599.json file to validate")
    parser.add_argument("--schema", default="../gebaeude.din18599.schema.json", help="Path to the schema file (default: ../gebaeude.din18599.schema.json)")
    
    args = parser.parse_args()

    # Resolve paths relative to script location if default is used
    if args.schema == "../gebaeude.din18599.schema.json":
        script_dir = os.path.dirname(os.path.abspath(__file__))
        schema_path = os.path.join(script_dir, args.schema)
    else:
        schema_path = args.schema

    schema = load_schema(schema_path)
    success = validate_file(args.file, schema)
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
