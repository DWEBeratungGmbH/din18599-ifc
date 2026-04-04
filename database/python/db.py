"""
DIN 18599 Sidecar — Datenbank Import/Export

Stellt Import, Export und Verwaltung von Sidecar-JSONs in PostgreSQL bereit.
Nutzt den Validator um sicherzustellen dass nur geprüfte Daten importiert werden.

Abhängigkeiten:
    pip install psycopg2-binary

Verwendung:
    db = SidecarDB("postgresql://postgres:postgres@localhost:5432/din18599")
    result = db.import_sidecar(data, project_name="Musterhaus")
"""

import json
import hashlib
import time
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None

from .validator import SidecarValidator, ValidationResult, extract_metadata


# ══════════════════════════════════════════════════════════════════════
# Datenstrukturen für Rückgabewerte
# ══════════════════════════════════════════════════════════════════════

@dataclass
class ImportResult:
    """Ergebnis eines Import-Vorgangs"""
    success: bool
    project_id: Optional[str] = None
    sidecar_id: Optional[str] = None
    version: int = 0
    validation: Optional[ValidationResult] = None
    message: str = ""

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "project_id": self.project_id,
            "sidecar_id": self.sidecar_id,
            "version": self.version,
            "validation": self.validation.to_dict() if self.validation else None,
            "message": self.message,
        }


@dataclass
class ProjectInfo:
    """Projekt-Übersicht aus der View"""
    project_id: str
    project_name: str
    description: Optional[str]
    sidecar_id: Optional[str]
    sidecar_version: Optional[int]
    schema_version: Optional[str]
    lod: Optional[str]
    construction_year: Optional[int]
    heated_area: Optional[float]
    wall_count: int
    window_count: int
    zone_count: int
    total_versions: int
    last_import_status: Optional[str]


# ══════════════════════════════════════════════════════════════════════
# Haupt-Klasse: SidecarDB
# ══════════════════════════════════════════════════════════════════════

