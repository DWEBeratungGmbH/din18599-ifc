# IFC + DIN 18599 Sidecar

**Ein offenes Austauschformat für die energetische Gebäudeakte in Deutschland**

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-3.1.0-green.svg)](CHANGELOG.md)
[![Schema](https://img.shields.io/badge/Schema-JSON%20Draft--07-orange.svg)](schema/v3.1-complete.json)

> **Status:** v3.1.0 — Gebäudeakte-Release (documents, funding, roadmap, sla_context)
> **Lizenz:** Apache License 2.0
> **Repository:** [github.com/DWEBeratungGmbH/din18599-ifc](https://github.com/DWEBeratungGmbH/din18599-ifc)

---

## 📑 Inhaltsverzeichnis

- [Zielbild](#-zielbild)
- [Features v3.1](#-features-v31)
- [Roadmap 2026](#-roadmap-2026)
- [Quick Start](#-quick-start)
- [Scope & Datenmodell](#-scope--datenmodell)
- [Workflow-Integration](#-workflow-integration)
- [Tools & Ecosystem](#-tools--ecosystem)
- [Dokumentation](#-dokumentation)
- [Beitragen](#-beitragen)
- [Lizenz](#-lizenz)

---

## 🎯 Zielbild

Wir definieren einen **software-neutralen Datenstandard** für die energetische Gebäudeakte.
Ziel ist die Entkopplung von **Geometrie** (BIM/IFC), **physikalischer Beschreibung** (Sidecar) und **Berechnung** (Software).

Ein Energieberatungsprojekt besteht künftig aus mindestens zwei Dateien:

1.  **`gebaeude.ifc`** (Standard IFC4/IFC5)
    *   **Inhalt:** Reine Geometrie, Bauteilstruktur, Raumgeometrie.
    *   **Rolle:** Bleibt "dumm" (keine komplexe Physik, keine Heizungslogik, keine proprietären Psets).
    *   **Kompatibilität:** Lesbar mit jedem BIM-Viewer.

2.  **`gebaeude.din18599.json`** (Sidecar)
    *   **Inhalt:** Zonierung, bauphysikalische Qualitäten, Anlagentechnik, Varianten, iSFP.
    *   **Rolle:** "Veredelt" das IFC-Modell mit der energetischen Intelligenz.
    *   **Referenz:** Verknüpft Eigenschaften via GUID mit den IFC-Objekten.

**Das Ziel:** Ein Architekt exportiert ein IFC, der Energieberater ergänzt es mit dem Sidecar (Zonen, U-Werte, Technik), und jede Fachsoftware kann das Projekt verlustfrei lesen und weiterberechnen.

---

## ✨ Features v3.1

### 🎯 Kern-Features

- ✅ **JSON Schema v3.1** - Vollständig validierbar (Draft-07), abwärtskompatibel bis v2.0
- ✅ **IFC-Verknüpfung** - GUID-basiertes Mapping (IfcBuilding, IfcSpace, IfcWall, IfcWindow)
- ✅ **LOD-Konzept** - Level of Detail 100-500 (BIM-inspiriert)
- ✅ **Varianten-Management** - Delta-Modell (Base + Scenarios)
- ✅ **Schichtaufbauten** - Layer Structures mit U-Wert-Berechnung
- ✅ **Materialien** - Standard + Air Layers (EN ISO 6946)
- ✅ **Wärmebrücken** - ΔU_WB mit Typen (DEFAULT, REDUCED, DETAILED)
- ✅ **Kataloge** - Bundesanzeiger 2020 (97 U-Werte, BEG-konform)

### 🏛️ Gebäudeakte-Sektionen (neu in v3.0/v3.1)

- ✅ **`documents[]`** - Pläne, Nachweise, Fotos, Rechnungen als Cloud-Links (Nextcloud/S3 via Storage-Resolver)
- ✅ **`funding[]`** - Förderungen (BEG, KfW, BAFA) als Hybrid-Modell mit ERPNext-Referenz + Snapshot
- ✅ **`roadmap`** - Sanierungsfahrplan mit priorisierten Schritten (iSFP-kompatibel)
- ✅ **`sla_context`** - Brücke zur SLA-Sandbox (BGF, WE, BT, Szenarien-Mapping)
- ✅ **`input.energy_certificate`** (v3.1) - Energieausweis-Daten (VERBRAUCH/BEDARF) mit Audit-Quelle
- ✅ **`input.targets`** (v3.1) - freie Zielwerte für den "nur IFC vorhanden"-Fall

### � Tools

- ✅ **Python Validator** - CLI-Tool für Schema-Validierung
- ✅ **Web Viewer** - Drag & Drop Visualisierung (HTML/JS)
- ✅ **FastAPI Service** - REST-API für Validierung
- ✅ **4 LOD-Beispiele** - Von Schnellschätzung bis GEG-Nachweis

### 📚 Dokumentation

- ✅ **ARCHITECTURE.md** - 5-Layer-Architektur, DB-Schema, Deployment
- ✅ **IFC_SIDECAR_LINK.md** - GUID-Mapping, Datenfluss, Best Practices
- ✅ **PARAMETER_MATRIX.md** - Alle DIN 18599 Parameter (Teil 1-10)
- ✅ **LOD_GUIDE.md** - LOD-Definitionen, Use Cases, Genauigkeit
- ✅ **KATALOG_VERWENDUNG.md** - Bundesanzeiger, Custom Catalogs

---

## �️ Roadmap 2026

**Aktueller Stand (April 2026):** Schema v3.1 ausgeliefert, FastAPI-Parser produktiv, Viewer-MVP in Arbeit.

👉 **[Vollständige Roadmap ansehen](ROADMAP.md)**

**Highlights:**
- **Q2 2026 (abgeschlossen):** Schema v2.1 → v3.1, Parser-System (IFC + EVEBI), DB v3.0 mit Helper-Funktionen
- **Mai 2026:** MVP-Präsentation in Berlin
- **Q3 2026:** IFC.js-Integration, Editor-Prototyp, weitere Parser
- **Q4 2026:** Community-Aufbau, externe Norm-Review

---

## 🎯 Quick Start

### Option A: Docker Compose (Empfohlen)

**Alles mit einem Befehl starten:**

```bash
git clone https://github.com/DWEBeratungGmbH/din18599-ifc.git
cd din18599-ifc

# Starte PostgreSQL + API + Viewer
docker-compose up -d

# Warte 10 Sekunden (DB-Initialisierung)
sleep 10

# Öffne Viewer
open http://localhost:8080/viewer/index.html
```

**Services:**
- 🗄️ **PostgreSQL:** localhost:5432 (Datenbank)
- 🚀 **API:** http://localhost:8000 (FastAPI)
- 🌐 **Viewer:** http://localhost:8080 (Nginx)

**Stoppen:**
```bash
docker-compose down
```

---

### Option B: Manuell (ohne Docker)

#### 1. Repository klonen

```bash
git clone https://github.com/DWEBeratungGmbH/din18599-ifc.git
cd din18599-ifc
```

#### 2. Datenbank initialisieren (optional)

```bash
# PostgreSQL muss laufen
./database/setup.sh

# Oder mit Drop (Vorsicht!)
./database/setup.sh --drop
```

#### 3. Beispiel validieren

```bash
python3 tools/validate.py examples/lod400_geg_nachweis.din18599.json
# ✅ Validierung erfolgreich
```

#### 4. Viewer öffnen

```bash
# Lokalen Server starten
python3 -m http.server 8000

# Browser öffnen
open http://localhost:8000/viewer/index.html
```

---

### Eigenes Projekt erstellen

```json
{
  "schema_info": {
    "$id": "https://din18599-ifc.de/schema/v3.1/complete",
    "version": "3.1.0"
  },
  "meta": {
    "project_name": "Mein Projekt",
    "ifc_file_ref": "gebaeude.ifc",
    "ifc_guid_building": "2Uj8Lq3Vr9QxPkXr4bN8FD",
    "lod": "200"
  },
  "input": {
    "zones": [...],
    "elements": [...],
    "systems": [...]
  }
}
```

Siehe [LOD_GUIDE.md](docs/LOD_GUIDE.md) für Details zu den LOD-Levels.

---

## �📦 Scope & Datenmodell

Das Datenmodell ist strikt in **Eingabedaten (Input)** und **Ergebnisdaten (Output)** unterteilt. Dies gewährleistet Interoperabilität, ohne die Berechnungshoheit der Fachsoftware anzutasten.

### 1. Eingabedaten (The Definition)
Alle Parameter, die notwendig sind, um eine Norm-Berechnung (z.B. DIN 18599) zu starten. Dies ist der "Source of Truth" für den energetischen Zustand.

*   **Topologie & Zonierung:**
    *   Gruppierung von IFC-Räumen zu **thermischen Zonen** nach DIN 18599-1.
    *   Definition von **Nutzungsprofilen** (DIN 18599-10).
    *   **Nachbarschaften (Adjacencies):** Definition der Randbedingungen für Bauteile (Außenluft, Erdreich, Unbeheizt), entscheidend für Temperatur-Korrekturfaktoren ($F_x$).

*   **Bauphysik (Hülle):**
    *   Ergänzung der IFC-Elemente um energetisch relevante Attribute.
    *   **Hülle:** U-Werte, Schichtaufbauten (optional), Wärmebrückenzuschläge ($\Delta U_{WB}$).
    *   **Material:** Referenzierung auf Ökobilanz-Datenbanken (z.B. Ökobaudat) für QNG/LCA-Nachweise.
    *   **Fenster:** $g_{tot}$-Werte, Rahmenanteile, detaillierte Verschattungsfaktoren.

*   **Anlagentechnik (Systeme):**
    *   Strukturiertes Modell für Erzeuger, Speicher, Verteilung und Übergabe (DIN 18599 Teil 5-9).
    *   **Detailtiefe:** Erfassung von Baujahr, Energieträger, Wirkungsgraden (z.B. COP-Kennlinien), Kältemittel (GWP) und Regelungsstrategien.

### 2. Ergebnisdaten (The Snapshot)
Die resultierenden Bilanzwerte eines Berechnungslaufs. Dies ermöglicht die Nutzung in Drittsystemen (ERP, Förderantrag, Dashboard), ohne dass diese über einen eigenen Rechenkern verfügen müssen.

*   **Bedarf:** Endenergie, Primärenergie, Nutzenergie (aufgeschlüsselt nach Gewerken: Heizung, WW, Kühlung, Licht).
*   **Bewertung:** CO₂-Emissionen, Primärenergiefaktoren, Effizienzklassen (GEG).
*   **Status:** Metadaten zur Berechnung (verwendete Software, Norm-Version, Datum) zur Sicherung der Validität.

### 3. Der Rechenkern (Blackbox)
Der Standard beschreibt **Daten**, keine Algorithmen.
Der Rechenweg selbst (die "Blackbox") bleibt Aufgabe der zertifizierten Software-Kernel. Das Format stellt sicher, dass jede normkonforme Software die gleichen Eingabewerte erhält ("Lossless Roundtrip") und Ergebnisse einheitlich zurückschreibt.

---

## 🔄 Workflow-Integration

Das Format unterstützt den gesamten Lebenszyklus:

1.  **Bestandsaufnahme:** Erfassung des Ist-Zustands (Status Quo).
2.  **Variantenvergleich:** Definition von Sanierungsszenarien (Maßnahmenpakete) als Delta zum Ist-Zustand.
3.  **Sanierungsfahrplan (iSFP):** Zeitliche Einordnung der Maßnahmen in eine Roadmap.
4.  **Monitoring:** Vergleich von berechnetem Bedarf (Output) mit gemessenen Verbräuchen.

## 📁 Repository-Struktur

```
din18599-ifc/
├── schema/                          # JSON Schema (Single Source of Truth)
│   ├── v3.1-complete.json           # Aktuelle Version (v3.1)
│   ├── v3.0-complete.json           # Gebäudeakte-Release
│   ├── v2.3-complete.json           # Flache Struktur (historisch)
│   └── MIGRATION_*.md               # Upgrade-Guides pro Version
├── database/                        # PostgreSQL Schema + Helper-Funktionen
│   └── schema.sql                   # v3.0 mit get_documents/get_funding/...
├── README.md                        # Dieses Dokument
├── LICENSE                          # Apache 2.0
├── CHANGELOG.md                     # Versionshistorie (Keep a Changelog)
│
├── docs/                            # Dokumentation
│   ├── ARCHITECTURE.md              # 5-Layer-Architektur, DB-Schema
│   ├── IFC_SIDECAR_LINK.md          # GUID-Mapping, Datenfluss
│   ├── PARAMETER_MATRIX.md          # Alle DIN 18599 Parameter
│   ├── LOD_GUIDE.md                 # LOD 100-500 Definitionen
│   └── KATALOG_VERWENDUNG.md        # Katalog-Integration
│
├── examples/                        # Beispiel-Dateien (LOD 100-400)
├── catalogs/                        # Bundesanzeiger 2020 Katalog
├── tools/                           # CLI Validator (validate.py)
├── viewer/                          # React/Vite Viewer
└── api/                             # FastAPI Parser-System
    ├── main.py                      # Endpunkte: /process, /health
    ├── parsers/                     # IFC + EVEBI Parser
    └── generators/                  # Sidecar-Generator
```

### Projekt-Dateistruktur (Anwendung)

```
projekt_musterstrasse1/
├── gebaeude.ifc                  # Geometrie (IFC4, Standard)
├── gebaeude.din18599.json        # DIN 18599 Sidecar (Input & Output)
└── assets/
    ├── fotos/
    └── dokumente/
```

## 🧰 Tools & Ecosystem

Wir stellen offene Referenz-Implementierungen bereit, um die Integration zu erleichtern:

### 1. Python Validator (`tools/validate.py`)
Ein Command-Line Tool zur Validierung von JSON-Dateien gegen das Schema.

```bash
python3 tools/validate.py examples/musterhaus.din18599.json
# ✅ Validation successful
```

### 2. Web Viewer (`viewer/index.html`)
Ein HTML5/JS Viewer zur Visualisierung der Sidecar-Dateien.

**Features:**
*   **Drag & Drop** Interface
*   **Beispiel-Auswahl** (LOD 100-400)
*   **Dashboard** mit Energiebilanz, Zonen und Anlagentechnik
*   **Bauteilliste** mit U-Werten und Flächen
*   **Wärmebrücken-Analyse** (Ø ΔU_WB, Typen)
*   Läuft komplett lokal im Browser (kein Upload)

**Starten:**
```bash
python3 -m http.server 8000
open http://localhost:8000/viewer/index.html
```

### 3. Validation API (`api/`)
Ein Docker-ready Microservice (FastAPI), der Validierung als Service anbietet.

```bash
# Starten
docker build -t din18599-api .
docker run -p 8000:8000 din18599-api

# Nutzen
curl -X POST -F "file=@examples/musterhaus.din18599.json" http://localhost:8000/validate
```

---

## 📚 Dokumentation

### Kern-Dokumentation

| Dokument | Beschreibung |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | 5-Layer-Architektur, DB-Schema, Deployment-Optionen |
| [IFC_SIDECAR_LINK.md](docs/IFC_SIDECAR_LINK.md) | GUID-Mapping, Datenfluss, Best Practices |
| [PARAMETER_MATRIX.md](docs/PARAMETER_MATRIX.md) | Alle DIN 18599 Parameter (Teil 1-10) |
| [LOD_GUIDE.md](docs/LOD_GUIDE.md) | LOD 100-500 Definitionen, Use Cases |
| [KATALOG_VERWENDUNG.md](docs/KATALOG_VERWENDUNG.md) | Bundesanzeiger, Custom Catalogs |
| [CATALOG_STRATEGY.md](docs/CATALOG_STRATEGY.md) | Strategie Hersteller-/Produktkataloge (ÖKOBAUDAT, EPREL, bSDD) |
| [IFC_REQUIREMENTS.md](docs/IFC_REQUIREMENTS.md) | IFC-Mindestanforderungs-Spec + buildingSMART-Andockpunkte |

### Technische Dokumentation

| Dokument | Beschreibung |
|----------|-------------|
| [schema/v3.1-complete.json](schema/v3.1-complete.json) | JSON Schema v3.1 (Draft-07) — Single Source of Truth |
| [schema/MIGRATION_v3.0_to_v3.1.md](schema/MIGRATION_v3.0_to_v3.1.md) | Migration v3.0 → v3.1 |
| [schema/MIGRATION_v2.3_to_v3.0.md](schema/MIGRATION_v2.3_to_v3.0.md) | Migration v2.3 → v3.0 (Gebäudeakte) |
| [database/schema.sql](database/schema.sql) | PostgreSQL Schema v3.0 + Helper-Funktionen |
| [CHANGELOG.md](CHANGELOG.md) | Versionshistorie |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution Guidelines + Schema-First-Workflow |

### Pläne & Konzepte

| Dokument | Beschreibung |
|----------|-------------|
| [.plans/master-implementierung.md](.plans/master-implementierung.md) | Master-Plan (LOD + Layer Structures) |
| [.plans/ifc-viewer-integration-konzept.md](.plans/ifc-viewer-integration-konzept.md) | IFC-Viewer Integration (Option C - Hybrid) |
| [.plans/schichtaufbau-architektur.md](.plans/schichtaufbau-architektur.md) | Schichtaufbau-Konzept |
| [.plans/lod-defaults-kataloge.md](.plans/lod-defaults-kataloge.md) | LOD-Konzept + Bundesanzeiger |

---

## 🤝 Beitragen

Dieses Projekt lebt von der Community! Wir freuen uns über jeden Beitrag.

Siehe [CONTRIBUTING.md](CONTRIBUTING.md) für Details.

### Wie kann ich beitragen?

**1. Feedback & Diskussion**
- Öffne ein [Issue](https://github.com/DWEBeratungGmbH/din18599-ifc/issues) für Verbesserungsvorschläge
- Diskutiere im [Discussions-Bereich](https://github.com/DWEBeratungGmbH/din18599-ifc/discussions) über Konzepte
- Teile Praxiserfahrungen und Anwendungsfälle

**2. Dokumentation verbessern**
- Verbesserungen an README, Parameter-Matrix oder Schema
- Beispiele aus der Praxis ergänzen
- Übersetzungen in andere Sprachen

**3. Code & Tools**
- Validator, Viewer oder API verbessern
- Neue Tools entwickeln (z.B. IFC→Sidecar Converter)
- Test-Cases und Beispieldateien erstellen

### Qualitätsstandards

**Schema-Änderungen:**
- Abwärtskompatibilität beachten (keine Breaking Changes ohne Major Version)
- Änderungen in `PARAMETER_MATRIX.md` dokumentieren
- Beispiel-JSON (`examples/`) aktualisieren
- Tests anpassen und ausführen

**Code-Beiträge:**
- Python: PEP 8 Style Guide
- JavaScript: ESLint + Prettier
- Kommentare auf Deutsch (Code auf Englisch)
- Tests für neue Features

**Pull Request Workflow:**
1. Fork des Repositories erstellen
2. Feature-Branch erstellen (`feature/mein-feature`)
3. Änderungen committen mit aussagekräftigen Messages
4. Tests lokal ausführen
5. Pull Request gegen `main` öffnen
6. Review abwarten und ggf. Anpassungen vornehmen

### Kontakt & Support

- **Issues:** [GitHub Issues](https://github.com/DWEBeratungGmbH/din18599-ifc/issues)
- **Diskussionen:** [GitHub Discussions](https://github.com/DWEBeratungGmbH/din18599-ifc/discussions)
- **E-Mail:** opensource@dwe-beratung.de

---

## 📄 Lizenz

**Apache License, Version 2.0** - Offener Standard für maximale Interoperabilität.

Diese Lizenz erlaubt kommerzielle und nicht-kommerzielle Nutzung, Modifikation und Weiterverbreitung, unter der Bedingung, dass Copyright-Hinweise und Lizenztext beibehalten werden. Die Apache 2.0 Lizenz beinhaltet zudem eine ausdrückliche Patent-Klausel, die Rechtssicherheit für Implementierer schafft.

Siehe [LICENSE](LICENSE) für Details.
