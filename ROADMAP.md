# DIN 18599 IFC Sidecar - Roadmap 2026

**Stand:** 13. April 2026
**Schema-Version:** v3.1 (ausgeliefert), v3.2 in Planung
**Projekt:** Open Source Standard für energetische Gebäudeakte

---

## 🎯 Vision & Ziele

**Vision:** Software-neutraler Datenstandard für die energetische Gebäudeakte, der Geometrie (IFC), Physik (Sidecar) und Berechnung (Software) entkoppelt.

**Hauptziele 2026:**
1. ✅ **Schema v2.1 → v3.1:** Norm-konforme Datenstruktur + Gebäudeakte-Sektionen (Q2) — **ABGESCHLOSSEN**
2. ✅ **Parser-System:** IFC + EVEBI → Sidecar Generator (Q2) — **ABGESCHLOSSEN**
3. 🔄 **Viewer-MVP:** Professioneller 3D-Viewer + Upload/Download (Q2) — **IN ARBEIT**
4. 📅 **Community:** Erste externe Contributors, Berlin-Präsentation (Q2–Q4)

> **Der Block "Status Quo (1. April 2026)" weiter unten ist ein historischer Snapshot** —
> er dokumentiert den Zustand vom 1.4., als das Parser-System fertig war. Für den
> aktuellen Stand siehe diesen Abschnitt und den [CHANGELOG](CHANGELOG.md).

### 🟢 Seit dem 1. April erreicht

- **Schema v2.2, v2.3, v3.0, v3.1** ausgeliefert — siehe [CHANGELOG.md](CHANGELOG.md)
- **v3.0 Gebäudeakte-Release:** neue Sektionen `documents`, `funding`, `roadmap`, `sla_context`
- **v3.1 Additiv:** `input.energy_certificate`, `input.targets`
- **database/schema.sql v3.0:** 3 neue Statistik-Spalten, 4 Helper-Funktionen (get_documents, get_funding, get_roadmap_steps, sum_approved_funding)
- **E2E-Roundtrip-Test** (lossless) produktiv — Parser → Generator → Validator
- **Cross-Repo-Integration DWEapp:** `schema:generate` + `schema:check` Scripts in [/opt/weclapp-manager](../weclapp-manager) lesen v3.0-complete.json als Single Source of Truth
- **Contributing-Workflow:** Schema-First-Workflow formalisiert (8 Schritte, siehe [CONTRIBUTING.md](CONTRIBUTING.md))

---

## ✅ Status Quo (1. April 2026)

### 🎉 **DURCHBRUCH: IFC + EVEBI Parser-System implementiert!**

**Heute erreicht (1. April 2026):**

#### ✅ **Backend: Parser-System (Python + FastAPI)**
- **EVEBI Parser** (`api/parsers/evebi_parser.py`) - 350+ Zeilen
  - Parst `.evea` ZIP-Archive (EVEBI Projekt-Dateien)
  - Extrahiert `projekt.xml` aus ZIP
  - Liest U-Werte, Konstruktionen, Materialien, Bauteile
  - Vollständige Dataclasses (EVEBIData, EVEBIElement, EVEBIConstruction)

- **IFC Parser** (`api/parsers/ifc_parser.py`) - 280+ Zeilen
  - Parst IFC-Dateien mit `ifcopenshell`
  - Extrahiert Geometrie (Wände, Dächer, Böden, Fenster)
  - Berechnet Flächen, Orientierung, Neigung
  - IFC-GUID + PosNo (Tag) Extraktion

- **Mapping Engine** (`api/parsers/mapper.py`) - 200+ Zeilen
  - 3 Mapping-Strategien:
    1. **PosNo-basiert** (höchste Priorität, 100% Confidence)
    2. **Name-basiert** (Fallback, Similarity-Score)
    3. **Geometrie-basiert** (Fläche + Orientierung + Neigung)
  - Confidence Scoring (0.0 - 1.0)
  - Unmatched Elements Tracking

- **Sidecar Generator** (`api/parsers/sidecar_generator.py`) - 150+ Zeilen
  - Generiert DIN18599 Sidecar JSON v2.1
  - Kombiniert IFC-Geometrie + EVEBI-Daten
  - Vollständige Metadaten (Mapping Stats, Timestamps)
  - Konstruktions-Details (Schichten, λ-Werte)

- **FastAPI Endpoints** (`api/main.py`)
  - `POST /process` - Upload IFC + EVEBI → Sidecar JSON
  - CORS für Viewer (localhost:3002)
  - Error Handling + Validation
  - Temporäre Datei-Verarbeitung

