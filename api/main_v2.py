"""
FastAPI Backend v2 - Neuer 2-Schritt-Workflow
1. IFC-Analyse (unabhängig)
2. EVEBI-Mapping auf IFC-JSON
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import tempfile
import os
from pathlib import Path
from typing import Dict, Any

from parsers.ifc_parser import parse_ifc_file
from parsers.evebi_parser import parse_evea_file
from generators.sidecar_generator import SidecarGenerator

app = FastAPI(title="DIN18599 IFC-EVEBI Backend v2")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0"}


@app.post("/analyze-ifc")
async def analyze_ifc(file: UploadFile = File(...)):
    """
    Schritt 1: Analysiere IFC-Datei (unabhängig)
    
    Returns:
        IFC-JSON mit vollständiger Geometrie-Analyse
    """
    try:
        print(f"\n{'='*60}")
        print(f"📐 SCHRITT 1: IFC-ANALYSE")
        print(f"{'='*60}\n")
        
        # Temporäre Datei speichern
        with tempfile.NamedTemporaryFile(delete=False, suffix='.ifc') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # IFC parsen
            print(f"📂 Parse IFC: {file.filename}")
            ifc_data = parse_ifc_file(tmp_path)
            
            # Statistiken
            total_elements = (
                len(ifc_data['walls']) + 
                len(ifc_data['roofs']) + 
                len(ifc_data['floors']) + 
                len(ifc_data['windows']) + 
                len(ifc_data['doors'])
            )
            
            print(f"\n✅ IFC-Analyse abgeschlossen:")
            print(f"   - Wände:   {len(ifc_data['walls'])}")
            print(f"   - Dächer:  {len(ifc_data['roofs'])}")
            print(f"   - Böden:   {len(ifc_data['floors'])}")
            print(f"   - Fenster: {len(ifc_data['windows'])}")
            print(f"   - Türen:   {len(ifc_data['doors'])}")
            print(f"   - Total:   {total_elements}")
            
            return {
                "success": True,
                "ifc_data": ifc_data,
                "stats": {
                    "total_elements": total_elements,
                    "walls": len(ifc_data['walls']),
                    "roofs": len(ifc_data['roofs']),
                    "floors": len(ifc_data['floors']),
                    "windows": len(ifc_data['windows']),
                    "doors": len(ifc_data['doors'])
                }
            }
            
        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"❌ Fehler bei IFC-Analyse: {e}")
        print(error_detail)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-evebi")
async def analyze_evebi(file: UploadFile = File(...)):
    """
    Analysiere EVEBI-Datei (unabhängig)
    
    Returns:
        EVEBI-JSON mit allen Elementen und Zonen
    """
    try:
        print(f"\n{'='*60}")
        print(f"📋 EVEBI-ANALYSE")
        print(f"{'='*60}\n")
        
        # Temporäre Datei speichern
        with tempfile.NamedTemporaryFile(delete=False, suffix='.evea') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # EVEBI parsen
            print(f"📂 Parse EVEBI: {file.filename}")
            evebi_data = parse_evea_file(tmp_path)
            
            print(f"\n✅ EVEBI-Analyse abgeschlossen:")
            print(f"   - Elemente: {len(evebi_data['elements'])}")
            print(f"   - Zonen:    {len(evebi_data['zones'])}")
            
            return {
                "success": True,
                "evebi_data": evebi_data,
                "stats": {
                    "elements": len(evebi_data['elements']),
                    "zones": len(evebi_data['zones'])
                }
            }
            
        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"❌ Fehler bei EVEBI-Analyse: {e}")
        print(error_detail)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/map-evebi-to-sidecar")
async def map_evebi_to_sidecar(
    ifc_data: Dict[str, Any] = Body(...),
    evebi_file: UploadFile = File(...)
):
    """
    Schritt 2: Mappe EVEBI-Daten auf IFC-JSON → Sidecar
    
    Body:
        ifc_data: IFC-JSON aus /analyze-ifc
        evebi_file: EVEBI-Datei
    
    Returns:
        DIN18599 Sidecar JSON
    """
    try:
        print(f"\n{'='*60}")
        print(f"🔗 SCHRITT 2: EVEBI-MAPPING")
        print(f"{'='*60}\n")
        
        # EVEBI parsen
        with tempfile.NamedTemporaryFile(delete=False, suffix='.evea') as tmp:
            content = await evebi_file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            print(f"📂 Parse EVEBI: {evebi_file.filename}")
            evebi_data = parse_evea_file(tmp_path)
            
            # Sidecar generieren
            print(f"\n🔧 Generiere Sidecar...")
            generator = SidecarGenerator()
            sidecar = generator.generate(ifc_data, evebi_data)
            
            # Statistiken
            envelope = sidecar['input']['envelope']
            
            print(f"\n✅ Sidecar generiert!")
            print(f"   - Wände:   {len(envelope['walls_external'])}")
            print(f"   - Dächer:  {len(envelope['roofs'])}")
            print(f"   - Gauben:  {len(envelope.get('dormers', []))}")
            print(f"   - Böden:   {len(envelope['floors'])}")
            print(f"   - Fenster: {len(envelope['openings'])}")
            print(f"   - Zonen:   {len(sidecar['input']['zones'])}")
            
            return {
                "success": True,
                "sidecar": sidecar,
                "stats": {
                    "walls": len(envelope['walls_external']),
                    "roofs": len(envelope['roofs']),
                    "dormers": len(envelope.get('dormers', [])),
                    "floors": len(envelope['floors']),
                    "windows": len(envelope['openings']),
                    "zones": len(sidecar['input']['zones'])
                }
            }
            
        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"❌ Fehler beim EVEBI-Mapping: {e}")
        print(error_detail)
        raise HTTPException(status_code=500, detail=str(e))


# Legacy endpoint (für Kompatibilität)
@app.post("/generate-sidecar")
async def generate_sidecar_legacy(
    ifc_file: UploadFile = File(...),
    evebi_file: UploadFile = File(...)
):
    """
    Legacy: Kombinierter Endpoint (für Rückwärtskompatibilität)
    Nutzt intern den neuen 2-Schritt-Workflow
    """
    try:
        # Schritt 1: IFC analysieren
        ifc_response = await analyze_ifc(ifc_file)
        ifc_data = ifc_response["ifc_data"]
        
        # Schritt 2: EVEBI mappen
        sidecar_response = await map_evebi_to_sidecar(ifc_data, evebi_file)
        
        return sidecar_response
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"❌ Fehler: {e}")
        print(error_detail)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
