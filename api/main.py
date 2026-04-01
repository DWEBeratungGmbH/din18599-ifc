from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import tempfile
import shutil
from pathlib import Path
from jsonschema import validate, ValidationError
from parsers import parse_evea, parse_ifc, map_ifc_to_evebi, generate_sidecar

app = FastAPI(
    title="DIN 18599 Sidecar API",
    description="API für IFC + EVEBI Upload, Parsing und Sidecar-Generierung",
    version="2.0.0"
)

# CORS für Viewer
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


@app.post("/process")
async def process_files(
    ifc_file: UploadFile = File(...),
    evebi_file: UploadFile = File(...)
):
    """
    Verarbeitet IFC + EVEBI Dateien und generiert Sidecar JSON
    """
    # Validierung
    if not ifc_file.filename.endswith('.ifc'):
        raise HTTPException(status_code=400, detail="IFC-Datei muss .ifc Extension haben")
    
    if not evebi_file.filename.endswith('.evea'):
        raise HTTPException(status_code=400, detail="EVEBI-Datei muss .evea Extension haben")
    
    # Temporäre Dateien erstellen
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # IFC speichern
        ifc_path = temp_path / ifc_file.filename
        with open(ifc_path, 'wb') as f:
            shutil.copyfileobj(ifc_file.file, f)
        
        # EVEBI speichern
        evebi_path = temp_path / evebi_file.filename
        with open(evebi_path, 'wb') as f:
            shutil.copyfileobj(evebi_file.file, f)
        
        try:
            # 1. IFC parsen
            ifc_geometry = parse_ifc(str(ifc_path))
            
            # 2. EVEBI parsen
            evebi_data = parse_evea(str(evebi_path))
            
            # 3. Mapping
            mapping_result = map_ifc_to_evebi(ifc_geometry, evebi_data, strategy='auto')
            
            # 4. Sidecar generieren
            sidecar = generate_sidecar(
                ifc_geometry=ifc_geometry,
                evebi_data=evebi_data,
                mapping_result=mapping_result,
                ifc_filename=ifc_file.filename,
                evebi_filename=evebi_file.filename
            )
            
            return {
                "success": True,
                "sidecar": sidecar,
                "stats": mapping_result.stats,
                "warnings": [
                    f"{len(mapping_result.unmatched_ifc)} IFC-Elemente nicht gemappt",
                    f"{len(mapping_result.unmatched_evebi)} EVEBI-Elemente nicht gemappt"
                ] if mapping_result.unmatched_ifc or mapping_result.unmatched_evebi else []
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fehler beim Verarbeiten: {str(e)}")
