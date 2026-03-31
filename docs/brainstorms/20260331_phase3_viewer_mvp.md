# Brainstorm: Phase 3 - Viewer-MVP mit Editor-Funktionen

**Datum:** 31. März 2026  
**Session:** #5 - Viewer-UX & Editor-Features  
**Ziel:** Professioneller Viewer + Editor-Funktionen für Berlin-Präsentation (Mai 2026)

---

## 🎯 Vision

**"Von Viewer zu Editor"** - Nicht nur Daten anzeigen, sondern auch bearbeiten!

**Langfristige Vision:** Eigenes Energieberaterprogramm auf Basis von DIN 18599 IFC Sidecar

**MVP-Ziel (Mai 2026):**
- ✅ 3D-Viewer (bereits vorhanden)
- ✅ Katalog-Browser
- ✅ Bauteil-Editor (NEU!)
- ✅ Szenario-Vergleich
- ✅ Live-Demo-fähig

---

## 🏗️ Architektur-Entscheidungen

### **1. Layout: 3-Panel-Design**

```
┌─────────────────────────────────────────────────────────┐
│  TopBar: Logo | Project Name | Actions (Save, Export)  │
├──────────────┬──────────────────────────────┬───────────┤
│              │                              │           │
│  Sidebar     │      3D Viewer               │  Inspector│
│  (Tree)      │      (Three.js)              │  (Details)│
│              │                              │           │
│  • Building  │                              │  Selected:│
│    • Zones   │      [3D Model]              │  Wall 1   │
│    • Walls   │                              │           │
│    • Windows │                              │  U-Value: │
│    • Roof    │                              │  [1.2]    │
│              │                              │           │
│  • Systems   │                              │  [Edit]   │
│    • Heating │                              │  [Catalog]│
│              │                              │           │
│  • Scenarios │                              │           │
│    ▶ Base    │                              │           │
│    ▶ WDVS    │                              │           │
│              │                              │           │
├──────────────┴──────────────────────────────┴───────────┤
│  BottomBar: Stats | Energiekennwerte | Warnings         │
└─────────────────────────────────────────────────────────┘
```

**Vorteile:**
- ✅ Übersichtlich (3 klare Bereiche)
- ✅ Fokus auf 3D-Viewer (Hauptbereich)
- ✅ Inspector für Details (rechts)
- ✅ Tree-Navigation (links)

---

### **2. Navigation: Tree-View mit Suche**

```
Sidebar (Tree-View):
├── 📦 Building
│   ├── 🏠 Zones
│   │   ├── Zone EG (72.5 m²)
│   │   └── Zone OG (73.0 m²)
│   │
│   ├── 🧱 Envelope
│   │   ├── Walls External (4)
│   │   │   ├── Wall Süd (35.2 m²) ⚠️
│   │   │   ├── Wall Nord (28.5 m²)
│   │   │   ├── Wall Ost (22.1 m²)
│   │   │   └── Wall West (22.1 m²)
│   │   │
│   │   ├── Windows (8)
│   │   ├── Roof (1)
│   │   └── Floor (1)
│   │
│   └── 🔧 Systems
│       ├── Heating (Gas Boiler)
│       ├── Ventilation (Natural)
│       └── DHW (Central)
│
├── 🎭 Scenarios
│   ├── ▶ Base (Bestand)
│   ├── ▶ Sanierung Stufe 1 (WDVS)
│   └── ▶ Sanierung Stufe 2 (+ WP)
│
└── 📊 Results
    ├── Base: 203.7 kWh/(m²a)
    ├── Stufe 1: 116.4 kWh/(m²a) (-43%)
    └── Stufe 2: 65.3 kWh/(m²a) (-68%)
```

**Features:**
- ✅ Hierarchische Struktur (wie Schema v2.1)
- ✅ Icons für Kategorien
- ✅ Flächen/Kennwerte direkt sichtbar
- ✅ Warnings (⚠️) bei Problemen
- ✅ Szenario-Switcher

---

### **3. Highlighting-Strategie**

**Interaktion:**
```
Klick auf "Wall Süd" im Tree
    ↓
3D-Viewer: Wall wird gelb highlighted
    ↓
Inspector: Details werden angezeigt
    ↓
Kamera: Zoom auf Wall (optional)
```

