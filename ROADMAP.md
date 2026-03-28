# DIN 18599 IFC Sidecar - Roadmap 2026

**Version:** 2.1  
**Stand:** 28. März 2026  
**Projekt:** Open Source Standard für energetische Gebäudeakte

---

## 🎯 Vision & Ziele

**Vision:** Software-neutraler Datenstandard für die energetische Gebäudeakte, der Geometrie (IFC), Physik (Sidecar) und Berechnung (Software) entkoppelt.

**Hauptziele 2026:**
1. **Schema v2.1:** Robustes, interoperables Datenformat (Q2)
2. **Viewer-MVP:** Professioneller 3D-Viewer + Energiedaten (Q2)
3. **Community:** Erste externe Contributors, Präsentationen (Q3-Q4)

**Deadline:** **Mai 2026** - MVP-Präsentation in Berlin

---

## ✅ Status Quo (März 2026)

### v2.0.0 - Production Ready (27. März 2026)

**Implementiert:**
- ✅ JSON Schema Draft-07 mit Basis-Validierung
- ✅ 5 Geometrie-Modi (Standalone, Simplified, IFC-Linked, Hierarchical, B-Rep)
- ✅ B-Rep Geometrie-Modell (Vertices + Faces)
- ✅ 3D-Viewer (Three.js, funktionsfähig)
- ✅ Topologische Validierung
- ✅ Delta-Modell für Varianten (Base + Scenarios)
- ✅ Bundesanzeiger-Katalog (97 U-Werte)
- ✅ Dokumentation (8 Dokumente)

**Technologie:**
- JSON Schema Draft-07
- Three.js für 3D-Rendering
- Apache License 2.0
- GitHub: https://github.com/DWEBeratungGmbH/din18599-ifc

---

## 🚨 Kritisches Feedback (Externe Review)

### Schwere: 🔴 Kritisch

1. **Schema-Constraints zu permissiv**
   - `elements[].ifc_guid` nicht required → Geometrie-Verankerung fehlt
   - Kein `uniqueItems` auf Arrays → Duplikate möglich
   - Kein `additionalProperties: false` → Beliebige Felder erlaubt

2. **Delta-Merge-Semantik undefiniert**
   - Keine formale Spezifikation, wie Base + Delta gemergt wird
   - Merge-Key unklar (id? ifc_guid?)
   - Verschiedene Implementierungen werden unterschiedlich mergen

3. **`usage_profile` kein Enum**
   - Freier String statt DIN 18599-10 Enum
   - "17", "017", "Büro", 17 alle schema-konform
   - Maschinelle Interpretation unmöglich

4. **Primärenergiefaktoren fehlen**
   - `output.primary_energy_kwh_a` ohne fp-Angaben
   - Ergebnisse nicht reproduzierbar/auditierbar

### Schwere: 🟠 Hoch

5. **Fenster-Geometrie fehlt**
   - Keine `orientation`, `inclination`, `area`
   - Solarer Eintrag nicht berechenbar

6. **System-Zonen-Zuordnung fehlt**
   - Welches Heizungssystem versorgt welche Zone?

7. **Doku ↔ Schema Inkonsistenz**
   - PARAMETER_MATRIX.md vs. tatsächliches Schema

### Schwere: 🟡 Mittel

8. **Schema-URL nicht erreichbar**
   - `din18599-ifc.de` nicht registriert
   - Kein Online-Schema-Abruf möglich

---

## 📅 Roadmap Q2 2026 (April - Mai)

### **Phase 1: Schema v2.1 - Kritische Fixes** (2 Wochen, 1.-14. April)

**Ziel:** Interoperabilität sicherstellen, kritische Schema-Lücken schließen

#### Woche 1 (1.-7. April): Brainstorm & Konzept

**Brainstorm-Sessions:**
- [ ] **Session 1:** Schema-Constraints Review (2h)
  - Required-Felder definieren (ifc_guid vs. id)
  - uniqueItems-Strategie
  - additionalProperties-Policy

