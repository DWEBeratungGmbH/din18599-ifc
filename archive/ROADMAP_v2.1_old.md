# DIN 18599 IFC Sidecar - Roadmap 2026

**Version:** 2.3  
**Stand:** 1. April 2026  
**Projekt:** Open Source Standard für energetische Gebäudeakte

---

## 🎯 Vision & Ziele

**Vision:** Software-neutraler Datenstandard für die energetische Gebäudeakte, der Geometrie (IFC), Physik (Sidecar) und Berechnung (Software) entkoppelt.

**Hauptziele 2026:**
1. **Schema v2.1:** Norm-konforme, robuste Datenstruktur (Q2) ✅ **ABGESCHLOSSEN**
2. **Viewer-MVP:** Professioneller 3D-Viewer + Energiedaten (Q2) 🔄 **IN ARBEIT**
3. **Community:** Erste externe Contributors, Präsentationen (Q3-Q4)

**Deadline:** **Mai 2026** - MVP-Präsentation in Berlin

---

## ✅ Status Quo (1. April 2026)

### 🎉 **DURCHBRUCH: Schema v2.1 Final - Vollständig implementiert!**

**Heute erreicht (1. April 2026):**
- ✅ **Schema v2.1 komplett implementiert**
  - Parent-Child Beziehungen (parent_element_id, parent_element_type)
  - Solargewinne (solar_absorption, shading_factor_fs)
  - Wärmebrücken-Typ (DEFAULT | REDUCED | DETAILED)
  - B' für Fx-Faktor (perimeter, characteristic_dimension_b)
  - BuildingElement Add-On für LOD 300+ (Treppen, Gauben, Anbauten)
  - Maßnahmen mit Kosten & Förderung
  - Szenario-Output mit Einsparungen

- ✅ **TypeScript Types vollständig** (410 Zeilen)
  - Alle Interfaces für v2.1
  - BuildingElement als Add-On
  - Vollständige Type-Safety

- ✅ **Demo-JSON erweitert** (360 Zeilen)
  - Alle v2.1 Felder mit realistischen Werten
  - BuildingElement: Kellertreppe als Beispiel
  - Szenario mit vollständigem Output
  - Kosten: 26.000 € | Förderung: 5.200 € | Einsparung: 1.600 €/a

- ✅ **Dokumentation**
  - Schema v2.1 Final Specification (300+ Zeilen)
  - Brainstorm-Dokument (379 Zeilen)
  - Verbesserungen-Dokument (258 Zeilen)

- ✅ **Git Commit + Push**
  - Commit: feat: DIN 18599 Schema v2.1
  - 15 Dateien, 2847+ Zeilen Code
  - GitHub: https://github.com/DWEBeratungGmbH/din18599-ifc

### Status vor v2.1 (29. März 2026)

### 🎉 **DURCHBRUCH: DIN 18599 Registries komplett!**

**Heute erreicht (29. März 2026):**
- ✅ **DIN 18599 Registries auf 100%**
  - 222 Begriffe (Glossar komplett)
  - 562 Symbole (alle Formelzeichen)
  - 735 Indizes (alle Indizes)
  - 45 Nutzungsprofile (Wohn + Nichtwohn)
  - **= 1564 Einträge total**

- ✅ **Katalog-System komplett**
  - 52 Materialien (λ, ρ, c, μ nach DIN 4108-4)
  - 24 Schichtaufbauten (U-Werte 0.14-5.8 W/(m²K))
  - 45 Nutzungsprofile (Enum-validiert)

- ✅ **Schema v2.1 Extensions**
  - Katalog-Referenzen (usage_profile_ref, construction_ref, material_ref)
  - Override-Mechanismus
  - Migration Guide v2.0 → v2.1

- ✅ **Demo-Projekt**
  - Einfamilienhaus mit 2 Sanierungsszenarien
  - Katalog-Referenzen demonstriert
  - Energiebilanzen (Bestand: 203.7 kWh/a → Stufe 2: 65.3 kWh/a, -68%)

- ✅ **Dokumentation**
  - CATALOG_GUIDE.md (409 Zeilen)
  - Brainstorm: Sidecar-Struktur an DIN 18599 anlehnen

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

## 🎯 **ENTSCHEIDUNGEN: Schema v2.1 Neustrukturierung (29. März 2026)**

### **Brainstorm-Ergebnisse:**

**1. Envelope-Struktur: Hybrid (Opak/Transparent + Bauteilspezifisch)**
- ✅ Trennung opak/transparent (DIN 18599-2 konform)
- ✅ Bauteilspezifische Parameter (walls, roofs, floors, windows)
- ✅ Flexibel für Wohn- und Nichtwohngebäude

**2. Systems-Struktur: Detailliert (Erzeugung/Verteilung/Übergabe/Regelung)**
- ✅ DIN 18599-5 Systematik 1:1 abbilden
- ✅ Aufwandszahlen berechenbar (e_g, e_d, e_ce)
- ✅ Optimierungspotenziale erkennbar

**3. Breaking Changes: Maximal**
- ✅ Komplette Neustrukturierung für v2.1
- ✅ Migration-Script v2.0 → v2.1
- ✅ Jetzt oder nie - langfristige Vorteile

**4. Priorität: Norm-Konformität + Usability**
- ✅ Nah an der Norm bleiben (Zertifizierung, Validierung)
- ✅ Usability durch Katalog-System (einfache Nutzung)

### **Neue Schema v2.1 Struktur:**