**Highlighting-Modi:**
- **Selected:** Gelb (aktuell ausgewählt)
- **Hover:** Hellblau (Maus darüber)
- **Warning:** Rot (U-Wert zu hoch)
- **Modified:** Grün (in Szenario geändert)

---

## ✏️ Editor-Funktionen (MVP)

### **1. Bauteil-Editor (Inspector Panel)**

```
┌─────────────────────────────────┐
│  Inspector: Wall Süd            │
├─────────────────────────────────┤
│                                 │
│  📐 Geometrie                   │
│  ├─ Fläche: 35.2 m²            │
│  ├─ Orientierung: 180° (Süd)   │
│  └─ Neigung: 90° (vertikal)    │
│                                 │
│  🧱 Konstruktion                │
│  ├─ Katalog: [Dropdown ▼]      │
│  │   • WALL_UNINSULATED        │
│  │   • WALL_WDVS_120           │
│  │   • WALL_WDVS_160 ✓         │
│  │   • WALL_WDVS_200           │
│  │                              │
│  ├─ U-Wert: 0.21 W/(m²K)       │
│  └─ [Details anzeigen]         │
│                                 │
│  🎨 Darstellung                 │
│  ├─ Farbe: [#cccccc]           │
│  └─ Transparenz: 100%          │
│                                 │
│  [Speichern] [Abbrechen]       │
└─────────────────────────────────┘
```

**Funktionen:**
- ✅ Katalog-Dropdown (Construction auswählen)
- ✅ U-Wert Override (manuell eingeben)
- ✅ Geometrie anzeigen (read-only)
- ✅ Speichern → Delta wird erstellt

---

### **2. Katalog-Browser**

```
┌─────────────────────────────────┐
│  Katalog: Konstruktionen        │
├─────────────────────────────────┤
│                                 │
│  🔍 Suche: [WDVS...]           │
│                                 │
│  📁 Außenwände (12)             │
│  ├─ WALL_EXT_BRICK_UNINSULATED │
│  │   U: 1.20 W/(m²K)           │
│  │                              │
│  ├─ WALL_EXT_BRICK_WDVS_120    │
│  │   U: 0.28 W/(m²K)           │
│  │                              │
│  ├─ WALL_EXT_BRICK_WDVS_160 ✓  │
│  │   U: 0.21 W/(m²K)           │
│  │   [Schichtaufbau anzeigen]  │
│  │                              │
│  └─ WALL_EXT_BRICK_WDVS_200    │
│      U: 0.17 W/(m²K)           │
│                                 │
│  📁 Dächer (4)                  │
│  📁 Böden (3)                   │
│                                 │
│  [Auswählen] [Abbrechen]       │
└─────────────────────────────────┘
```

**Features:**
- ✅ Suche (Filter nach Name/U-Wert)
- ✅ Kategorien (Wände, Dächer, Böden)
- ✅ Schichtaufbau-Details
- ✅ Drag & Drop auf 3D-Modell (optional)

---

### **3. Schichtaufbau-Visualisierung**

```
┌─────────────────────────────────┐
│  Schichtaufbau: WALL_WDVS_160   │
├─────────────────────────────────┤
│                                 │
│  Außen → Innen:                 │
│                                 │
│  ┌─────────────────────────┐   │
│  │ Putz außen (10mm)       │   │
│  │ λ = 0.87 W/(mK)         │   │
│  ├─────────────────────────┤   │
│  │ WDVS EPS (160mm)        │   │
│  │ λ = 0.035 W/(mK) ████   │   │
│  ├─────────────────────────┤   │
│  │ Ziegel (240mm)          │   │
│  │ λ = 0.50 W/(mK)         │   │
│  ├─────────────────────────┤   │
│  │ Putz innen (10mm)       │   │
│  │ λ = 0.87 W/(mK)         │   │
│  └─────────────────────────┘   │
│                                 │
│  Gesamt-U-Wert: 0.21 W/(m²K)   │
│  Gesamtdicke: 420 mm           │
│                                 │
│  [Schließen]                    │
└─────────────────────────────────┘
```

**Visualisierung:**
- ✅ Schichten von außen nach innen
- ✅ Dicke proportional (Balkendiagramm)
- ✅ λ-Werte anzeigen
- ✅ Gesamt-U-Wert berechnet

---

### **4. Szenario-Editor**