- [ ] **Session 2:** Delta-Merge-Algorithmus (2h)
  - Merge-Semantik formal spezifizieren
  - Merge-Keys pro Array-Typ
  - Konflikt-Auflösung (Base vs. Delta)

- [ ] **Session 3:** Katalog-Architektur (2h)
  - Material-Katalog vs. Construction-Katalog
  - Referenz-Mechanismus (catalog_ref)
  - Override-Semantik

**Deliverables:**
- `docs/SCHEMA_V2.1_CONCEPT.md` - Konzept-Dokument
- `docs/MERGE_ALGORITHM.md` - Formale Merge-Spezifikation

#### Woche 2 (8.-14. April): Schema-Implementierung

**Implementierung:**
- [ ] Schema v2.1 erweitern:
  - `elements[].ifc_guid` als required (oder id)
  - `usage_profile` Enum (DIN 18599-10, alle 30+ Profile)
  - `uniqueItems: true` auf alle ID-Arrays
  - `additionalProperties: false` aktivieren
  - `output.meta.primary_energy_factors` hinzufügen
  - `windows[]` um `orientation`, `area` erweitern
  - `systems[]` um `zone_ids` erweitern

- [ ] Validierung:
  - Alle Demo-Dateien gegen v2.1 validieren
  - Migration-Script (v2.0 → v2.1)
  - Breaking Changes dokumentieren

**Deliverables:**
- `gebaeude.din18599.schema.v2.1.json`
- `MIGRATION_GUIDE_v2.0_to_v2.1.md`
- Aktualisierte Demo-Dateien

---

### **Phase 2: Katalog-System** (2 Wochen, 15.-28. April)

**Ziel:** Material-Katalog, Schichtaufbauten, Nutzungsprofile

#### Woche 3 (15.-21. April): Katalog-Datenmodell

**Brainstorm-Session:**
- [ ] **Session 4:** Katalog-Struktur (2h)
  - Material-Properties (λ, ρ, c, μ)
  - Schichtaufbau-Modell (Layers)
  - Nutzungsprofil-Details (DIN 18599-10)
  - Randbedingungen (Klima, Standort)

**Implementierung:**
- [ ] Schema erweitern:
  - `materials[]` Definition
  - `layer_structures[]` Definition
  - `usage_profiles[]` Definition (detailliert)
  - `climate_location` Objekt

- [ ] Katalog-Daten erstellen:
  - 50+ Materialien (Dämmstoffe, Baustoffe)
  - 20+ Schichtaufbauten (Wände, Dächer, Böden)
  - 30+ Nutzungsprofile (DIN 18599-10)

**Deliverables:**
- `catalog/materials.json`
- `catalog/constructions.json`
- `catalog/usage_profiles.json`
- `docs/CATALOG_GUIDE.md`

#### Woche 4 (22.-28. April): Katalog-Referenzen

**Implementierung:**
- [ ] Referenz-Mechanismus:
  - `elements[].construction_ref` → `layer_structures[].id`
  - `zones[].usage_profile_ref` → `usage_profiles[].id`
  - Override-Logik (catalog vs. custom values)

- [ ] Demo-Projekt:
  - Einfamilienhaus mit Katalog-Referenzen
  - Sanierungsvarianten (WDVS, Fenster, Heizung)

**Deliverables:**
- `viewer/demo-catalog.din18599.json`
- Katalog-Validierung im Schema

---

### **Phase 3: Viewer-MVP** (2 Wochen, 29. April - 12. Mai)

**Ziel:** Professioneller Viewer für Berlin-Präsentation

#### Woche 5 (29. April - 5. Mai): Viewer UI

**Brainstorm-Session:**
- [ ] **Session 5:** Viewer-UX (1h)
  - Layout (3D + Sidebar vs. Split-View)
  - Navigation (Tree-View, Search)
  - Highlighting-Strategie

