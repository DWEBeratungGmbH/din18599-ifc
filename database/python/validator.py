"""
DIN 18599 Sidecar Validator — 3-Ebenen-Validierung

Validiert Sidecar-JSON-Dateien BEVOR sie in die Datenbank importiert werden.

Ebene 1: Schema-Validierung (Struktur, Typen, Enums)
Ebene 2: Referenz-Integrität (construction_ref, zone_ref, parent_wall_guid)
Ebene 3: Fachliche Plausibilität (U-Wert-Bereiche, Flächen, DIN 18599)

Ergebnis:
    ValidationResult mit errors[] und warnings[]
    - Errors → Import wird blockiert
    - Warnings → Import geht durch, User wird informiert
"""

import json
import time
from dataclasses import dataclass, field
from typing import Any
from pathlib import Path


# ══════════════════════════════════════════════════════════════════════
# Datenstrukturen
# ══════════════════════════════════════════════════════════════════════

@dataclass
class ValidationMessage:
    """Einzelne Validierungsmeldung mit Kontext"""
    # Ebene: "schema", "reference", "plausibility"
    level: str
    # Schwere: "error" oder "warning"
    severity: str
    # Betroffener Pfad im JSON (z.B. "input.envelope.walls[3].u_value")
    path: str
    # Meldung auf Deutsch
    message: str
    # Optionaler Vorschlag zur Behebung
    suggestion: str = ""

    def to_dict(self) -> dict:
        """Serialisierung für JSONB-Speicherung im Import-Log"""
        result = {
            "level": self.level,
            "severity": self.severity,
            "path": self.path,
            "message": self.message,
        }
        if self.suggestion:
            result["suggestion"] = self.suggestion
        return result


@dataclass
class ValidationResult:
    """Gesamtergebnis der Validierung"""
    # Ist das JSON grundsätzlich importierbar?
    valid: bool = True
    # Ebenen-Status
    schema_valid: bool = True
    references_valid: bool = True
    plausibility_valid: bool = True
    # Alle Meldungen
    errors: list[ValidationMessage] = field(default_factory=list)
    warnings: list[ValidationMessage] = field(default_factory=list)
    # Performance
    duration_ms: int = 0

    def add_error(self, level: str, path: str, message: str, suggestion: str = ""):
        """Fehler hinzufügen — blockiert den Import"""
        self.valid = False
        self.errors.append(ValidationMessage(
            level=level, severity="error", path=path,
            message=message, suggestion=suggestion
        ))
        # Ebene markieren
        if level == "schema":
            self.schema_valid = False
        elif level == "reference":
            self.references_valid = False
        elif level == "plausibility":
            self.plausibility_valid = False

    def add_warning(self, level: str, path: str, message: str, suggestion: str = ""):
        """Warnung hinzufügen — Import geht trotzdem durch"""
        self.warnings.append(ValidationMessage(
            level=level, severity="warning", path=path,
            message=message, suggestion=suggestion
        ))

    @property
    def status(self) -> str:
        """Import-Status für die Datenbank"""
        if not self.valid:
            return "FAILED"
        if self.warnings:
            return "WARNINGS"
        return "SUCCESS"

    def to_dict(self) -> dict:
        return {
            "valid": self.valid,
            "status": self.status,
            "schema_valid": self.schema_valid,
            "references_valid": self.references_valid,
            "plausibility_valid": self.plausibility_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "duration_ms": self.duration_ms,
        }

    def print_summary(self):
        """Zusammenfassung auf der Konsole ausgeben"""
        status_icon = {"SUCCESS": "✅", "WARNINGS": "⚠️", "FAILED": "❌"}
        print(f"\n{'═' * 60}")
        print(f"  Validierung: {status_icon.get(self.status, '?')} {self.status}")
        print(f"  Dauer: {self.duration_ms} ms")
        print(f"{'═' * 60}")

        if self.errors:
            print(f"\n  ❌ {len(self.errors)} Fehler:")
            for e in self.errors:
                print(f"     [{e.level}] {e.path}: {e.message}")
                if e.suggestion:
                    print(f"              → {e.suggestion}")

        if self.warnings:
            print(f"\n  ⚠️  {len(self.warnings)} Warnungen:")
            for w in self.warnings:
                print(f"     [{w.level}] {w.path}: {w.message}")
                if w.suggestion:
                    print(f"              → {w.suggestion}")

        if not self.errors and not self.warnings:
            print(f"\n  Keine Probleme gefunden.")
        print()


