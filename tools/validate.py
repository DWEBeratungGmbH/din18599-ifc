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
        print(f"Fehler: Schema-Datei nicht gefunden unter {schema_path}")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Fehler: Schema-Datei ist kein gültiges JSON: {schema_path}")
        sys.exit(1)

def validate_file(json_path, schema):
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Fehler: Eingabedatei nicht gefunden unter {json_path}")
        return False
    except json.JSONDecodeError:
        print(f"Fehler: Eingabedatei ist kein gültiges JSON: {json_path}")
        return False

    try:
        validate(instance=data, schema=schema)
        print(f"✅ Validierung erfolgreich: {json_path}")
        return True
    except ValidationError as e:
        print(f"❌ Validierung fehlgeschlagen: {json_path}")
        print(f"   Fehler: {e.message}")
        print(f"   Pfad: {' -> '.join(str(p) for p in e.path)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Validiert eine JSON-Datei gegen das DIN 18599 Sidecar Schema.")
    parser.add_argument("file", help="Pfad zur .din18599.json Datei")
    parser.add_argument("--schema", default="../gebaeude.din18599.schema.json", help="Pfad zur Schema-Datei (Standard: ../gebaeude.din18599.schema.json)")
    
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