**Code-Statistik:**
- **~1000 Zeilen Python** (Production-Ready)
- **4 Parser-Module** (EVEBI, IFC, Mapper, Generator)
- **Vollständige Type Hints** (Dataclasses)

#### ✅ **Frontend: Upload UI + Download (React + TypeScript)**
- **Upload Komponente** (`viewer/src/components/FileUpload.tsx`) - 200+ Zeilen
  - Drag & Drop für IFC + EVEBI `.evea`
  - File Validation (.ifc, .evea Extensions)
  - Progress Indicator (Loading State)
  - Success/Error Messages
  - Mapping Statistics Anzeige

- **App Integration** (`viewer/src/App.tsx`)
  - Upload Modal (Overlay)
  - Download Button (JSON Export)
  - "Neue Dateien" Button
  - State Management (showUpload)

**Features:**
- ✅ IFC + EVEBI Upload
- ✅ Automatische Verarbeitung (Backend)
- ✅ Sidecar JSON Download
- ✅ Mapping Statistics
- ✅ Error Handling

#### ✅ **Dokumentation**
- `.plans/evea-format-breakthrough.md` - EVEBI Format-Analyse
- `.plans/use-case-final-correct.md` - Korrigierter Use-Case
- `.plans/workflow-final-revised.md` - Workflow-Dokumentation

---

## 🚀 **WORKFLOW: Upload → Process → Download**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. User öffnet Viewer (localhost:3002)                     │
│    - Klickt "Neue Dateien"                                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Upload IFC + EVEBI .evea                                 │
│    - File Validation                                        │
│    - FormData Upload zu Backend                            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Backend Processing (FastAPI)                            │
│    ├─→ IFC Parser: Geometrie extrahieren                   │
│    ├─→ EVEBI Parser: U-Werte, Konstruktionen extrahieren   │
│    ├─→ Mapping Engine: IFC ↔ EVEBI verknüpfen             │
│    └─→ Sidecar Generator: JSON generieren                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Viewer Display                                           │
│    - 3D-Modell (aus IFC)                                    │
│    - Energetische Daten (aus EVEBI)                         │
│    - Mapping Statistics                                     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Download                                                 │
│    - Sidecar JSON (DIN18599 v2.1)                          │
│    - IFC-Datei (optional)                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 📅 Roadmap Q2 2026 (April - Mai)

### ✅ **Phase 1: Schema v2.1** (1.-7. April) - **ABGESCHLOSSEN**

**Erreicht:**
- [x] Schema v2.1 Final implementiert
- [x] TypeScript Types (410 Zeilen)
- [x] Demo-JSON (360 Zeilen)
- [x] Dokumentation (3 Dokumente)

### 🚀 **Phase 2: Parser-System** (1. April) - **ABGESCHLOSSEN**

**Erreicht:**
- [x] EVEBI Parser (ZIP + XML)
- [x] IFC Parser (ifcopenshell)
- [x] Mapping Engine (3 Strategien)
- [x] Sidecar Generator
- [x] FastAPI Endpoints
- [x] Upload UI + Download

**Deliverables:**
- ✅ `api/parsers/` - Vollständiges Parser-System
- ✅ `viewer/src/components/FileUpload.tsx` - Upload UI
- ✅ `api/main.py` - FastAPI Backend

### ✅ **Phase 3: Setup & Testing** (2.-7. April) — **ABGESCHLOSSEN**

**Erreicht:**
- [x] Python Environment + ifcopenshell installiert
- [x] FastAPI Backend läuft, CORS für DWEapp-Dev (Port 3000) konfiguriert
- [x] End-to-End Roundtrip-Test: lossless verifiziert (Commit 4510760)
- [x] `api/README.md`, `docs/QUICKSTART.md` vorhanden

**Noch offen (nachgelagert zur Doku-Aufräum-Session, siehe unten):**
- [ ] `docs/API.md` — OpenAPI/Swagger-Export

### 📅 **Phase 4: Viewer-Verbesserungen** (8.-14. April)

**Aufgaben:**
- [ ] **3D-Viewer Integration** (3h)
  - IFC-Datei im Viewer anzeigen
  - IFC.js Integration
  - Bauteil-Highlighting

- [ ] **Daten-Anzeige** (2h)
  - Bauteil-Details (U-Werte, Konstruktionen)
  - Mapping-Confidence anzeigen
  - Unmatched Elements Liste

