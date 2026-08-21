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
from adapters.evebi import normalize_evebi, parse_evea, evebi_data_to_dict
from parsers.ifc_parser import parse_ifc, ifc_geometry_to_dict
from parsers.ifc_v4_parser import parse_ifc_to_sidecar_v4
from generators.sidecar_generator import SidecarGenerator

# QNG/external-import module (Phase 3.9 Welle 3)
try:
    from qng.orchestrator import orchestrate as qng_orchestrate
    QNG_AVAILABLE = True
except ImportError:
    QNG_AVAILABLE = False

# Datenbank-Integration (optional — funktioniert auch ohne PostgreSQL).
# Der /db/*-Router ist ein bewusst optionaler Zweig: schlaegt der Import fehl,
# laeuft die API ohne DB-Endpoints weiter (die DWEapp nutzt sie nicht, sie
# importiert Sidecars ueber ihre eigene Prisma-Schicht).
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
DB_IMPORT_ERROR = None
try:
    from database.python.api_routes import create_db_router
    DB_AVAILABLE = True
except ImportError as e:
    # Grund festhalten, statt ihn pauschal psycopg2 anzulasten. Im api-only
    # Container-Mount (nur api/ -> /app) liegt das database/-Paket nicht im
    # Python-Pfad -> "No module named 'database'"; psycopg2 selbst ist optional
    # und in db.py zusaetzlich per try/except abgesichert.
    DB_AVAILABLE = False
    DB_IMPORT_ERROR = e

app = FastAPI(
    title="DIN 18599 Sidecar API",
    description="API fuer IFC-Import, Sidecar-Erzeugung, Validierung und Datenbank. Produktspezifische Importadapter sind separat gekennzeichnet.",
    version="2.1.0"
)

# Datenbank-Router einbinden (wenn verfügbar)
if DB_AVAILABLE:
    db_router = create_db_router()
    app.include_router(db_router, prefix="/db")
    print("✅ Datenbank-Endpoints verfügbar unter /db/*")
else:
    print(f"Datenbank-Endpoints nicht verfuegbar (optional). Grund: {DB_IMPORT_ERROR}")

# CORS für Viewer
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3002", "http://localhost:3003", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load schema on startup
# Load supported schemas on startup. v3.1 remains the legacy default; v4.0 is
# selected from the submitted sidecar's schema_info URL/version.
SCHEMA_PATHS = {
    "v3.1": os.path.join(os.path.dirname(__file__), "../schema/v3.1-complete.json"),
    "v4.0": os.path.join(os.path.dirname(__file__), "../schema/v4.0/sidecar.schema.json"),
}
SCHEMAS = {}
for schema_key, schema_path in SCHEMA_PATHS.items():
    try:
        with open(schema_path, "r") as schema_file:
            SCHEMAS[schema_key] = json.load(schema_file)
    except Exception as error:
        print(f"Schema {schema_key} konnte nicht geladen werden von {schema_path}: {error}")

SCHEMA = SCHEMAS.get("v3.1")

