from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import json
import os
from jsonschema import validate, ValidationError

app = FastAPI(
    title="DIN 18599 Sidecar Validator API",
    description="Microservice zur Validierung von DIN 18599 Sidecar JSON-Dateien gegen das Schema.",
    version="1.0.0"
)

# Load schema on startup
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "../gebaeude.din18599.schema.json")
try:
    with open(SCHEMA_PATH, "r") as f:
        SCHEMA = json.load(f)
except Exception as e:
    print(f"KRITISCH: Schema konnte nicht geladen werden von {SCHEMA_PATH}: {e}")
    SCHEMA = None

@app.get("/health")
def health_check():
    if SCHEMA is None:
        return JSONResponse(status_code=503, content={"status": "unhealthy", "reason": "Schema nicht geladen"})
    return {"status": "healthy", "version": "1.0.0"}

@app.post("/validate")
async def validate_json(file: UploadFile):
    if SCHEMA is None:
        raise HTTPException(status_code=503, detail="Validator-Service nicht verfügbar (Schema fehlt)")
    
    if not file.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="Datei muss eine JSON-Datei sein")

    try:
        content = await file.read()
        data = json.loads(content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Ungültiges JSON-Format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Lesen der Datei: {str(e)}")

    try:
        validate(instance=data, schema=SCHEMA)
        return {
            "valid": True,
            "filename": file.filename,
            "message": "Datei ist valide gegenüber dem DIN 18599 Sidecar Schema."
        }
    except ValidationError as e:
        return JSONResponse(
            status_code=422,
            content={
                "valid": False,
                "filename": file.filename,
                "error": e.message,
                "path": list(e.path),
                "schema_path": list(e.schema_path)
            }
        )
