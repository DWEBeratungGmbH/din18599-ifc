"""
DIN 18599 Sidecar — FastAPI Routen für Datenbank-Integration

Stellt REST-Endpoints bereit für:
    - POST /db/validate     → JSON validieren (ohne Import)
    - POST /db/import       → JSON validieren + in DB importieren
    - GET  /db/projects     → Alle Projekte auflisten
    - GET  /db/export/{id}  → Sidecar exportieren (1:1 Original-JSON)
    - GET  /db/versions/{project_id} → Alle Versionen eines Projekts
    - GET  /db/import-log/{project_id} → Import-Protokoll
    - DELETE /db/projects/{id} → Projekt löschen

Einbindung in main.py:
    from database.python.api_routes import create_db_router
    app.include_router(create_db_router(db_url), prefix="/db")
"""

import json
import os
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse

from .validator import SidecarValidator
from .db import SidecarDB


def create_db_router(database_url: Optional[str] = None) -> APIRouter:
    """
    Erstellt den FastAPI-Router für Datenbank-Operationen.

    Args:
        database_url: PostgreSQL Connection-String.
                      Fallback auf Umgebungsvariable DATABASE_URL.
    """
    router = APIRouter(tags=["Datenbank"])
    validator = SidecarValidator()

    # DB-Verbindung: Aus Parameter oder Umgebungsvariable
    db_url = database_url or os.environ.get(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/din18599"
    )

    def _get_db() -> SidecarDB:
        """Erstellt eine DB-Instanz (lazy, keine Verbindung beim Import)"""
        return SidecarDB(db_url)

    # ──────────────────────────────────────────────────────────────
    # POST /db/validate — Nur validieren, nicht importieren
    # ──────────────────────────────────────────────────────────────

    @router.post("/validate")
    async def validate_sidecar(file: UploadFile = File(...)):
        """
        Validiert eine Sidecar-JSON-Datei (3 Ebenen).
        Importiert NICHT in die Datenbank.

        Nützlich für: Vorab-Prüfung bevor man importiert.
        """
        if not file.filename.endswith(".json"):
            raise HTTPException(400, "Datei muss .json Extension haben")

        try:
            content = await file.read()
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise HTTPException(400, f"Ungültiges JSON: {e}")

        result = validator.validate(data)
        return result.to_dict()

    # ──────────────────────────────────────────────────────────────
    # POST /db/import — Validieren + Importieren
    # ──────────────────────────────────────────────────────────────

    @router.post("/import")
    async def import_sidecar(
        file: UploadFile = File(...),
        project_name: Optional[str] = Query(None, description="Projektname (optional)"),
        project_id: Optional[str] = Query(None, description="Bestehendes Projekt-UUID (optional)"),
    ):
        """
        Validiert und importiert eine Sidecar-JSON-Datei in die Datenbank.

        Ablauf:
            1. JSON parsen
            2. 3-Ebenen-Validierung
            3. Bei Fehlern: Abbruch + Import-Log
            4. Bei Erfolg/Warnings: Import + extrahierte Metadaten
        """
        if not file.filename.endswith(".json"):
            raise HTTPException(400, "Datei muss .json Extension haben")

        try:
            content = await file.read()
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise HTTPException(400, f"Ungültiges JSON: {e}")

        db = _get_db()
        result = db.import_sidecar(
            data=data,
            project_name=project_name,
            project_id=project_id,
            filename=file.filename,
        )

        status_code = 200 if result.success else 422
        return JSONResponse(status_code=status_code, content=result.to_dict())

    # ──────────────────────────────────────────────────────────────
    # GET /db/projects — Alle Projekte auflisten
    # ──────────────────────────────────────────────────────────────

    @router.get("/projects")
    async def list_projects():
        """
        Listet alle Projekte mit aktuellem Sidecar-Status.
        Nutzt die v_projects_overview View für schnelle Abfrage.
        """
        db = _get_db()
        try:
            projects = db.list_projects()
            return {
                "count": len(projects),
                "projects": projects,
            }
        except Exception as e:
            raise HTTPException(500, f"Datenbankfehler: {e}")

    # ──────────────────────────────────────────────────────────────
    # GET /db/export/{sidecar_id} — Sidecar exportieren
    # ──────────────────────────────────────────────────────────────

    @router.get("/export/{sidecar_id}")
    async def export_sidecar(sidecar_id: str):
        """
        Exportiert ein Sidecar-JSON 1:1 aus der Datenbank.
        Das zurückgegebene JSON ist identisch mit dem importierten Original.
        """
        db = _get_db()
        try:
            data = db.export_sidecar(sidecar_id)
        except Exception as e:
            raise HTTPException(500, f"Datenbankfehler: {e}")

        if data is None:
            raise HTTPException(404, f"Sidecar {sidecar_id} nicht gefunden")
        return data

    # ──────────────────────────────────────────────────────────────
    # GET /db/export/current/{project_id} — Aktuelle Version exportieren
    # ──────────────────────────────────────────────────────────────

    @router.get("/export/current/{project_id}")
    async def export_current(project_id: str):
        """
        Exportiert die aktuelle (neueste) Version eines Projekts.
        """
        db = _get_db()
        try:
            data = db.export_current(project_id)
        except Exception as e:
            raise HTTPException(500, f"Datenbankfehler: {e}")

        if data is None:
            raise HTTPException(404, f"Kein aktueller Sidecar für Projekt {project_id}")
        return data

    # ──────────────────────────────────────────────────────────────
    # GET /db/versions/{project_id} — Alle Versionen
    # ──────────────────────────────────────────────────────────────

    @router.get("/versions/{project_id}")
    async def list_versions(project_id: str):
        """
        Listet alle Sidecar-Versionen eines Projekts.
        Zeigt Version, Schema, LOD, Statistiken.
        """
        db = _get_db()
        try:
            versions = db.list_versions(project_id)
            return {
                "project_id": project_id,
                "count": len(versions),
                "versions": versions,
            }
        except Exception as e:
            raise HTTPException(500, f"Datenbankfehler: {e}")

    # ──────────────────────────────────────────────────────────────
    # GET /db/import-log/{project_id} — Import-Protokoll
    # ──────────────────────────────────────────────────────────────

    @router.get("/import-log/{project_id}")
    async def get_import_log(project_id: str):
        """
        Zeigt das Import-Protokoll eines Projekts.
        Enthält Validierungsergebnisse, Fehler und Warnungen.
        """
        db = _get_db()
        try:
            log = db.get_import_log(project_id)
            return {
                "project_id": project_id,
                "count": len(log),
                "entries": log,
            }
        except Exception as e:
            raise HTTPException(500, f"Datenbankfehler: {e}")

    # ──────────────────────────────────────────────────────────────
    # DELETE /db/projects/{project_id} — Projekt löschen
    # ──────────────────────────────────────────────────────────────

    @router.delete("/projects/{project_id}")
    async def delete_project(project_id: str):
        """
        Löscht ein Projekt und alle zugehörigen Sidecars und Import-Logs.
        ACHTUNG: Nicht umkehrbar!
        """
        db = _get_db()
        try:
            deleted = db.delete_project(project_id)
        except Exception as e:
            raise HTTPException(500, f"Datenbankfehler: {e}")

        if not deleted:
            raise HTTPException(404, f"Projekt {project_id} nicht gefunden")
        return {"deleted": True, "project_id": project_id}

    # ──────────────────────────────────────────────────────────────
    # POST /db/init — Schema initialisieren (nur für Entwicklung)
    # ──────────────────────────────────────────────────────────────

    @router.post("/init")
    async def init_database():
        """
        Initialisiert das Datenbank-Schema (CREATE TABLE IF NOT EXISTS).
        Sicher für wiederholte Aufrufe.
        NUR FÜR ENTWICKLUNG — in Produktion via Migration-Scripts.
        """
        db = _get_db()
        try:
            db.init_schema()
            return {"status": "ok", "message": "Schema initialisiert"}
        except Exception as e:
            raise HTTPException(500, f"Schema-Initialisierung fehlgeschlagen: {e}")

    return router