@app.get("/health")
def health_check():
    # Schema ist optional - Backend funktioniert auch ohne
    schema_status = "loaded" if SCHEMA is not None else "not_loaded"
    return {
        "status": "healthy",
        "version": "2.1.0",
        "schema": schema_status,
        "schemas": sorted(SCHEMAS),
    }

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

    schema_key = "v3.1"
    schema_info = data.get("schema_info", {}) if isinstance(data, dict) else {}
    schema_url = schema_info.get("url", "")
    schema_version = schema_info.get("version", "")
    if "/v4.0/" in schema_url or str(schema_version).startswith("4.0."):
        schema_key = "v4.0"
    schema = SCHEMAS.get(schema_key)
    if schema is None:
        raise HTTPException(status_code=503, detail=f"Schema {schema_key} nicht verfügbar")

    try:
        validate(instance=data, schema=schema)
        return {
            "valid": True,
            "filename": file.filename,
            "schema": schema_key,
            "message": "Datei ist valide gegenüber dem DIN 18599 Sidecar Schema."
        }
    except ValidationError as e:
        return JSONResponse(
            status_code=422,
            content={
                "valid": False,
                "filename": file.filename,
                "schema": schema_key,
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


@app.post("/parse-ifc-v4")
async def parse_ifc_v4_endpoint(ifc_file: UploadFile = File(...)):
    """
    Erzeugt aus einer NACKTEN IFC-Datei (ohne mitgelieferten Sidecar) ein
    strukturell gueltiges v4.0-Sidecar auf Level ``draft`` — Eingangs-Kanal 2
    "IFC-Upload" der Gebaeudeakte.

    Nimmt bewusst NUR ``ifc_file`` (kein ``evebi_file`` wie /generate-sidecar):
    das ist der IFC-only-Bootstrap, den der Alt-Endpunkt nicht bedienen konnte.
    Der Berater zieht das zurueckgelieferte Skelett danach mensch-gefuehrt hoch.

    Vertrag: ``docs/v4/SPEC-ifc-skelett-parser-v4.md`` §9.1 (rein geometrisch,
    ADR-033). Erwartete Validator-Warnungen auf ``draft``: BOUNDARIES_EMPTY und
    HEATING_STATUS_UNCONFIRMED — beide blockieren erst ``geometry_ok``.
    """
    if not ifc_file.filename.endswith('.ifc'):
        raise HTTPException(status_code=400, detail="IFC-Datei muss .ifc Extension haben")

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        ifc_path = temp_path / ifc_file.filename

        with open(ifc_path, 'wb') as f:
            shutil.copyfileobj(ifc_file.file, f)

        try:
            sidecar = parse_ifc_to_sidecar_v4(
                str(ifc_path),
                ifc_file_ref=ifc_file.filename,
            )
            return JSONResponse(content=sidecar)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fehler beim Parsen: {str(e)}")


@app.post(
    "/parse-ifc-neutral",
    tags=["neutral"],
    summary="Build a neutral v4 sidecar from IFC",
)
async def parse_ifc_neutral_endpoint(
    ifc_file: UploadFile = File(...),
    building_type: str = "non_residential",
):
    """Parse IFC through the neutral adapter and sidecar builder.

    This endpoint deliberately sits beside ``/parse-ifc-v4`` during the
    migration. The established endpoint remains byte-shape compatible while
    this route makes the new adapter/core boundary observable.
    """
    if not ifc_file.filename.endswith(".ifc"):
        raise HTTPException(status_code=400, detail="IFC-Datei muss .ifc Extension haben")

    with tempfile.TemporaryDirectory() as temp_dir:
        ifc_path = Path(temp_dir) / ifc_file.filename
        with open(ifc_path, "wb") as file_handle:
            shutil.copyfileobj(ifc_file.file, file_handle)

        try:
            from adapters.ifc import parse_ifc_to_bundle
            from core.sidecar_builder import build_draft_sidecar

            bundle = parse_ifc_to_bundle(
                str(ifc_path),
                ifc_file_ref=ifc_file.filename,
                building_type=building_type,
            )
            project_name = bundle.metadata.get("project_name") or ifc_file.filename
            sidecar = build_draft_sidecar(
                bundle,
                project_name=project_name,
                building_type=building_type,
                ifc_file_ref=ifc_file.filename,
            )
            return JSONResponse(content=sidecar)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fehler beim neutralen IFC-Parsing: {str(e)}")


@app.post(
    "/parse-evebi",
    tags=["adapter:evebi"],
    deprecated=True,
    summary="Legacy EVEBI adapter import",
)
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
            normalized = normalize_evebi(
                evebi_data,
                source_ref=evebi_file.filename,
            )
            
            # Frontend erwartet nur Anzahlen, nicht vollständige Daten
            return {
                "success": True,
                "evebi_data": {
                    "project_name": evebi_data.project_name,
                    "materials": len(evebi_data.materials),
                    "constructions": len(evebi_data.constructions),
                    "elements": len(evebi_data.elements),
                    "zones": len(evebi_data.zones)
                },
                "normalized_import": {
                    "origin": normalized.provenance.origin if normalized.provenance else None,
                    "elements": len(normalized.elements),
                    "constructions": len(normalized.constructions),
                    "rooms": len(normalized.rooms),
                    "zones": len(normalized.zones),
                    "systems": len(normalized.systems),
                }
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Fehler beim Parsen: {str(e)}")


@app.post(
    "/generate-sidecar",
    tags=["adapter:evebi"],
    deprecated=True,
    summary="Legacy IFC plus EVEBI sidecar generation",
)
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


# ─────────────────────────────────────────────────────────────────────────────
# QNG/external-import endpoint — Phase 3.9 Welle 3
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/qng/parse")
async def qng_parse(file: UploadFile = File(...)):
    """
    Erkennt externe Importformate automatisch und extrahiert QNG-relevante Werte.

    Unterstützte Formate:
    - BEG-GEG-Nachweis-Import.xml  → deterministisch, Confidence 1.0
    - eLCA XML Export               → deterministisch, Confidence 1.0
    - idi-al.ini                    → deterministisch, Confidence 1.0
    - Nachhaltigkeit.docx           → Ollama-unterstützt, Confidence < 1.0
    - IFC                           → nur Metadaten, Confidence 0.0

    Response:
    {
      "kanal":          str,           # EingangKanal-Enum
      "ki_extrahiert":  { "sidecar.pfad": {"wert": X, "confidence": 1.0} },
      "ki_confidence":  float,
      "direkt_freigabe": bool,         # true = sofort in Sidecar schreiben
      "warnungen":      [str],
    }
    """
    if not QNG_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="QNG-Parser nicht verfügbar (Import-Fehler beim Start).",
        )

    content = await file.read()
    filename = file.filename or "unbekannt"

    try:
        result = qng_orchestrate(content, filename)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        import traceback
        print(f"❌ QNG-Parser Fehler: {e}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Parser-Fehler: {str(e)}")

    return {
        "adapter":         result.adapter,
        "source_format":   result.source_format,
        "kanal":           result.kanal,
        "ki_extrahiert":   result.ki_extrahiert,
        "ki_confidence":   result.ki_confidence,
        "direkt_freigabe": result.direkt_freigabe,
        "warnungen":       result.warnungen,
        **({"bauteilkatalog": result.bauteilkatalog} if result.bauteilkatalog else {}),
    }
