from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import tempfile
import shutil
from pathlib import Path
from jsonschema import validate, ValidationError

# Neue Imports für Sidecar Generator v2
from parsers.evebi_parser import parse_evea, evebi_data_to_dict
from parsers.ifc_parser import parse_ifc, ifc_geometry_to_dict
from generators.sidecar_generator import SidecarGenerator

app = FastAPI(
    title="DIN 18599 Sidecar API",
    description="API für IFC + EVEBI Upload, Parsing und Sidecar-Generierung",
    version="2.0.0"
)

# CORS für Viewer
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3002", "http://localhost:3003", "http://localhost:5173"],
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
    # Schema ist optional - Backend funktioniert auch ohne
    schema_status = "loaded" if SCHEMA is not None else "not_loaded"
    return {"status": "healthy", "version": "1.0.0", "schema": schema_status}

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


@app.post("/parse-ifc")
async def parse_ifc_file(ifc_file: UploadFile = File(...)):
    """
    Parst IFC-Datei und gibt Vorschau zurück (Step 1)
    """
    if not ifc_file.filename.endswith('.ifc'):
        raise HTTPException(status_code=400, detail="IFC-Datei muss .ifc Extension haben")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        ifc_path = temp_path / ifc_file.filename
        
        with open(ifc_path, 'wb') as f:
            shutil.copyfileobj(ifc_file.file, f)
        
        try:
            ifc_geometry = parse_ifc(str(ifc_path))
            
            return {
                "project_name": ifc_geometry.project_name,
                "building_name": ifc_geometry.building_name,
                "walls": len(ifc_geometry.walls),
                "roofs": len(ifc_geometry.roofs),
                "slabs": len(ifc_geometry.slabs),
                "windows": len(ifc_geometry.windows),
                "doors": len(ifc_geometry.doors),
                "total_elements": len(ifc_geometry.all_elements)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fehler beim Parsen: {str(e)}")


@app.post("/parse-evebi")
async def parse_evebi_endpoint(
    evebi_file: UploadFile = File(...),
    ifc_file: UploadFile = File(None)
):
    """
    Parst EVEBI-Datei und gibt strukturierte Daten zurück
    """
    # Validierung
    if not (evebi_file.filename.endswith('.evea') or evebi_file.filename.endswith('.evex')):
        raise HTTPException(status_code=400, detail="EVEBI-Datei muss .evea oder .evex Extension haben")
    
    # Temporäre Dateien erstellen
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # EVEBI speichern
        evebi_path = temp_path / evebi_file.filename
        with open(evebi_path, 'wb') as f:
            shutil.copyfileobj(evebi_file.file, f)
        
        try:
            # EVEBI parsen
            evebi_data = parse_evea(str(evebi_path))
            
            # Frontend erwartet nur Anzahlen, nicht vollständige Daten
            return {
                "success": True,
                "evebi_data": {
                    "project_name": evebi_data.project_name,
                    "materials": len(evebi_data.materials),
                    "constructions": len(evebi_data.constructions),
                    "elements": len(evebi_data.elements),
                    "zones": len(evebi_data.zones)
                }
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Fehler beim Parsen: {str(e)}")


@app.post("/generate-sidecar")
async def generate_sidecar_json(
    ifc_file: UploadFile = File(...),
    evebi_file: UploadFile = File(...)
):
    """
    Generiert DIN18599 Sidecar JSON aus IFC + EVEBI (Neue Version mit SidecarGenerator)
    """
    print("\n=== Sidecar Generator v2 ===")
    
    # Validierung
    if not ifc_file.filename.endswith('.ifc'):
        raise HTTPException(status_code=400, detail="IFC-Datei muss .ifc Extension haben")
    
    if not (evebi_file.filename.endswith('.evea') or evebi_file.filename.endswith('.evex')):
        raise HTTPException(status_code=400, detail="EVEBI-Datei muss .evea oder .evex Extension haben")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # IFC speichern
        ifc_path = temp_path / ifc_file.filename
        with open(ifc_path, 'wb') as f:
            shutil.copyfileobj(ifc_file.file, f)
        print(f"📂 IFC gespeichert: {ifc_path}")
        
        # EVEBI speichern
        evebi_path = temp_path / evebi_file.filename
        with open(evebi_path, 'wb') as f:
            shutil.copyfileobj(evebi_file.file, f)
        print(f"📂 EVEBI gespeichert: {evebi_path}")
        
        try:
            # 1. EVEBI parsen
            print("\n🔍 Parse EVEBI...")
            evebi_data = parse_evea(str(evebi_path))
            evebi_dict = evebi_data_to_dict(evebi_data)
            
            print(f"✅ EVEBI geparst:")
            print(f"   - Projekt: {evebi_dict['project_name']}")
            print(f"   - Materialien: {len(evebi_dict['materials'])}")
            print(f"   - Konstruktionen: {len(evebi_dict['constructions'])}")
            print(f"   - Bauteile: {len(evebi_dict['elements'])}")
            print(f"   - Zonen: {len(evebi_dict['zones'])}")
            
            # 2. IFC parsen
            print("\n🔍 Parse IFC...")
            ifc_geometry = parse_ifc(str(ifc_path))
            ifc_dict = ifc_geometry_to_dict(ifc_geometry)
            
            print(f"✅ IFC geparst:")
            print(f"   - Projekt: {ifc_dict['project_name']}")
            print(f"   - Wände: {len(ifc_dict['walls'])}")
            print(f"   - Dächer: {len(ifc_dict['roofs'])}")
            print(f"   - Böden: {len(ifc_dict['floors'])}")
            print(f"   - Fenster: {len(ifc_dict['windows'])}")
            print(f"   - Türen: {len(ifc_dict['doors'])}")
            
            # 3. Sidecar generieren
            print("\n🔨 Generiere Sidecar JSON...")
            generator = SidecarGenerator()
            sidecar = generator.generate(
                ifc_data=ifc_dict,
                evebi_data=evebi_dict,
                project_name=evebi_dict['project_name'],
                ifc_file_ref=ifc_file.filename
            )
            
            print(f"✅ Sidecar generiert!")
            print(f"   - Zonen: {len(sidecar['input']['zones'])}")
            print(f"   - Materialien: {len(sidecar['input']['materials'])}")
            print(f"   - Konstruktionen: {len(sidecar['input']['layer_structures'])}")
            
            # Envelope Stats
            envelope = sidecar['input']['envelope']
            print(f"   - Außenwände: {len(envelope['walls_external'])}")
            print(f"   - Dächer: {len(envelope['roofs'])}")
            print(f"   - Gauben: {len(envelope.get('dormers', []))}")
            print(f"   - Böden: {len(envelope['floors'])}")
            print(f"   - Fenster: {len(envelope['openings'])}")
            
            # Stats berechnen
            total_ifc = len(ifc_dict['walls']) + len(ifc_dict['roofs']) + len(ifc_dict['floors']) + len(ifc_dict['windows']) + len(ifc_dict['doors'])
            total_sidecar = len(envelope['walls_external']) + len(envelope['roofs']) + len(envelope['floors']) + len(envelope['openings'])
            
            warnings = []
            if total_sidecar < total_ifc:
                unmatched = total_ifc - total_sidecar
                warnings.append(f"{unmatched} IFC-Elemente konnten nicht mit EVEBI-Daten gematcht werden")
            
            return {
                "success": True,
                "sidecar": sidecar,
                "stats": {
                    "ifc_elements": total_ifc,
                    "evebi_elements": len(evebi_dict['elements']),
                    "evebi_zones": len(evebi_dict['zones']),
                    "sidecar_walls": len(envelope['walls_external']),
                    "sidecar_roofs": len(envelope['roofs']),
                    "sidecar_dormers": len(envelope.get('dormers', [])),
                    "sidecar_floors": len(envelope['floors']),
                    "sidecar_windows": len(envelope['openings']),
                    "sidecar_zones": len(sidecar['input']['zones']),
                    "match_rate": round(total_sidecar / total_ifc * 100, 1) if total_ifc > 0 else 0
                },
                "warnings": warnings
            }
            
        except Exception as e:
            import traceback
            print(f"❌ Fehler: {e}")
            print(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Fehler beim Generieren: {str(e)}")
