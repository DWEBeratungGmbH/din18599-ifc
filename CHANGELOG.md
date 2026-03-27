# Changelog

Alle wichtigen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/lang/de/).

---

## [2.0.0] - 2026-03-27

### 🎉 Major Release - Production Ready

**Vollständige Überarbeitung des Schemas und der Dokumentation**

### Added

#### Schema v2.0
- **LOD-Konzept** (Level of Detail 100-500) für verschiedene Planungsphasen
- **Varianten-Management** (Delta-Modell: Base + Scenarios)
- **Layer Structures** (Schichtaufbauten von außen nach innen)
- **Materials erweitert** (STANDARD + AIR_LAYER nach EN ISO 6946)
- **Wärmebrücken-Typen** (DEFAULT, REDUCED, DETAILED)
- **u_value_override** für manuelle U-Wert-Überschreibung
- **construction_catalog_ref** für Katalog-Referenzen
- **data_quality** Metadaten (geometry, envelope, systems)

#### Kataloge
- **Bundesanzeiger 2020** Katalog (97 U-Wert-Referenzen, BEG-konform)
- Katalog-Schema (`$schema: https://din18599-ifc.de/schema/catalog/v1`)
- 10 Baualtersklassen (bis 1918 bis ab 2010)
- Opake Bauteile (Wände, Dächer, Decken, Bodenplatten)
- Transparente Bauteile (Fenster, Türen)

#### Beispiele
- **LOD 100** - Schnellschätzung (Minimal-Input, Katalog-basiert)
- **LOD 200** - iSFP Bestandsaufnahme (Begehung, Bundesanzeiger)
- **LOD 300** - Sanierungsvarianten (Delta-Modell, Schichtaufbauten)
- **LOD 400** - GEG-Nachweis (Vollständig, Produktdatenblätter)

#### Viewer
- **Beispiel-Auswahl** Dropdown (LOD 100-400)
- **Bauteilliste** mit U-Werten und IFC GUIDs
- **Wärmebrücken-Analyse** (Ø ΔU_WB, Typen-Verteilung)
- **Fenster-Liste** (U_g, U_f, g-Wert, Rahmenanteil)

#### Dokumentation
- **ARCHITECTURE.md** - 5-Layer-Architektur, DB-Schema, Deployment
- **IFC_SIDECAR_LINK.md** - GUID-Mapping, Datenfluss, Best Practices
- **LOD_GUIDE.md** - LOD 100-500 Definitionen, Use Cases, Genauigkeit
- **KATALOG_VERWENDUNG.md** - Bundesanzeiger, Custom Catalogs
- **CONTRIBUTING.md** - Contribution Guidelines
- **CHANGELOG.md** - Versionshistorie (diese Datei)

#### Pläne & Konzepte
- **master-implementierung.md** - Master-Plan (LOD + Layer Structures)
- **ifc-viewer-integration-konzept.md** - IFC-Viewer Integration (Option C)
- **schichtaufbau-architektur.md** - Schichtaufbau-Konzept
- **lod-defaults-kataloge.md** - LOD-Konzept + Bundesanzeiger

### Changed

- **Schema-Struktur** - oneOf für Legacy vs. Varianten-Format
- **Materials** - `type` Feld hinzugefügt (STANDARD | AIR_LAYER)
- **Air Layers** - EN ISO 6946 konforme Luftschichten
- **README.md** - Vollständig überarbeitet (v2.0 Features, Quick Start)
- **Lizenz** - Von MIT zu Apache 2.0 (Patent-Klausel)

### Fixed

- **Validator** - Alle Ausgaben auf Deutsch übersetzt
- **API** - Alle Responses auf Deutsch übersetzt
- **Parameter-Matrix** - Feldnamen konsistent (`_kwh_a` Suffix)

### Deprecated

- **Legacy Format** - Einzelne Datei ohne Varianten (weiterhin unterstützt via oneOf)

---

## [1.0.0] - 2024-XX-XX

### Added

- **Initiales JSON Schema** (Draft-07)
- **Parameter-Matrix** (DIN 18599 Teil 1-10)
- **Python Validator** (CLI-Tool)
- **Web Viewer** (HTML/JS, Drag & Drop)
- **FastAPI Service** (REST-API für Validierung)
- **Beispiel-Datei** (musterhaus.din18599.json)
- **README.md** (Projekt-Übersicht)
- **LICENSE** (MIT)

### Schema v1.0

- **meta** - Projekt-Metadaten
- **input** - Eingabedaten (Zonen, Bauteile, Systeme)
- **output** - Ergebnisdaten (Energiebilanz, Kennwerte)
- **climate_location** - Klimadaten (Postleitzahl, TRY-Region)
- **zones** - Thermische Zonen
- **elements** - Opake Bauteile (U-Werte)
- **windows** - Transparente Bauteile
- **materials** - Materialien (λ, ρ, Ökobaudat)
- **systems** - Wärmeerzeuger
- **distribution** - Wärmeverteilung
- **dhw** - Trinkwarmwasser
- **ventilation** - Lüftung
- **lighting** - Beleuchtung
- **automation** - Gebäudeautomation
- **pv** - Photovoltaik

---

## [Unreleased]

### Geplant für v2.1

- **Validator-Erweiterung** (GUID-Checks, Referenz-Checks, LOD-Validierung)
- **Viewer-Erweiterung** (Layer Structures Visualisierung, Materials-Liste, LOD-Badge)
- **Editing MVP** (Inline-Edit U-Werte, Save/Export JSON)

### Geplant für v2.2

- **Schichtaufbau-Editor** (Modal, Drag-to-Reorder, Live U-Wert-Berechnung)
- **API-Erweiterung** (OpenAPI/Swagger, Merge-Endpoint)
- **Docker Compose** (Lokale Entwicklungsumgebung)

### Geplant für v3.0 (Optional)

- **IFC-Viewer Integration** (xeokit, GUID-Highlighting, Click-to-inspect)
- **IFC-Geometrie-Extraktion** (Normalenvektor → Orientierung, Flächen-Berechnung)
- **Multi-User-Editing** (WebSockets, Real-Time Collaboration)

---

## Versionsschema

**Format:** `MAJOR.MINOR.PATCH`

- **MAJOR:** Breaking Changes (Schema-Änderungen, API-Änderungen)
- **MINOR:** Neue Features (abwärtskompatibel)
- **PATCH:** Bugfixes (keine neuen Features)

**Beispiele:**
- `1.0.0` → `2.0.0` - Schema v2.0 (Breaking Changes)
- `2.0.0` → `2.1.0` - Validator-Erweiterung (neue Features)
- `2.1.0` → `2.1.1` - Bugfix (U-Wert-Berechnung korrigiert)

---

## Links

- **Repository:** https://github.com/DWEBeratungGmbH/din18599-ifc
- **Issues:** https://github.com/DWEBeratungGmbH/din18599-ifc/issues
- **Discussions:** https://github.com/DWEBeratungGmbH/din18599-ifc/discussions
- **Releases:** https://github.com/DWEBeratungGmbH/din18599-ifc/releases

---

[2.0.0]: https://github.com/DWEBeratungGmbH/din18599-ifc/releases/tag/v2.0.0
[1.0.0]: https://github.com/DWEBeratungGmbH/din18599-ifc/releases/tag/v1.0.0
[Unreleased]: https://github.com/DWEBeratungGmbH/din18599-ifc/compare/v2.0.0...HEAD