**Implementierung:**
- [ ] UI-Komponenten:
  - Layout: 3D-Viewer + Sidebar (responsive)
  - Navigation: Tree-View (Zonen → Bauteile → Fenster)
  - Info-Panels: Bauteil-Details, Katalog-Infos
  - Highlighting: Klick → 3D-Highlight + Sidebar-Sync

- [ ] Katalog-Integration:
  - Katalog-Browser in Sidebar
  - Material-Details anzeigen
  - Schichtaufbau visualisieren

**Deliverables:**
- `viewer/index.html` (neuer Viewer mit UI)
- `viewer/styles.css` (Tailwind oder Custom)
- `viewer/app.js` (State Management)

#### Woche 6 (6.-12. Mai): MVP-Finalisierung

**Implementierung:**
- [ ] Features:
  - Statistiken (Gesamt-U-Wert, Fensterflächenanteil)
  - Export (Screenshot, JSON-Download)
  - Performance-Optimierung

- [ ] Testing:
  - Browser-Kompatibilität (Chrome, Firefox, Safari)
  - Mobile-Ansicht (Tablet)
  - Große Modelle (100+ Bauteile)

- [ ] Präsentation:
  - Demo-Slides (Konzept, Format, Viewer)
  - Live-Demo-Script (5 Min Walkthrough)
  - Backup-Video (falls Internet ausfällt)

**Deliverables:**
- Deployment (GitHub Pages: `din18599-ifc.github.io`)
- Präsentations-Paket (Slides + Demo + Doku)
- `docs/QUICKSTART_GUIDE.md`

---

## 📊 Meilensteine & Deadlines

| Datum | Meilenstein | Deliverables | Status |
|-------|-------------|--------------|--------|
| **27. März** | v2.0 Release | B-Rep Geometrie, Basis-Schema | ✅ Fertig |
| **7. April** | Konzept-Phase | Schema v2.1 Konzept, Merge-Algo | 🔄 Geplant |
| **14. April** | Schema v2.1 | Robustes Schema, Migration Guide | 🔄 Geplant |
| **21. April** | Katalog-Daten | Materials, Constructions, Profiles | 🔄 Geplant |
| **28. April** | Katalog-Integration | Demo mit Katalog-Referenzen | 🔄 Geplant |
| **5. Mai** | Viewer-UI | Funktionierender Viewer mit UI | 🔄 Geplant |
| **12. Mai** | MVP-Ready | Präsentations-Paket komplett | 🎯 Deadline |
| **Mai (Berlin)** | **Präsentation** | Live-Demo vor Publikum | 🎤 Event |

---

## 🧠 Brainstorm-Sessions (Übersicht)

| Session | Thema | Dauer | Woche | Ziel |
|---------|-------|-------|-------|------|
| **#1** | Schema-Constraints Review | 2h | 1 | Required-Felder, uniqueItems, additionalProperties |
| **#2** | Delta-Merge-Algorithmus | 2h | 1 | Formale Merge-Semantik spezifizieren |
| **#3** | Katalog-Architektur | 2h | 1 | Material vs. Construction, Referenz-Mechanismus |
| **#4** | Katalog-Struktur | 2h | 3 | Material-Properties, Schichtaufbau, Nutzungsprofile |
| **#5** | Viewer-UX | 1h | 5 | Layout, Navigation, Highlighting |

**Format:** Markdown-Notizen in `docs/brainstorms/YYYYMMDD_session_N.md`

---

## 🔧 Technologie-Stack

### Schema & Validierung
- **Format:** JSON Schema Draft-07
- **Validierung:** ajv (JavaScript), jsonschema (Python)
- **Versionierung:** Semantic Versioning (2.1.0)

### Katalog
- **Format:** JSON-Dateien (statisch)
- **Struktur:** `catalog/*.json`
- **Validierung:** JSON Schema