# ══════════════════════════════════════════════════════════════════════
# Haupt-Validator
# ══════════════════════════════════════════════════════════════════════

class SidecarValidator:
    """
    3-Ebenen-Validator für DIN 18599 Sidecar JSON.

    Verwendung:
        validator = SidecarValidator()
        result = validator.validate(sidecar_data)
        if result.valid:
            # Importieren...
        else:
            result.print_summary()
    """

    def validate(self, data: dict) -> ValidationResult:
        """
        Führt alle 3 Validierungsebenen sequenziell aus.
        Ebene 2+3 werden nur ausgeführt wenn Ebene 1 besteht.
        """
        result = ValidationResult()
        start = time.time()

        # Ebene 1: Schema-Validierung (Struktur)
        self._validate_schema(data, result)

        # Ebene 2+3 nur wenn Grundstruktur stimmt
        if result.schema_valid:
            # Ebene 2: Referenz-Integrität
            self._validate_references(data, result)
            # Ebene 3: Fachliche Plausibilität
            self._validate_plausibility(data, result)

        result.duration_ms = int((time.time() - start) * 1000)
        return result

    def validate_file(self, filepath: str) -> ValidationResult:
        """Validiert eine JSON-Datei vom Dateisystem"""
        result = ValidationResult()
        start = time.time()

        path = Path(filepath)
        if not path.exists():
            result.add_error("schema", "file", f"Datei nicht gefunden: {filepath}")
            result.duration_ms = int((time.time() - start) * 1000)
            return result

        if not path.suffix == ".json":
            result.add_error("schema", "file", "Datei muss .json Extension haben")
            result.duration_ms = int((time.time() - start) * 1000)
            return result

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            result.add_error("schema", "file", f"Ungültiges JSON: {e}")
            result.duration_ms = int((time.time() - start) * 1000)
            return result

        return self.validate(data)

    # ──────────────────────────────────────────────────────────────
    # EBENE 1: Schema-Validierung
    # Prüft: Required-Felder, Typen, Enums, Grundstruktur
    # ──────────────────────────────────────────────────────────────

    def _validate_schema(self, data: dict, result: ValidationResult):
        """Ebene 1: Strukturelle Validierung"""

        # 1.1 Top-Level-Pflichtfelder
        if not isinstance(data, dict):
            result.add_error("schema", "root", "Sidecar muss ein JSON-Objekt sein")
            return

        # schema_info ist optional, aber wenn vorhanden muss version drin sein
        if "schema_info" in data:
            schema_info = data["schema_info"]
            if isinstance(schema_info, dict) and "version" not in schema_info:
                result.add_warning("schema", "schema_info.version",
                    "Schema-Version fehlt",
                    "Empfohlen: schema_info.version = '2.3.0'")

        # meta ist empfohlen
        if "meta" not in data:
            result.add_warning("schema", "meta",
                "meta-Block fehlt",
                "Empfohlen: meta mit project_name und created")
        else:
            meta = data["meta"]
            if isinstance(meta, dict):
                if "project_name" not in meta:
                    result.add_warning("schema", "meta.project_name",
                        "Projektname fehlt")

        # input ist PFLICHT
        if "input" not in data:
            result.add_error("schema", "input",
                "input-Block fehlt — Sidecar hat keine Eingabedaten",
                "Mindestens input.building muss vorhanden sein")
            return

        inp = data["input"]
        if not isinstance(inp, dict):
            result.add_error("schema", "input", "input muss ein Objekt sein")
            return

        # 1.2 building-Block
        if "building" not in inp:
            result.add_warning("schema", "input.building",
                "building-Block fehlt",
                "Empfohlen für LOD >= 200")
        else:
            self._validate_building(inp["building"], result)

        # 1.3 envelope (Gebäudehülle)
        if "envelope" in inp:
            self._validate_envelope(inp["envelope"], result)

        # 1.4 zones (Thermische Zonen)
        building = inp.get("building", {})
        zones = building.get("zones", [])
        if not zones:
            result.add_warning("schema", "input.building.zones",
                "Keine thermischen Zonen definiert",
                "Für DIN 18599 Berechnung mindestens eine Zone nötig")

        # 1.5 constructions
        if "constructions" in inp:
            self._validate_constructions(inp["constructions"], result)

    def _validate_building(self, building: Any, result: ValidationResult):
        """Validiert den building-Block"""
        if not isinstance(building, dict):
            result.add_error("schema", "input.building", "building muss ein Objekt sein")
            return

        # Geschosse prüfen
        storeys = building.get("storeys", [])
        if not isinstance(storeys, list):
            result.add_error("schema", "input.building.storeys",
                "storeys muss ein Array sein")

        # Zonen prüfen
        zones = building.get("zones", [])
        if isinstance(zones, list):
            for i, zone in enumerate(zones):
                if not isinstance(zone, dict):
                    continue
                if "id" not in zone:
                    result.add_error("schema", f"input.building.zones[{i}].id",
                        "Zone hat keine ID")
                if "area" not in zone and "area" not in zone:
                    result.add_warning("schema", f"input.building.zones[{i}].area",
                        "Zone hat keine Fläche",
                        "Fläche wird für DIN 18599 Berechnung benötigt")

        # Räume prüfen
        rooms = building.get("rooms", [])
        if isinstance(rooms, list):
            for i, room in enumerate(rooms):
                if not isinstance(room, dict):
                    continue
                if "id" not in room:
                    result.add_error("schema", f"input.building.rooms[{i}].id",
                        "Raum hat keine ID")

    def _validate_envelope(self, envelope: Any, result: ValidationResult):
        """Validiert die Gebäudehülle"""
        if not isinstance(envelope, dict):
            result.add_error("schema", "input.envelope", "envelope muss ein Objekt sein")
            return

        # Jede Bauteil-Kategorie prüfen
        for category in ["walls", "roofs", "floors", "windows", "doors"]:
            elements = envelope.get(category, [])
            if not isinstance(elements, list):
                result.add_error("schema", f"input.envelope.{category}",
                    f"{category} muss ein Array sein")
                continue
            for i, elem in enumerate(elements):
                self._validate_element(elem, f"input.envelope.{category}[{i}]", result)

    def _validate_element(self, elem: Any, path: str, result: ValidationResult):
        """Validiert ein einzelnes Bauteil (opak oder transparent)"""
        if not isinstance(elem, dict):
            result.add_error("schema", path, "Bauteil muss ein Objekt sein")
            return

        # ID ist Pflicht
        if "id" not in elem:
            result.add_error("schema", f"{path}.id", "Bauteil hat keine ID")

        # Fläche ist Pflicht
        if "area" not in elem:
            result.add_error("schema", f"{path}.area", "Bauteil hat keine Fläche")
        elif not isinstance(elem["area"], (int, float)):
            result.add_error("schema", f"{path}.area",
                f"Fläche muss eine Zahl sein, ist aber {type(elem['area']).__name__}")

    def _validate_constructions(self, constructions: Any, result: ValidationResult):
        """Validiert Konstruktionen/Schichtaufbauten"""
        if not isinstance(constructions, list):
            result.add_error("schema", "input.constructions",
                "constructions muss ein Array sein")
            return

        for i, constr in enumerate(constructions):
            if not isinstance(constr, dict):
                continue
            if "id" not in constr:
                result.add_error("schema", f"input.constructions[{i}].id",
                    "Konstruktion hat keine ID")

    # ──────────────────────────────────────────────────────────────
    # EBENE 2: Referenz-Integrität
    # Prüft: Interne Verweise (construction_ref → constructions, etc.)
    # ──────────────────────────────────────────────────────────────

    def _validate_references(self, data: dict, result: ValidationResult):
        """Ebene 2: Prüft ob alle internen Referenzen auflösbar sind"""
        inp = data.get("input", {})

        # Verfügbare IDs sammeln
        construction_ids = self._collect_ids(inp.get("constructions", []))
        window_constr_ids = self._collect_ids(inp.get("window_constructions", []))

        building = inp.get("building", {})
        zone_ids = self._collect_ids(building.get("zones", []))
        room_ids = self._collect_ids(building.get("rooms", []))
        storey_ids = self._collect_ids(building.get("storeys", []))

        # Alle Hüllen-Element-IDs sammeln (für parent_wall_guid)
        envelope = inp.get("envelope", {})
        all_element_ids = set()
        all_element_guids = set()
        for category in ["walls", "roofs", "floors"]:
            for elem in envelope.get(category, []):
                if "id" in elem:
                    all_element_ids.add(elem["id"])
                if "ifc_guid" in elem:
                    all_element_guids.add(elem["ifc_guid"])

        # Referenzen in Bauteilen prüfen
        for category in ["walls", "roofs", "floors", "windows", "doors"]:
            for i, elem in enumerate(envelope.get(category, [])):
                path = f"input.envelope.{category}[{i}]"
                self._check_element_refs(
                    elem, path, result,
                    construction_ids, window_constr_ids,
                    zone_ids, room_ids, storey_ids,
                    all_element_ids, all_element_guids
                )

        # Referenzen in Räumen prüfen (zone_ref, storey_ref)
        for i, room in enumerate(building.get("rooms", [])):
            path = f"input.building.rooms[{i}]"
            zone_ref = room.get("zone_ref")
            if zone_ref and zone_ref not in zone_ids:
                result.add_error("reference", f"{path}.zone_ref",
                    f"Zone '{zone_ref}' existiert nicht",
                    f"Verfügbare Zonen: {', '.join(sorted(zone_ids)[:5])}")

            storey_ref = room.get("storey_ref")
            if storey_ref and storey_ref not in storey_ids:
                result.add_warning("reference", f"{path}.storey_ref",
                    f"Geschoss '{storey_ref}' existiert nicht in storeys[]")

    def _check_element_refs(
        self, elem: dict, path: str, result: ValidationResult,
        construction_ids: set, window_constr_ids: set,
        zone_ids: set, room_ids: set, storey_ids: set,
        all_element_ids: set, all_element_guids: set
    ):
        """Prüft alle Referenzen eines Bauteils"""

        # construction_ref → constructions[]
        constr_ref = elem.get("construction_ref")
        if constr_ref:
            if constr_ref not in construction_ids and constr_ref not in window_constr_ids:
                result.add_warning("reference", f"{path}.construction_ref",
                    f"Konstruktion '{constr_ref}' nicht gefunden",
                    "Konstruktion existiert möglicherweise in EVEBI aber nicht im Sidecar")

        # zone_ref → zones[]
        zone_ref = elem.get("zone_ref")
        if zone_ref and zone_ref not in zone_ids:
            result.add_warning("reference", f"{path}.zone_ref",
                f"Zone '{zone_ref}' existiert nicht")

        # room_ref → rooms[]
        room_ref = elem.get("room_ref")
        if room_ref and room_ref not in room_ids:
            result.add_warning("reference", f"{path}.room_ref",
                f"Raum '{room_ref}' existiert nicht")

        # parent_wall_guid → walls/roofs/floors (für Fenster/Türen)
        parent_guid = elem.get("parent_wall_guid")
        if parent_guid:
            if parent_guid not in all_element_ids and parent_guid not in all_element_guids:
                result.add_warning("reference", f"{path}.parent_wall_guid",
                    f"Eltern-Element '{parent_guid}' nicht gefunden",
                    "Fenster/Tür kann keiner Wand zugeordnet werden")

    def _collect_ids(self, items: list) -> set:
        """Sammelt alle IDs aus einer Liste von Objekten"""
        ids = set()
        for item in items:
            if isinstance(item, dict):
                if "id" in item:
                    ids.add(item["id"])
                # Auch GUID als alternative ID akzeptieren
                if "ifc_guid" in item:
                    ids.add(item["ifc_guid"])
        return ids

    # ──────────────────────────────────────────────────────────────
    # EBENE 3: Fachliche Plausibilität
    # Prüft: DIN 18599 Regeln, physikalische Grenzen, Konsistenz
    # ──────────────────────────────────────────────────────────────

    def _validate_plausibility(self, data: dict, result: ValidationResult):
        """Ebene 3: Fachliche Plausibilitätsprüfung"""
        inp = data.get("input", {})
        envelope = inp.get("envelope", {})

        # 3.1 U-Wert-Bereiche prüfen
        self._check_u_values(envelope, result)

        # 3.2 Flächen-Konsistenz prüfen
        self._check_areas(envelope, result)

        # 3.3 Orientierung prüfen
        self._check_orientations(envelope, result)

        # 3.4 Zonen-Konsistenz
        building = inp.get("building", {})
        self._check_zones(building, result)

        # 3.5 Fenster-Wand-Verhältnis
        self._check_window_wall_ratio(envelope, result)

    def _check_u_values(self, envelope: dict, result: ValidationResult):
        """
        Prüft ob U-Werte in physikalisch sinnvollen Bereichen liegen.
        DIN 18599: U-Werte typisch 0.1 - 5.0 W/(m²K)
        """
        # Grenzwerte pro Bauteil-Typ
        u_limits = {
            "walls":   {"min": 0.05, "max": 5.0, "name": "Wand"},
            "roofs":   {"min": 0.05, "max": 4.0, "name": "Dach"},
            "floors":  {"min": 0.05, "max": 4.0, "name": "Boden"},
            "windows": {"min": 0.5,  "max": 6.0, "name": "Fenster"},
            "doors":   {"min": 0.5,  "max": 6.0, "name": "Tür"},
        }

        for category, limits in u_limits.items():
            for i, elem in enumerate(envelope.get(category, [])):
                u_value = elem.get("u_value")
                if u_value is None:
                    # U-Wert fehlt — Warnung
                    result.add_warning("plausibility",
                        f"input.envelope.{category}[{i}].u_value",
                        f"{limits['name']} '{elem.get('name', 'unbenannt')}' hat keinen U-Wert",
                        "U-Wert wird für DIN 18599 Berechnung benötigt")
                    continue

                if not isinstance(u_value, (int, float)):
                    continue

                if u_value == 0.0:
                    result.add_warning("plausibility",
                        f"input.envelope.{category}[{i}].u_value",
                        f"{limits['name']} '{elem.get('name', 'unbenannt')}' hat U-Wert = 0.0",
                        "Vermutlich nicht erfasst — Katalog-Lookup empfohlen")
                elif u_value < limits["min"]:
                    result.add_warning("plausibility",
                        f"input.envelope.{category}[{i}].u_value",
                        f"{limits['name']} U-Wert {u_value} ist ungewöhnlich niedrig (< {limits['min']})",
                        "Bitte prüfen — könnte ein Eingabefehler sein")
                elif u_value > limits["max"]:
                    result.add_warning("plausibility",
                        f"input.envelope.{category}[{i}].u_value",
                        f"{limits['name']} U-Wert {u_value} ist ungewöhnlich hoch (> {limits['max']})",
                        "Bitte prüfen — liegt außerhalb des typischen Bereichs")

    def _check_areas(self, envelope: dict, result: ValidationResult):
        """Prüft ob Flächen plausibel sind"""
        for category in ["walls", "roofs", "floors", "windows", "doors"]:
            for i, elem in enumerate(envelope.get(category, [])):
                area = elem.get("area")
                if area is None:
                    continue
                if not isinstance(area, (int, float)):
                    continue

                if area <= 0:
                    result.add_error("plausibility",
                        f"input.envelope.{category}[{i}].area",
                        f"Fläche {area} m² ist ungültig (muss > 0 sein)")
                elif area > 1000:
                    result.add_warning("plausibility",
                        f"input.envelope.{category}[{i}].area",
                        f"Fläche {area} m² ist ungewöhnlich groß",
                        "Bitte prüfen — typische Einzelbauteil-Fläche < 200 m²")

    def _check_orientations(self, envelope: dict, result: ValidationResult):
        """Prüft ob Orientierungen gültig sind (0-360°)"""
        for category in ["walls", "windows", "doors"]:
            for i, elem in enumerate(envelope.get(category, [])):
                orientation = elem.get("orientation")
                if orientation is None:
                    # Orientierung fehlt — nur Warnung bei Wänden
                    if category == "walls":
                        result.add_warning("plausibility",
                            f"input.envelope.{category}[{i}].orientation",
                            f"Wand '{elem.get('name', 'unbenannt')}' hat keine Orientierung",
                            "Orientierung wird für solare Gewinne benötigt")
                    continue

                if not isinstance(orientation, (int, float)):
                    continue

                if orientation < 0 or orientation > 360:
                    result.add_error("plausibility",
                        f"input.envelope.{category}[{i}].orientation",
                        f"Orientierung {orientation}° liegt außerhalb 0-360°")

    def _check_zones(self, building: dict, result: ValidationResult):
        """Prüft Zonen-Konsistenz"""
        zones = building.get("zones", [])
        rooms = building.get("rooms", [])

        # Warnung wenn Räume existieren aber keine Zone referenzieren
        rooms_without_zone = [r for r in rooms
                              if isinstance(r, dict) and not r.get("zone_ref")]
        if rooms_without_zone and zones:
            result.add_warning("plausibility",
                "input.building.rooms",
                f"{len(rooms_without_zone)} von {len(rooms)} Räumen haben keine Zone zugewiesen",
                "zone_ref sollte auf eine thermische Zone verweisen")

        # Zonen ohne Fläche prüfen
        for i, zone in enumerate(zones):
            if not isinstance(zone, dict):
                continue
            area = zone.get("area")
            if area is not None and isinstance(area, (int, float)) and area == 0:
                result.add_warning("plausibility",
                    f"input.building.zones[{i}].area",
                    f"Zone '{zone.get('name', 'unbenannt')}' hat Fläche = 0 m²")

    def _check_window_wall_ratio(self, envelope: dict, result: ValidationResult):
        """
        Prüft ob Fenster-Flächen kleiner als zugehörige Wand-Flächen sind.
        Sammelt alle Fenster pro parent_wall_guid und vergleicht mit Wand-Fläche.
        """
        # Wand-Flächen sammeln
        wall_areas: dict[str, float] = {}
        for wall in envelope.get("walls", []):
            wid = wall.get("ifc_guid") or wall.get("id")
            if wid and isinstance(wall.get("area"), (int, float)):
                wall_areas[wid] = wall["area"]

        # Fenster-Flächen pro Wand summieren
        window_areas_per_wall: dict[str, float] = {}
        for win in envelope.get("windows", []):
            parent = win.get("parent_wall_guid")
            if parent and isinstance(win.get("area"), (int, float)):
                window_areas_per_wall[parent] = (
                    window_areas_per_wall.get(parent, 0) + win["area"]
                )

        # Vergleich
        for wall_id, window_area in window_areas_per_wall.items():
            wall_area = wall_areas.get(wall_id)
            if wall_area and window_area > wall_area:
                result.add_warning("plausibility",
                    f"input.envelope.windows (parent: {wall_id})",
                    f"Fenster-Fläche ({window_area:.1f} m²) > Wand-Fläche ({wall_area:.1f} m²)",
                    "Summe der Fenster-Flächen sollte kleiner als die Wand-Fläche sein")