```
┌─────────────────────────────────┐
│  Szenario: Sanierung Stufe 1    │
├─────────────────────────────────┤
│                                 │
│  📝 Name: [Sanierung Stufe 1]  │
│  📅 Timeline: [2026]            │
│  ⭐ Priorität: [1]              │
│                                 │
│  🔄 Änderungen (Delta):         │
│                                 │
│  • Wall Süd                     │
│    ├─ Alt: WALL_UNINSULATED     │
│    └─ Neu: WALL_WDVS_160 ✓     │
│                                 │
│  • Window 1                     │
│    ├─ Alt: WINDOW_DOUBLE        │
│    └─ Neu: WINDOW_TRIPLE ✓     │
│                                 │
│  [+ Änderung hinzufügen]        │
│                                 │
│  💰 Kosten: ~45.000 €           │
│  💡 Einsparung: -43% Energie    │
│                                 │
│  [Speichern] [Löschen]          │
└─────────────────────────────────┘
```

**Features:**
- ✅ Szenario-Metadaten (Name, Timeline, Priorität)
- ✅ Delta-Liste (Änderungen anzeigen)
- ✅ Änderungen hinzufügen/entfernen
- ✅ Kosten/Einsparungen (wenn Output vorhanden)

---

### **5. Vergleichs-Modus**

```
┌─────────────────────────────────────────────────────────┐
│  Vergleich: Base ↔ Sanierung Stufe 1                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────┬──────────────────┬──────────────┐│
│  │ Base (Bestand)   │ Sanierung Stufe 1│ Differenz    ││
│  ├──────────────────┼──────────────────┼──────────────┤│
│  │ 203.7 kWh/(m²a) │ 116.4 kWh/(m²a) │ -87.3 (-43%)││
│  │ 26110 kWh/a     │ 14850 kWh/a     │ -11260       ││
│  │ 5271 kg CO₂/a   │ 3012 kg CO₂/a   │ -2259 (-43%)││
│  └──────────────────┴──────────────────┴──────────────┘│
│                                                         │
│  🔄 Geänderte Bauteile:                                │
│  • Wall Süd: U 1.20 → 0.21 W/(m²K) ✓                  │
│  • Window 1: U 2.80 → 0.70 W/(m²K) ✓                  │
│                                                         │
│  [3D-Vergleich] [Export PDF]                           │
└─────────────────────────────────────────────────────────┘
```

**Features:**
- ✅ Side-by-Side Vergleich
- ✅ Kennwerte-Tabelle
- ✅ Geänderte Bauteile hervorheben
- ✅ 3D-Vergleich (Split-Screen)

---

## 🎨 UI/UX-Design

### **Technologie-Stack:**

| Komponente | Technologie | Warum? |
|------------|-------------|--------|
| **Framework** | React + TypeScript | Modern, typsicher, große Community |
| **3D-Rendering** | Three.js | Bereits implementiert, performant |
| **UI-Library** | shadcn/ui + Tailwind | Modern, customizable, DWEapp-Style |
| **State Management** | Zustand | Einfach, performant |
| **Routing** | React Router | Standard |
| **Build** | Vite | Schnell, modern |

### **Design-System:**

```css
/* Farben (DWEapp-inspiriert) */
--primary: #2563eb;      /* Blau */
--success: #10b981;      /* Grün */
--warning: #f59e0b;      /* Orange */
--danger: #ef4444;       /* Rot */
--gray-50: #f9fafb;
--gray-900: #111827;

/* Highlighting */
--highlight-selected: #fbbf24;  /* Gelb */
--highlight-hover: #60a5fa;     /* Hellblau */
--highlight-warning: #ef4444;   /* Rot */
--highlight-modified: #10b981;  /* Grün */
```

---

## 🎯 MVP-Features (Priorität)

### **🔴 Must-Have (für Berlin-Präsentation)**

1. ✅ **3D-Viewer** (bereits vorhanden)
   - Rotation, Zoom, Pan
   - Highlighting (Selected, Hover)

2. ✅ **Tree-Navigation**
   - Hierarchische Struktur
   - Klick → 3D-Highlight
   - Icons für Kategorien

3. ✅ **Inspector Panel**
   - Bauteil-Details anzeigen
   - Katalog-Dropdown
   - U-Wert anzeigen

4. ✅ **Katalog-Browser**
   - Konstruktionen durchsuchen
   - Schichtaufbau anzeigen
   - Auswahl → Inspector

5. ✅ **Szenario-Switcher**
   - Base ↔ Szenarien wechseln
   - 3D-Modell aktualisiert sich
   - Kennwerte anzeigen