- [ ] **UI-Verbesserungen** (2h)
  - Responsive Design
  - Loading States
  - Error Messages

**Deliverables:**
- Funktionierender 3D-Viewer
- Vollständige Daten-Anzeige
- Professionelle UI

---

## 📊 Meilensteine & Deadlines

| Datum | Meilenstein | Deliverables | Status |
|-------|-------------|--------------|--------|
| **1. April** | Parser-System | EVEBI, IFC, Mapper, Generator | ✅ **FERTIG** |
| **1. April** | Upload UI | FileUpload Komponente | ✅ **FERTIG** |
| **7. April** | Setup & Testing | Python venv, E2E Tests, Doku | 🔄 In Arbeit |
| **14. April** | Viewer-MVP | 3D-Viewer + Daten-Anzeige | 📅 Geplant |
| **21. April** | Katalog-Integration | Material-Katalog im Viewer | 📅 Geplant |
| **28. April** | Polishing | Performance, UX, Testing | 📅 Geplant |
| **12. Mai** | **MVP-Ready** | Präsentations-Paket komplett | 🎯 Deadline |

---

## 🔧 Technologie-Stack

### Backend (Parser-System)
- **Python 3.12** - Programmiersprache
- **FastAPI** - Web Framework
- **ifcopenshell 0.7.0** - IFC Parser
- **zipfile** - EVEBI .evea Entpackung
- **xml.etree.ElementTree** - XML Parsing
- **Dataclasses** - Type Safety

### Frontend (Viewer)
- **React 18** - UI Framework
- **TypeScript** - Type Safety
- **Vite** - Build Tool
- **Three.js** - 3D-Rendering
- **Lucide React** - Icons

### Deployment
- **Docker** - Containerization (optional)
- **GitHub Pages** - Viewer Hosting
- **Vercel/Netlify** - Backend Hosting (optional)

---

## 📋 Offene Punkte (Priorität)

> Stand 13.4.: Die Punkte 1–3 aus dem 1.4.-Stand (Python-Setup, ifcopenshell, E2E-Testing) sind abgeschlossen. Die Liste unten ist entsprechend bereinigt.

### 🟠 Hoch (Should-Have)

4. **Dokumentation (API-Layer)**
   - API-Dokumentation (OpenAPI/Swagger-Export aus FastAPI)
   - Siehe auch "Dokumentations-Konsistenz (offen)" am Ende dieser Roadmap

5. **Error Handling**
   - Bessere Fehlermeldungen
   - Logging (Python logging)
   - Retry-Mechanismus

6. **Performance**
   - Große IFC-Dateien (>100 MB)
   - Streaming für große EVEBI-Archive
   - Caching

### 🟡 Mittel (Nice-to-Have)

7. **IFC.js Integration**
   - IFC-Datei im Viewer anzeigen
   - 3D-Highlighting
   - Bauteil-Selektion

8. **Mapping-Verbesserungen**
   - Machine Learning für Geometrie-Matching
   - Manuelle Korrektur-UI
   - Confidence-Threshold konfigurierbar

### 🟣 Strategie (Pitch-Vorbereitung 06.05.2026)

9. **Katalog-Anbindung — 3-Säulen-Strategie**
   Siehe [docs/CATALOG_STRATEGY.md](docs/CATALOG_STRATEGY.md)
   - ÖKOBAUDAT (LCA), EPREL (TGA), bSDD (Klassifikation)
   - Schema-Erweiterung v3.2: Identifier-Felder (`oekobaudat_uuid`, `eprel_id`, `bsdd_guid`)
   - Offene Flanke benannt: keine offene EU-DB für Bauhülle bis CPR/DPP

10. **IFC-Mindestanforderungs-Spec als IDS**
    Siehe [docs/IFC_REQUIREMENTS.md](docs/IFC_REQUIREMENTS.md)
    - Q2 2026: IDS 1.0 Draft `schema/ids/din18599-base.ids`
    - Q3 2026: bSDD-Domäne registrieren, IDS-Template-Antrag bei bSI
    - Q4 2026: Pset-Antrag (`Pset_ThermalBridge`, `Pset_ShadingDeviceWindow`) für IFC4.3 ADD3
    - Andockpunkt DE: Fachgruppe Nachhaltigkeit (Neustart 20.10.2025, Treffen 10.11.2025 Fulda)

11. **Export-Funktionen**
   - IFC-Export (mit Sidecar-Daten)
   - Excel-Export (Bauteil-Liste)
   - PDF-Report

---

## 📚 Dokumentations-Roadmap

