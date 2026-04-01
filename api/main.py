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
from generators.sidecar_generator import SidecarGenerator

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
async def parse_evebi_file(
    evebi_file: UploadFile = File(...),
    ifc_file: UploadFile = File(None)
):
    """
    Parst EVEBI-Datei und gibt Vorschau + Mapping-Preview zurück (Step 2)
    """
    if not evebi_file.filename.endswith('.evea'):
        raise HTTPException(status_code=400, detail="EVEBI-Datei muss .evea Extension haben")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # EVEBI speichern
        evebi_path = temp_path / evebi_file.filename
        with open(evebi_path, 'wb') as f:
            shutil.copyfileobj(evebi_file.file, f)
        
        try:
            evebi_data = parse_evea(str(evebi_path))
            
            # Mapping Preview (wenn IFC vorhanden)
            mapping_preview = None
            if ifc_file:
                ifc_path = temp_path / ifc_file.filename
                with open(ifc_path, 'wb') as f:
                    shutil.copyfileobj(ifc_file.file, f)
                
                ifc_geometry = parse_ifc(str(ifc_path))
                mapping_result = map_ifc_to_evebi(ifc_geometry, evebi_data, strategy='auto')
                
                mapping_preview = {
                    "total_ifc": mapping_result.stats['total_ifc'],
                    "total_evebi": mapping_result.stats['total_evebi'],
                    "potential_matches": mapping_result.stats['matched'],
                    "match_rate": mapping_result.stats['match_rate']
                }
            
            return {
                "evebi_data": {
                    "project_name": evebi_data.project_name,
                    "materials": len(evebi_data.materials),
                    "constructions": len(evebi_data.constructions),
                    "elements": len(evebi_data.elements),
                    "zones": len(evebi_data.zones)
                },
                "mapping_preview": mapping_preview
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fehler beim Parsen: {str(e)}")


@app.post("/process")
async def process_files(
    ifc_file: UploadFile = File(...),
    evebi_file: UploadFile = File(...)
):
    """
    Verarbeitet IFC + EVEBI Dateien und generiert Sidecar JSON (Step 3)
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
            
            # 2. IFC parsen (vereinfacht - TODO: Echten IFC-Parser nutzen)
            print("\n🔍 Parse IFC...")
            # Für jetzt: Mock-Daten (später echten IFC-Parser integrieren)
            ifc_dict = {
                "project_name": evebi_dict['project_name'],
                "building_guid": "MOCK-BUILDING-GUID",
                "walls": [],
                "roofs": [],
                "floors": [],
                "windows": [],
                "doors": []
            }
            print(f"⚠️  IFC-Parser noch nicht integriert (Mock-Daten)")
            
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
            print(f"   - Bauteile: {len(sidecar['input']['elements'])}")
            print(f"   - Fenster: {len(sidecar['input']['windows'])}")
            
            return {
                "success": True,
                "sidecar": sidecar,
                "stats": {
                    "evebi_elements": len(evebi_dict['elements']),
                    "evebi_zones": len(evebi_dict['zones']),
                    "sidecar_elements": len(sidecar['input']['elements']),
                    "sidecar_windows": len(sidecar['input']['windows']),
                    "sidecar_zones": len(sidecar['input']['zones'])
                },
                "warnings": [
                    "IFC-Parser noch nicht integriert - keine IFC-EVEBI Verknüpfung"
                ]
            }
            
        except Exception as e:
            import traceback
            print(f"❌ Fehler: {e}")
            print(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Fehler beim Generieren: {str(e)}")