class SidecarDB:
    """
    Datenbank-Schnittstelle für DIN 18599 Sidecar Import/Export.

    Architektur:
        1. Validator prüft JSON (3 Ebenen)
        2. Bei Erfolg/Warnings: INSERT mit extrahierten Metadaten
        3. Import-Log wird geschrieben (auch bei Fehlschlag)
        4. Export gibt das originale JSON 1:1 zurück
    """

    def __init__(self, connection_string: str):
        """
        Verbindung zur PostgreSQL Datenbank herstellen.

        Args:
            connection_string: z.B. "postgresql://postgres:postgres@localhost:5432/din18599"
        """
        if psycopg2 is None:
            raise ImportError(
                "psycopg2 ist nicht installiert. "
                "Bitte installieren: pip install psycopg2-binary"
            )
        self.conn_string = connection_string
        self.validator = SidecarValidator()

    def _connect(self):
        """Neue Datenbankverbindung erstellen"""
        return psycopg2.connect(self.conn_string)

    # ──────────────────────────────────────────────────────────────
    # IMPORT
    # ──────────────────────────────────────────────────────────────

    def import_sidecar(
        self,
        data: dict,
        project_name: Optional[str] = None,
        project_id: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> ImportResult:
        """
        Importiert ein Sidecar-JSON in die Datenbank.

        Ablauf:
            1. Validierung (3 Ebenen)
            2. Hash berechnen (Duplikat-Check)
            3. Projekt erstellen oder finden
            4. Nächste Version bestimmen
            5. Sidecar einfügen mit extrahierten Metadaten
            6. Import-Log schreiben

        Args:
            data: Das Sidecar-JSON als Dict
            project_name: Projektname (falls neues Projekt, sonst aus meta)
            project_id: Bestehendes Projekt (UUID) — wenn None, neues Projekt
            filename: Quelldatei-Name (für Import-Log)

        Returns:
            ImportResult mit Erfolg/Fehler + Validierungsergebnis
        """
        start = time.time()

        # ── Schritt 1: Validierung ──
        validation = self.validator.validate(data)

        # Bei Fehlern: Abbrechen, aber Import-Log schreiben
        if not validation.valid:
            self._write_import_log(
                project_id=project_id,
                sidecar_id=None,
                filename=filename,
                file_size=len(json.dumps(data)),
                validation=validation,
            )
            return ImportResult(
                success=False,
                validation=validation,
                message=f"Import abgebrochen: {len(validation.errors)} Fehler gefunden",
            )

        # ── Schritt 2: Hash berechnen ──
        data_json = json.dumps(data, sort_keys=True, ensure_ascii=False)
        data_hash = hashlib.sha256(data_json.encode("utf-8")).hexdigest()

        conn = self._connect()
        try:
            with conn.cursor() as cur:
                # ── Schritt 3: Projekt finden oder erstellen ──
                if project_id:
                    # Prüfen ob Projekt existiert
                    cur.execute(
                        "SELECT id FROM din18599.projects WHERE id = %s",
                        (project_id,)
                    )
                    if not cur.fetchone():
                        return ImportResult(
                            success=False,
                            validation=validation,
                            message=f"Projekt {project_id} nicht gefunden",
                        )
                else:
                    # Neues Projekt erstellen
                    name = project_name or data.get("meta", {}).get("project_name", "Unbenanntes Projekt")
                    ifc_ref = data.get("meta", {}).get("ifc_file_ref")
                    cur.execute(
                        """INSERT INTO din18599.projects (name, ifc_file_ref)
                           VALUES (%s, %s) RETURNING id""",
                        (name, ifc_ref)
                    )
                    project_id = str(cur.fetchone()[0])

                # ── Schritt 4: Duplikat-Check ──
                cur.execute(
                    """SELECT id FROM din18599.sidecars
                       WHERE project_id = %s AND data_hash = %s""",
                    (project_id, data_hash)
                )
                duplicate = cur.fetchone()
                if duplicate:
                    conn.rollback()
                    return ImportResult(
                        success=False,
                        project_id=project_id,
                        sidecar_id=str(duplicate[0]),
                        validation=validation,
                        message="Identischer Sidecar existiert bereits (gleicher Hash)",
                    )

                # ── Schritt 5: Nächste Version bestimmen ──
                cur.execute(
                    """SELECT COALESCE(MAX(version), 0) + 1
                       FROM din18599.sidecars WHERE project_id = %s""",
                    (project_id,)
                )
                next_version = cur.fetchone()[0]

                # ── Schritt 6: Metadaten extrahieren und einfügen ──
                meta = extract_metadata(data)

                cur.execute(
                    """INSERT INTO din18599.sidecars (
                        project_id, version, data, data_hash, is_current,
                        schema_version, lod, project_name, ifc_file_ref, ifc_schema,
                        construction_year, heated_area,
                        wall_count, roof_count, floor_count,
                        window_count, door_count, zone_count,
                        room_count, construction_count
                    ) VALUES (
                        %s, %s, %s, %s, true,
                        %s, %s, %s, %s, %s,
                        %s, %s,
                        %s, %s, %s,
                        %s, %s, %s,
                        %s, %s
                    ) RETURNING id""",
                    (
                        project_id, next_version, data_json, data_hash,
                        meta["schema_version"], meta["lod"],
                        meta["project_name"], meta["ifc_file_ref"], meta["ifc_schema"],
                        meta["construction_year"], meta["heated_area"],
                        meta["wall_count"], meta["roof_count"], meta["floor_count"],
                        meta["window_count"], meta["door_count"], meta["zone_count"],
                        meta["room_count"], meta["construction_count"],
                    )
                )
                sidecar_id = str(cur.fetchone()[0])

                # ── Schritt 7: Import-Log schreiben ──
                self._write_import_log(
                    project_id=project_id,
                    sidecar_id=sidecar_id,
                    filename=filename,
                    file_size=len(data_json),
                    validation=validation,
                    cur=cur,
                )

                conn.commit()

                duration_ms = int((time.time() - start) * 1000)
                warning_text = ""
                if validation.warnings:
                    warning_text = f" ({len(validation.warnings)} Warnungen)"

                return ImportResult(
                    success=True,
                    project_id=project_id,
                    sidecar_id=sidecar_id,
                    version=next_version,
                    validation=validation,
                    message=f"Import erfolgreich (Version {next_version}, {duration_ms}ms){warning_text}",
                )

        except Exception as e:
            conn.rollback()
            return ImportResult(
                success=False,
                validation=validation,
                message=f"Datenbankfehler: {e}",
            )
        finally:
            conn.close()

    # ──────────────────────────────────────────────────────────────
    # EXPORT
    # ──────────────────────────────────────────────────────────────

    def export_sidecar(self, sidecar_id: str) -> Optional[dict]:
        """
        Exportiert ein Sidecar-JSON aus der Datenbank.
        Gibt das ORIGINALE JSON 1:1 zurück (verlustfrei).

        Args:
            sidecar_id: UUID des Sidecars

        Returns:
            Das Sidecar-JSON als Dict, oder None wenn nicht gefunden
        """
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT data FROM din18599.sidecars WHERE id = %s",
                    (sidecar_id,)
                )
                row = cur.fetchone()
                if row:
                    return row[0] if isinstance(row[0], dict) else json.loads(row[0])
                return None
        finally:
            conn.close()

    def export_current(self, project_id: str) -> Optional[dict]:
        """
        Exportiert die aktuelle Version eines Projekts.

        Args:
            project_id: UUID des Projekts

        Returns:
            Das Sidecar-JSON als Dict, oder None
        """
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT data FROM din18599.sidecars
                       WHERE project_id = %s AND is_current = true""",
                    (project_id,)
                )
                row = cur.fetchone()
                if row:
                    return row[0] if isinstance(row[0], dict) else json.loads(row[0])
                return None
        finally:
            conn.close()

    def export_to_file(self, sidecar_id: str, filepath: str) -> bool:
        """
        Exportiert Sidecar direkt in eine JSON-Datei.

        Args:
            sidecar_id: UUID des Sidecars
            filepath: Ziel-Pfad für die JSON-Datei

        Returns:
            True wenn erfolgreich, False sonst
        """
        data = self.export_sidecar(sidecar_id)
        if data is None:
            return False
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True

    # ──────────────────────────────────────────────────────────────
    # VERWALTUNG
    # ──────────────────────────────────────────────────────────────

    def list_projects(self) -> list[dict]:
        """
        Listet alle Projekte mit aktuellem Sidecar-Status.
        Nutzt die v_projects_overview View.
        """
        conn = self._connect()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """SELECT * FROM din18599.v_projects_overview
                       ORDER BY project_updated DESC NULLS LAST"""
                )
                return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def list_versions(self, project_id: str) -> list[dict]:
        """Listet alle Versionen eines Projekts"""
        conn = self._connect()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """SELECT id, version, schema_version, lod,
                              is_current, created_at, data_hash,
                              wall_count, window_count, zone_count
                       FROM din18599.sidecars
                       WHERE project_id = %s
                       ORDER BY version DESC""",
                    (project_id,)
                )
                return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    def delete_project(self, project_id: str) -> bool:
        """
        Löscht ein Projekt und alle zugehörigen Sidecars (CASCADE).

        Args:
            project_id: UUID des Projekts

        Returns:
            True wenn gelöscht, False wenn nicht gefunden
        """
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM din18599.projects WHERE id = %s RETURNING id",
                    (project_id,)
                )
                deleted = cur.fetchone() is not None
                conn.commit()
                return deleted
        finally:
            conn.close()

    def get_import_log(self, project_id: str) -> list[dict]:
        """Import-Protokoll eines Projekts abrufen"""
        conn = self._connect()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """SELECT * FROM din18599.import_log
                       WHERE project_id = %s
                       ORDER BY imported_at DESC""",
                    (project_id,)
                )
                return [dict(row) for row in cur.fetchall()]
        finally:
            conn.close()

    # ──────────────────────────────────────────────────────────────
    # HILFSFUNKTIONEN
    # ──────────────────────────────────────────────────────────────

    def _write_import_log(
        self,
        project_id: Optional[str],
        sidecar_id: Optional[str],
        filename: Optional[str],
        file_size: int,
        validation: ValidationResult,
        cur=None,
    ):
        """Schreibt einen Eintrag ins Import-Log"""
        # Eigene Verbindung wenn kein Cursor übergeben
        own_conn = False
        if cur is None:
            conn = self._connect()
            cur = conn.cursor()
            own_conn = True

        try:
            cur.execute(
                """INSERT INTO din18599.import_log (
                    sidecar_id, project_id, filename, file_size_bytes,
                    status, schema_valid, references_valid, plausibility_valid,
                    errors, warnings, validation_duration_ms
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    sidecar_id, project_id, filename, file_size,
                    validation.status,
                    validation.schema_valid,
                    validation.references_valid,
                    validation.plausibility_valid,
                    json.dumps([e.to_dict() for e in validation.errors]),
                    json.dumps([w.to_dict() for w in validation.warnings]),
                    validation.duration_ms,
                )
            )
            if own_conn:
                conn.commit()
        finally:
            if own_conn:
                conn.close()

    def init_schema(self):
        """
        Initialisiert das Datenbank-Schema.
        Führt schema.sql aus. Sicher für wiederholte Aufrufe (IF NOT EXISTS).
        """
        import os
        schema_path = os.path.join(
            os.path.dirname(__file__), "..", "schema.sql"
        )
        with open(schema_path, "r") as f:
            sql = f.read()

        conn = self._connect()
        try:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
            print("✅ Datenbank-Schema initialisiert")
        finally:
            conn.close()