### Viewer
- **Framework:** React + TypeScript (oder Vanilla JS)
- **3D:** Three.js (bereits implementiert)
- **UI:** Tailwind CSS + shadcn/ui (optional)
- **State:** React Context oder Zustand
- **Deployment:** GitHub Pages

---

## 📋 Schema v2.1 - Änderungen (Priorität)

### 🔴 Kritisch (Must-Have für v2.1)

1. **Required-Felder:**
   - `elements[].ifc_guid` ODER `elements[].id`
   - `windows[].ifc_guid` ODER `windows[].id`
   - `zones[].id`

2. **Enum-Constraints:**
   - `usage_profile` → Enum mit allen DIN 18599-10 Codes
   - `boundary_condition` → Präziseres Enum

3. **Array-Constraints:**
   - `uniqueItems: true` auf alle ID-Arrays
   - `minItems: 1` wo sinnvoll

4. **Objekt-Constraints:**
   - `additionalProperties: false` auf allen Definitionen

5. **Output-Erweiterung:**
   - `output.meta.primary_energy_factors` (fp pro Energieträger)

6. **Fenster-Geometrie:**
   - `windows[].orientation` (0-360°)
   - `windows[].inclination` (0-90°)
   - `windows[].area` (m²)

7. **System-Zuordnung:**
   - `systems[].zone_ids` (Array von Zone-IDs)

### 🟠 Hoch (Should-Have für v2.1)

8. **Katalog-Referenzen:**
   - `elements[].construction_ref`
   - `zones[].usage_profile_ref`

9. **Material-Katalog:**
   - `materials[]` Array mit λ, ρ, c, μ

10. **Schichtaufbauten:**
    - `layer_structures[]` mit Layers

11. **Nutzungsprofile:**
    - `usage_profiles[]` mit DIN 18599-10 Details

12. **Klima-Daten:**
    - `climate_location` Objekt (TRY, Gradtagszahlen)

### 🟡 Mittel (Nice-to-Have)

13. **iSFP-Roadmap:**
    - `scenarios[].priority` (1-3)
    - `scenarios[].timeline` (Jahr)
    - `scenarios[].funding` (BEG-Stufe)

14. **HVAC-Details:**
    - Übergabesystem (Heizkörper, FBH)
    - Vollständige WP-Kennlinie

15. **QNG-Felder:**
    - Nachhaltigkeits-Kennwerte

---

## 📚 Dokumentations-Roadmap

### Neue Dokumente (April-Mai)

1. **`docs/SCHEMA_V2.1_CONCEPT.md`** - Konzept für v2.1
2. **`docs/MERGE_ALGORITHM.md`** - Formale Delta-Merge-Spezifikation
3. **`docs/MIGRATION_GUIDE_v2.0_to_v2.1.md`** - Breaking Changes
4. **`docs/CATALOG_GUIDE.md`** - Katalog-Nutzung
5. **`docs/QUICKSTART_GUIDE.md`** - 5-Minuten-Einstieg
6. **`docs/brainstorms/*.md`** - Session-Notizen

### Aktualisierungen

- `README.md` - v2.1 Features
- `CHANGELOG.md` - v2.1 Release Notes
- `PARAMETER_MATRIX.md` - Schema-Sync
- `FILE_FORMATS.md` - Katalog-Modus

---

## 🎤 Berlin-Präsentation (Mai 2026)

### Agenda (10 Min)

1. **Problem** (2 Min)
   - Proprietäre Formate, Vendor Lock-in
   - Datenverlust bei Software-Wechsel

2. **Lösung** (2 Min)
   - IFC + DIN 18599 Sidecar
   - GUID-basiertes Mapping
   - Open Source, Apache 2.0

3. **Live-Demo** (4 Min)
   - JSON-Datei laden
   - 3D-Modell zeigen (Rotation, Zoom)
   - Auf Wand klicken → Katalog-Infos
   - Sanierungsvariante wechseln
   - Statistiken anzeigen