### ✅ Abgeschlossen
- ✅ `.plans/evea-format-breakthrough.md` - EVEBI Format-Analyse
- ✅ `.plans/use-case-final-correct.md` - Use-Case Definition
- ✅ `.plans/workflow-final-revised.md` - Workflow-Dokumentation

### 🔄 In Arbeit
- [ ] `api/README.md` - Parser-System Dokumentation
- [ ] `docs/API.md` - API-Dokumentation (OpenAPI)
- [ ] `docs/QUICKSTART.md` - Setup-Guide

### 📅 Geplant
- [ ] `docs/MAPPING_STRATEGIES.md` - Mapping-Algorithmen
- [ ] `docs/EVEBI_FORMAT.md` - EVEBI Format-Spezifikation
- [ ] `docs/TROUBLESHOOTING.md` - Häufige Probleme

---

## 🎤 Berlin-Präsentation (Mai 2026)

### Demo-Szenario (10 Min)

**Projekt:** Einfamilienhaus (Real-World Beispiel)

**Workflow:**
1. **Upload** (1 Min)
   - IFC-Datei hochladen (aus Cascados)
   - EVEBI .evea hochladen (aus EVEBI)
   - "Sidecar generieren" klicken

2. **Processing** (30 Sek)
   - Backend parst beide Dateien
   - Mapping via PosNo (100% Match)
   - Sidecar JSON wird generiert

3. **Viewer** (3 Min)
   - 3D-Modell anzeigen
   - Auf Wand klicken → U-Wert anzeigen
   - Konstruktion anzeigen (Schichten, λ-Werte)
   - Mapping Statistics

4. **Download** (30 Sek)
   - Sidecar JSON downloaden
   - In anderer Software öffnen (z.B. Excel)

5. **Ausblick** (2 Min)
   - Open Source, Apache 2.0
   - Community-Aufbau
   - Weitere Parser (Hottgenroth, Dämmwerk)

6. **Q&A** (3 Min)

**Backup:** Video-Recording (falls Live-Demo fehlschlägt)

---

## 🚀 Roadmap Q3-Q4 2026 (Ausblick)

### Q3 (Juli - September): Weitere Parser

- **Hottgenroth Parser** - EnEV/GEG Software
- **Dämmwerk Parser** - U-Wert Berechnung
- **ArchiPHYSIK Parser** - Passivhaus-Software
- **IFC Export** - Roundtrip (Sidecar → IFC)

### Q4 (Oktober - Dezember): Community & Ecosystem

- **API + Python SDK** - Programmatischer Zugriff
- **Website + Tutorials** - din18599-ifc.de
- **v3.0 Release** - Community Release
- **Externe Reviews** - Norm-Konformität

**Meilensteine:**
- **v2.5** (September) - Weitere Parser
- **v3.0** (Dezember) - Community Release

---

## ✅ Erfolgs-Kriterien (MVP Mai 2026)

### Parser-System
- [x] EVEBI Parser funktioniert
- [x] IFC Parser funktioniert
- [x] Mapping Engine funktioniert
- [x] Sidecar Generator funktioniert
- [ ] End-to-End Tests bestanden
- [ ] Dokumentation vollständig

### Viewer
- [x] Upload UI funktioniert
- [x] Download funktioniert
- [ ] 3D-Viewer zeigt IFC an
- [ ] Daten-Anzeige funktioniert
- [ ] Browser-kompatibel (Chrome, Firefox, Safari)

### Präsentation
- [ ] Demo-Projekt fertig
- [ ] Slides fertig
- [ ] Live-Demo getestet (3x Probe)
- [ ] Backup-Video vorhanden

---

## 📊 KPIs für 2026

| Metrik | Ziel Q2 | Ziel Q4 | Aktuell |
|--------|---------|---------|---------|
| **Parser-Module** | 2+ | 5+ | 2 (EVEBI, IFC) |
| **Code-Zeilen (Python)** | 1000+ | 3000+ | ~1000 |
| **Mapping-Accuracy** | 80%+ | 95%+ | TBD |
| **GitHub Stars** | 20+ | 100+ | 5 |
| **Contributors** | 2+ | 10+ | 1 |
| **Dokumentations-Seiten** | 15+ | 25+ | 12 |

---

## 🤝 Nächste Schritte (2.-7. April)

### 🔄 Aktuell (Priorität)