# ══════════════════════════════════════════════════════════════════════
# Extraktions-Hilfsfunktionen
# Werden beim Import verwendet um die extrahierten Spalten zu befüllen
# ══════════════════════════════════════════════════════════════════════

def extract_metadata(data: dict) -> dict:
    """
    Extrahiert Metadaten aus dem Sidecar-JSON für die extrahierten DB-Spalten.
    Wird beim Import aufgerufen.
    """
    inp = data.get("input", {})
    meta = data.get("meta", {})
    schema_info = data.get("schema_info", {})
    building = inp.get("building", {})
    envelope = inp.get("envelope", {})

    return {
        "schema_version": schema_info.get("version"),
        "lod": meta.get("lod"),
        "project_name": meta.get("project_name"),
        "ifc_file_ref": meta.get("ifc_file_ref"),
        "ifc_schema": meta.get("ifc_schema"),
        "construction_year": building.get("construction_year"),
        "heated_area": building.get("heated_area"),
        # Statistiken
        "wall_count": len(envelope.get("walls", [])),
        "roof_count": len(envelope.get("roofs", [])),
        "floor_count": len(envelope.get("floors", [])),
        "window_count": len(envelope.get("windows", [])),
        "door_count": len(envelope.get("doors", [])),
        "zone_count": len(building.get("zones", [])),
        "room_count": len(building.get("rooms", [])),
        "construction_count": len(inp.get("constructions", [])),
    }


# ══════════════════════════════════════════════════════════════════════
# CLI: Direkt ausführbar für schnelle Tests
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Verwendung: python validator.py <sidecar.json>")
        print("Beispiel:   python validator.py output_roundtrip_FINAL_v11.json")
        sys.exit(1)

    filepath = sys.argv[1]
    validator = SidecarValidator()
    result = validator.validate_file(filepath)
    result.print_summary()
    sys.exit(0 if result.valid else 1)