4. **Ausblick** (1 Min)
   - IFC Import (Q3)
   - Community-Aufbau
   - Konformitätsprüfung

5. **Q&A** (5 Min)

### Demo-Szenario

**Projekt:** Einfamilienhaus (Baujahr 1980, unsaniert)

**Workflow:**
1. Datei laden: `demo-catalog.din18599.json`
2. 3D-Ansicht: Gebäude rotieren, Wände highlighten
3. Bauteil-Info: Außenwand Süd → U=1.2 W/(m²K), ungedämmt
4. Katalog öffnen: WDVS 20cm → U=0.24 W/(m²K)
5. Variante wechseln: "Sanierung WDVS" → Wand wird grün
6. Statistiken: Heizwärmebedarf -45%

**Backup:** Video-Recording (falls Live-Demo fehlschlägt)

---

## 🚀 Roadmap Q3-Q4 2026 (Ausblick)

### Q3 (Juli - September): IFC Integration

- **Phase 4:** IFC Import (web-ifc)
- **Phase 5:** IFC Export (Roundtrip)
- **Phase 6:** Editor-Prototyp (Pascal-inspiriert)

### Q4 (Oktober - Dezember): Community & Ecosystem

- **Phase 7:** API + Python SDK
- **Phase 8:** Website + Tutorials
- **Phase 9:** v3.0 Release

**Meilensteine:**
- **v2.5** (September) - IFC Integration
- **v3.0** (Dezember) - Community Release

---

## ✅ Erfolgs-Kriterien (MVP Mai 2026)

### Schema v2.1
- [ ] Alle 🔴 kritischen Fixes implementiert
- [ ] Migration Guide vorhanden
- [ ] Externe Validierung (min. 1 Reviewer)

### Katalog
- [ ] 50+ Materialien
- [ ] 20+ Schichtaufbauten
- [ ] 30+ Nutzungsprofile (DIN 18599-10)

### Viewer
- [ ] 3D-Rendering funktioniert
- [ ] Katalog-Infos anzeigbar
- [ ] Highlighting (3D ↔ Daten)
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
| **Schema-Version** | v2.1 | v3.0 | v2.0 |
| **Katalog-Einträge** | 100+ | 500+ | 97 |
| **GitHub Stars** | 20+ | 100+ | 5 |
| **Contributors** | 2+ | 10+ | 1 |
| **Dokumentations-Seiten** | 12+ | 20+ | 8 |
| **Externe Reviews** | 1+ | 5+ | 0 |

---

## 🤝 Nächste Schritte (1. April 2026)

### Woche 1 - Tag 1-2
1. **Brainstorm Session #1:** Schema-Constraints Review
2. **Brainstorm Session #2:** Delta-Merge-Algorithmus
3. Konzept-Dokument schreiben

### Woche 1 - Tag 3-5
4. **Brainstorm Session #3:** Katalog-Architektur
5. Schema v2.1 Entwurf erstellen
6. Demo-Dateien gegen v2.1 testen

### Woche 2
7. Schema v2.1 finalisieren
8. Migration Guide schreiben
9. CHANGELOG.md aktualisieren

---

## 📝 Offene Fragen

1. **Domain registrieren?** `din18599-ifc.de` für Schema-Hosting?
2. **Externe Reviewer?** Wer könnte Schema v2.1 reviewen?
3. **Präsentations-Format?** Konferenz? Meetup? Webinar?
4. **Katalog-Quellen?** Welche Datenbanken nutzen? (WECOBIS, ÖKOBAUDAT?)
5. **UI-Framework?** React oder Vanilla JS für Viewer?

---

## ✅ Abschluss

Diese Roadmap ist ein **lebendiges Dokument** und wird nach jeder Phase aktualisiert.

**Feedback willkommen!** → GitHub Issues oder Discussions

**Letzte Aktualisierung:** 28. März 2026  
**Nächste Review:** 14. April 2026 (nach Schema v2.1)