1. **Python Environment Setup** (1h)
   ```bash
   sudo apt install python3.12-venv
   cd /opt/din18599-ifc/api
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Backend Server starten** (15min)
   ```bash
   cd /opt/din18599-ifc/api
   source venv/bin/activate
   uvicorn main:app --reload --port 8000
   ```

3. **End-to-End Test** (2h)
   - Upload `DIN18599TestIFCv2.ifc`
   - Upload `DIN18599Test_260401.evea`
   - Sidecar JSON validieren
   - Mapping-Qualität prüfen

4. **Dokumentation schreiben** (2h)
   - `api/README.md` erstellen
   - `docs/API.md` erstellen
   - `docs/QUICKSTART.md` erstellen

### 📅 Nächste Woche (8.-14. April)

5. 3D-Viewer Integration (IFC.js)
6. Daten-Anzeige verbessern
7. UI-Polishing
8. Performance-Optimierung

---

## 📝 Offene Fragen

1. **ifcopenshell Installation:** Docker Container verwenden?
2. **Hosting:** Wo Backend hosten? (Vercel, Railway, Render?)
3. **Domain:** `din18599-ifc.de` registrieren?
4. **Weitere Parser:** Welche Software als nächstes? (Hottgenroth, Dämmwerk?)
5. **Community:** Wie erste Contributors gewinnen?

---

## 📝 Dokumentations-Konsistenz (offen)

> Notiert am 13. April 2026 nach der v3.0/v3.1-Aufräum-Session.
> README.md, CLAUDE.md und diese Roadmap wurden bereits aktualisiert —
> die folgenden Punkte stehen noch aus.

### 🟠 Mittel (eigene Session, ca. 45 min)

- [ ] **docs/ARCHITECTURE.md** — 5-Layer-Architektur um die v3.0-Sektionen (documents, funding, roadmap, sla_context) erweitern; DB-Helper-Funktionen erwähnen
- [ ] **docs/QUICKSTART.md** — Setup-Guide auf v3.1 heben (Schema-Pfad, Beispiel-JSON)
- [ ] **docs/PARAMETER_MATRIX.md** — Auf v3.1-Stand prüfen; die v3.1-Neufelder (energy_certificate, targets) ergänzen falls relevant
- [ ] **CONTRIBUTING.md** — Schritt 2 verweist auf `schema/v3.x-complete.json` und `PARAMETER_MATRIX.md`; letzteren Verweis prüfen, ob er noch aktuell ist

### 🟡 Niedrig (nur bei Bedarf)

- [ ] **CHANGELOG-Rückfüllung v2.1–v2.3** — aktuell nur Hinweis auf Git-History; optional nachtragen für vollständige Keep-a-Changelog-Form
- [ ] **"Historisch"-Header für v2.1-Guides** — `docs/SIDECAR_SCHEMA_v2.1.md`, `docs/SCHEMA_V2.1_CONCEPT.md`, `docs/SCHEMA_V2.1_GUIDE.md`, `docs/SOLID_LIBRARY_v2.md`, `docs/MIGRATION_GUIDE_v2.0_to_v2.1.md` — jeweils einen Warnblock am Dateianfang hinzufügen, damit Leser erkennen dass es sich um versionsspezifische Guides handelt
- [ ] **Ungewisse Dateien prüfen** — `docs/LOD_GUIDE.md`, `docs/IFC_SIDECAR_LINK.md`, `docs/FILE_FORMATS.md` wurden im Drift-Scan nicht gefunden; stichprobenartig lesen ob sie trotzdem outdated sind

### 🟢 Nachgelagert

- [ ] **Datenbank-Migrationsskript** — `database/migrations/v2.3_to_v3.0.sql` erstellen (ALTER TABLE für die 3 neuen Statistik-Spalten + CREATE FUNCTION für die Helper), damit bestehende Produktiv-DBs sauber migriert werden können. Das pure schema.sql ist nur für frische Deployments autoritativ.
- [ ] **LFS-Evaluation** — sobald `sources/IFC_EVBI/` oder andere Binärordner insgesamt >500 MB überschreiten, Umstellung auf Git LFS erwägen (bislang alle Test-Fixtures direkt im Git, was bei den aktuellen Größen OK ist).

---

## ✅ Abschluss

Diese Roadmap ist ein **lebendiges Dokument** und wird nach jeder Phase aktualisiert.

**Feedback willkommen!** → GitHub Issues oder Discussions

**Letzte Aktualisierung:** 13. April 2026 (v3.1 ausgeliefert, Cross-Repo DWEapp integriert, Doku-Refresh für README/CLAUDE/ROADMAP)
**Nächste Review:** nach der Doku-Konsistenz-Session (siehe oben)