### **🟠 Should-Have (wenn Zeit)**

6. ⏳ **Bauteil-Editor**
   - Katalog-Referenz ändern
   - Delta wird erstellt
   - Speichern → JSON-Update

7. ⏳ **Vergleichs-Modus**
   - Side-by-Side Tabelle
   - Geänderte Bauteile highlighten

8. ⏳ **Export-Funktionen**
   - Screenshot (3D-Ansicht)
   - PDF-Report (Kennwerte)
   - JSON-Download

### **🟡 Nice-to-Have (später)**

9. 🔮 **Drag & Drop**
   - Katalog → 3D-Modell
   - Automatisches Mapping

10. 🔮 **Undo/Redo**
    - Änderungen rückgängig machen
    - History-Stack

11. 🔮 **Kollaboration**
    - Mehrere Nutzer gleichzeitig
    - WebSocket-Sync

---

## 🎬 Demo-Szenario (Berlin-Präsentation)

### **Projekt: Einfamilienhaus Musterstraße 1**

**Ausgangslage:**
- Baujahr: 1978
- Ungedämmt
- Doppelverglasung
- Gas-Heizkessel (Baujahr 1995)
- Energiebedarf: 203.7 kWh/(m²a)

**Sanierungsszenarien:**
1. **Stufe 1:** WDVS 160mm + Dreifachverglasung
   - Einsparung: -43%
   - Kosten: ~45.000 €

2. **Stufe 2:** + Wärmepumpe + PV
   - Einsparung: -68%
   - Kosten: ~75.000 €

---

### **Live-Demo-Script (5 Minuten)**

**Minute 1: Projekt laden**
```
1. Browser öffnen: https://din18599-ifc.github.io
2. "Demo laden" klicken
3. 3D-Modell wird geladen
4. "Das ist unser Einfamilienhaus von 1978, ungedämmt"
```

**Minute 2: Navigation & Inspektion**
```
5. Tree aufklappen: "Building → Envelope → Walls"
6. "Wall Süd" klicken
7. 3D-Modell: Wall wird gelb highlighted
8. Inspector: "U-Wert 1.20 W/(m²K) - viel zu hoch!"
```

**Minute 3: Katalog durchsuchen**
```
9. "Katalog" Button klicken
10. Suche: "WDVS"
11. "WALL_WDVS_160" auswählen
12. Schichtaufbau anzeigen: "160mm Dämmung"
13. "U-Wert sinkt auf 0.21 W/(m²K)"
```

**Minute 4: Szenario wechseln**
```
14. Szenario-Switcher: "Base" → "Sanierung Stufe 1"
15. 3D-Modell: Wände werden grün (= geändert)
16. Kennwerte: "203.7 → 116.4 kWh/(m²a) (-43%)"
17. "Das sind 870 € Einsparung pro Jahr!"
```

**Minute 5: Vergleich & Ausblick**
```
18. Vergleichs-Modus aktivieren
19. Tabelle: Base ↔ Stufe 1 ↔ Stufe 2
20. "Stufe 2 mit Wärmepumpe: -68% Energie"
21. "Open Source, Apache 2.0, GitHub verfügbar"
22. "Fragen?"
```

---

## 🛠️ Implementierungs-Plan

### **Woche 1 (1.-7. April): Grundgerüst**

**Tag 1-2: Setup**
- [ ] React + Vite Projekt aufsetzen
- [ ] Three.js Integration (bestehenden Code migrieren)
- [ ] shadcn/ui + Tailwind einrichten
- [ ] Layout-Komponenten (TopBar, Sidebar, Inspector)

**Tag 3-4: Tree-Navigation**
- [ ] Tree-View Komponente (hierarchisch)
- [ ] JSON → Tree-Daten Mapping
- [ ] Klick-Handler (Tree → 3D-Highlight)
- [ ] Icons für Kategorien

**Tag 5-7: Inspector Panel**
- [ ] Inspector-Layout
- [ ] Bauteil-Details anzeigen
- [ ] Katalog-Dropdown (read-only)
- [ ] U-Wert, Fläche, Orientierung

---

### **Woche 2 (8.-14. April): Katalog & Editor**

**Tag 8-10: Katalog-Browser**
- [ ] Katalog-Modal
- [ ] Suche & Filter
- [ ] Schichtaufbau-Visualisierung
- [ ] Auswahl → Inspector