```json
{
  "input": {
    "building": {
      "zones": [...],
      "climate": {...}
    },
    "envelope": {
      "opaque_elements": {
        "walls_external": [...],
        "walls_internal": [...],
        "roofs": [...],
        "floors_ground": [...],
        "floors_basement_ceiling": [...]
      },
      "transparent_elements": {
        "windows": [...],
        "doors": [...]
      },
      "thermal_bridges": {...}
    },
    "systems": {
      "heating": {
        "generation": {...},
        "distribution": {...},
        "emission": {...},
        "control": {...}
      },
      "ventilation": {...},
      "cooling": {...},
      "lighting": {...},
      "dhw": {...}
    },
    "electricity": {...},
    "automation": {...}
  }
}
```

---

## 📅 Roadmap Q2 2026 (April - Mai) - AKTUALISIERT

### **Phase 1: Schema v2.1 - Norm-konforme Neustrukturierung** (2 Wochen, 1.-14. April)

**Ziel:** Maximale Norm-Konformität bei guter Usability

#### ✅ Woche 1 (1. April): Schema v2.1 - ABGESCHLOSSEN

**Erreicht:**
- [x] **Schema v2.1 Final** - Vollständig implementiert (1.04. ✅)
  - Parent-Child Beziehungen (parent_element_id, parent_element_type)
  - Solargewinne (solar_absorption, shading_factor_fs)
  - Wärmebrücken-Typ (thermal_bridge_type)
  - B' für Fx-Faktor (perimeter, characteristic_dimension_b)
  - BuildingElement Add-On für LOD 300+
  - Maßnahmen mit Kosten & Förderung
  - Szenario-Output mit Einsparungen

- [x] **TypeScript Types** - 410 Zeilen (1.04. ✅)
  - Vollständiges Type-System
  - Alle v2.1 Interfaces
  - BuildingElement als Add-On

- [x] **Demo-JSON** - 360 Zeilen (1.04. ✅)
  - Alle v2.1 Felder
  - BuildingElement: Kellertreppe
  - Szenario mit Output & Einsparungen

- [x] **Dokumentation** (1.04. ✅)
  - Schema v2.1 Final Specification
  - Brainstorm-Dokument
  - Verbesserungen-Dokument

**Deliverables:**
- ✅ `viewer/src/store/viewer.store.ts` - TypeScript Types
- ✅ `viewer/public/demo/efh-demo.din18599.json` - Demo-JSON
- ✅ `.plans/schema-v2.1-final.md` - Dokumentation
- ✅ Git Commit + Push zu GitHub

#### Woche 2 (2.-7. April): Viewer-Implementierung

**Aufgaben:**
- [ ] **BuildingElement Logik** (2h)
  - `applyBuildingElements()` Funktion
  - Zonen-Flächen/Volumen anpassen
  - Bauteil-Flächen anpassen
  - Komponenten zur Hülle hinzufügen

- [ ] **Delta-Merge Funktion** (1h)
  - `applyScenario()` implementieren
  - Deep-Merge Logik
  - Array-Merge by ID

- [ ] **Viewer UI anpassen** (2h)
  - Neue Felder im Inspector anzeigen
  - Parent-Child Hierarchie in Sidebar
  - BuildingElements anzeigen

**Deliverables:**
- `viewer/src/utils/buildingElements.ts` - Logik
- `viewer/src/utils/scenarioMerge.ts` - Delta-Merge
- Aktualisierte UI-Komponenten

---

### **Phase 2: Szenario-Switcher & UI** (1 Woche, 8.-14. April)

**Ziel:** Szenario-Vergleich UI für Berlin-Präsentation

#### Woche 3 (8.-14. April): Szenario-Switcher

**Implementierung:**
- [ ] **Szenario-Switcher Komponente** (3h)
  - Dropdown/Tabs für Szenarien
  - Vergleichs-Tabelle (Vorher/Nachher)
  - Maßnahmen-Liste mit Kosten
  - Einsparungen anzeigen

- [ ] **3D-Viewer Updates** (2h)
  - Farbwechsel bei Szenario-Wechsel
  - Animationen (optional)
  - Performance-Optimierung

- [ ] **Testing** (1h)
  - Browser-Kompatibilität
  - Mobile-Ansicht
  - Demo-Durchlauf

**Deliverables:**
- Szenario-Switcher UI
- Vergleichs-Tabelle
- Funktionierende Demo

---

### **Phase 3: Katalog-System** (2 Wochen, 15.-28. April)

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
| **1. April** | Schema v2.1 Final | TypeScript Types, Demo-JSON, Doku | ✅ **FERTIG** |
| **7. April** | Viewer-Logik | applyBuildingElements, Delta-Merge | 🔄 Geplant |
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

### ✅ Abgeschlossen (1. April)
1. ✅ Schema v2.1 Final - Vollständig implementiert
2. ✅ TypeScript Types erstellt (410 Zeilen)
3. ✅ Demo-JSON erweitert (360 Zeilen)
4. ✅ Dokumentation geschrieben (3 Dokumente)
5. ✅ Git Commit + Push zu GitHub

### 🔄 Aktuell (2.-7. April)
1. **BuildingElement Logik** implementieren
2. **Delta-Merge Funktion** implementieren
3. **Viewer UI** anpassen (neue Felder)
4. **Szenario-Switcher** UI entwickeln

### 📅 Nächste Woche (8.-14. April)
5. Szenario-Vergleich UI
6. Testing & Performance
7. Demo-Präsentation vorbereiten

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

**Letzte Aktualisierung:** 1. April 2026  
**Nächste Review:** 14. April 2026 (nach Viewer-MVP)