**Tag 11-12: Bauteil-Editor (MVP)**
- [ ] Katalog-Referenz ändern
- [ ] Delta erstellen
- [ ] JSON-Update (in-memory)
- [ ] Speichern-Button

**Tag 13-14: Szenario-Switcher**
- [ ] Szenario-Dropdown
- [ ] Delta-Merge implementieren (siehe MERGE_ALGORITHM.md)
- [ ] 3D-Modell aktualisieren
- [ ] Kennwerte anzeigen

---

### **Woche 3 (15.-21. April): Polish & Demo**

**Tag 15-17: Vergleichs-Modus**
- [ ] Vergleichs-Tabelle
- [ ] Geänderte Bauteile highlighten
- [ ] Export-Funktionen (Screenshot, PDF)

**Tag 18-19: Demo-Projekt**
- [ ] Einfamilienhaus-JSON erstellen
- [ ] 2 Sanierungsszenarien
- [ ] Output-Daten (mock oder real)

**Tag 20-21: Testing & Bugfixes**
- [ ] Browser-Kompatibilität (Chrome, Firefox, Safari)
- [ ] Mobile-Ansicht (Tablet)
- [ ] Performance-Optimierung
- [ ] Bugfixes

---

## 📊 Erfolgs-Kriterien

### **Viewer-MVP ist erfolgreich, wenn:**

1. ✅ 3D-Modell wird korrekt dargestellt
2. ✅ Navigation funktioniert (Tree → 3D-Highlight)
3. ✅ Katalog-Browser funktioniert
4. ✅ Bauteil-Details werden angezeigt
5. ✅ Szenario-Wechsel funktioniert
6. ✅ Live-Demo läuft flüssig (5 Min ohne Fehler)
7. ✅ Browser-kompatibel (Chrome, Firefox, Safari)

---

## 🚀 Langfristige Vision: Eigenes Energieberaterprogramm

### **Roadmap 2026-2027:**

**Q2 2026 (April-Juni):**
- ✅ Viewer-MVP (Berlin-Präsentation)
- ⏳ Editor-Funktionen (Bauteil-Editor)

**Q3 2026 (Juli-September):**
- 🔮 IFC-Import (web-ifc)
- 🔮 Erweiterte Editor-Funktionen (Zonen, Systeme)
- 🔮 Berechnungs-Integration (externe Software)

**Q4 2026 (Oktober-Dezember):**
- 🔮 Vollständiger Editor (alle 18 Kategorien)
- 🔮 Berechnungs-Engine (eigene Implementierung?)
- 🔮 Energieausweis-Generator

**2027:**
- 🔮 Cloud-Version (SaaS)
- 🔮 Kollaboration (Multi-User)
- 🔮 KI-Assistent (Sanierungsempfehlungen)

### **Differenzierung zu bestehenden Tools:**

| Feature | Hottgenroth | Dämmwerk | **Unser Tool** |
|---------|-------------|----------|----------------|
| **Open Source** | ❌ | ❌ | ✅ |
| **IFC-Integration** | ⚠️ | ⚠️ | ✅ |
| **3D-Viewer** | ❌ | ❌ | ✅ |
| **Browser-basiert** | ❌ | ❌ | ✅ |
| **Katalog-System** | ✅ | ✅ | ✅ |
| **DIN 18599** | ✅ | ✅ | ✅ |
| **Kosten** | 💰💰💰 | 💰💰 | 🆓 |

**USP:** Open Source + IFC + 3D + Browser-basiert!

---

## 📚 Referenzen

- **Schema v2.1:** `schema/v2.1-complete.json`
- **Merge-Algorithmus:** `docs/MERGE_ALGORITHM.md`
- **Katalog-Guide:** `docs/CATALOG_GUIDE.md`
- **Bestehender Viewer:** `viewer/index.html`

---

## ✅ Nächste Schritte

1. **Heute (31. März):**
   - ✅ Brainstorm dokumentiert
   - ⏳ Roadmap aktualisieren
   - ⏳ GitHub Issues erstellen

2. **Morgen (1. April):**
   - React + Vite Setup
   - Three.js Migration
   - Layout-Komponenten

3. **Diese Woche:**
   - Tree-Navigation
   - Inspector Panel
   - Katalog-Browser (Grundgerüst)

---

**Erstellt:** 31. März 2026  
**Session:** #5  
**Status:** Ready to implement! 🚀
