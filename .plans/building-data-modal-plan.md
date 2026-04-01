# Gebäudedaten-Modal - Implementierungsplan

> **Basierend auf:** Variante A Mockup  
> **Ziel:** Professionelles Inspect Panel für alle Gebäudedaten  
> **Framework:** React + TypeScript (Vanilla CSS, kein shadcn/ui)  
> **Deadline:** 2-3 Stunden

---

## 🎯 Ziel

Ein **großes, professionelles Modal** über dem 3D-Viewer, das alle Gebäudedaten strukturiert in **6 Tabs** anzeigt:

1. **📊 Übersicht** - Meta, KPIs, LOD
2. **🏠 Zonen** - Thermische Zonen
3. **🧱 Gebäudehülle** - Wände, Dächer, Böden
4. **🪟 Öffnungen** - Fenster, Türen (Parent-Child)
5. **🔧 Anlagentechnik** - HVAC Systems
6. **🏗️ BuildingElements** - LOD 300+ (Treppen, Gauben)

---

## 📐 Design-Prinzipien

### Visuelle Sprache
- **Sachlich & hochwertig** - keine Spielereien
- **Helle neutrale Flächen** - #f8fafc Hintergrund
- **Dunkle Typografie** - #1e293b für Text
- **Akzent Blau/Teal** - #3b82f6 für aktive Elemente
- **Orange nur für Warnungen** - #f59e0b
- **U-Wert Ampel** - Grün/Gelb/Rot für Qualität

### Layout
- **Desktop:** 1200px Breite, 85vh Höhe, zentriert
- **Mobile:** 100vw × 100dvh, Fullscreen
- **Backdrop:** Blur + Dunkel (rgba(0,0,0,0.5))
- **Border-Radius:** 16px (Desktop), 0px (Mobile)

### Typografie
- **Modal-Titel:** 24px semibold
- **Tab-Labels:** 14px medium
- **Tabellen-Header:** 12px uppercase semibold
- **Zell-Inhalt:** 14px regular
- **IDs/GUIDs:** 12px monospace
- **Metadaten:** 12px muted (#64748b)

---

## 🏗️ Komponenten-Architektur

```
viewer/src/components/
├── BuildingDataModal/
│   ├── BuildingDataModal.tsx          # Haupt-Modal + State
│   ├── BuildingDataHeader.tsx         # Sticky Header
│   ├── BuildingDataTabs.tsx           # Tab Navigation
│   │
│   ├── tabs/
│   │   ├── OverviewTab.tsx            # Tab 1: Übersicht
│   │   ├── ZonesTab.tsx               # Tab 2: Zonen
│   │   ├── EnvelopeTab.tsx            # Tab 3: Gebäudehülle
│   │   ├── OpeningsTab.tsx            # Tab 4: Öffnungen
│   │   ├── SystemsTab.tsx             # Tab 5: Anlagentechnik
│   │   └── BuildingElementsTab.tsx    # Tab 6: BuildingElements
│   │
│   ├── shared/
│   │   ├── DataTable.tsx              # Wiederverwendbare Tabelle
│   │   ├── MetricCard.tsx             # KPI-Karte
│   │   ├── StatusBadge.tsx            # Status-Badge (grün/gelb/rot)
│   │   ├── UValueIndicator.tsx        # U-Wert Ampel
│   │   ├── CopyButton.tsx             # Copy-to-Clipboard
│   │   └── ViewerLinkButton.tsx       # Jump to Viewer
│   │
│   └── BuildingDataModal.css          # Styling
```

---

## 📋 Implementierungs-Phasen

### **Phase 1: Basis-Komponenten** (30 Min)

**Ziel:** Modal-Grundgerüst mit Tabs funktionsfähig

**Tasks:**
1. `BuildingDataModal.tsx` erstellen
   - State: `isOpen`, `activeTab`
   - Backdrop mit Blur
   - ESC-Key Handler
   - Animation (fade-in)

2. `BuildingDataHeader.tsx` erstellen
   - Gebäude-Icon + Titel
   - Meta-Info (LOD, Zonen, Bauteile)
   - Export/JSON/Close Buttons
   - Sticky Behavior

3. `BuildingDataTabs.tsx` erstellen
   - 6 Tabs horizontal
   - Active State
   - Badge mit Anzahl
   - Icons

4. Viewer Store erweitern
   - `buildingDataModalOpen: boolean`
   - `openBuildingDataModal()`
   - `closeBuildingDataModal()`

5. In App.tsx integrieren
   - Button im TopBar "📊 Gebäudedaten"
   - Modal rendern

**Deliverable:** Funktionierendes Modal mit Tab-Navigation

---

### **Phase 2: Tab 1 - Übersicht** (20 Min)

**Ziel:** Executive Summary des Gebäudes

**Layout:**
```
┌─────────────────────────────────────────┐
│  KPI-Karten (4 Spalten)                 │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐           │
│  │End │ │Prim│ │CO₂ │ │Eff │           │
│  └────┘ └────┘ └────┘ └────┘           │
│                                         │
│  2-Spalten Layout:                      │
│  ┌──────────────┐ ┌──────────────┐     │
│  │ Projekt-Meta │ │ Klima-Daten  │     │
│  └──────────────┘ └──────────────┘     │
│                                         │
│  LOD-Panel (Progress Bars)              │
│  ┌──────────────────────────────────┐   │
│  │ Geometry:  ████████░░  300       │   │
│  │ Envelope:  ████████░░  300       │   │
│  │ Systems:   ████░░░░░░  200       │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

**Komponenten:**
- `MetricCard.tsx` - KPI-Karte
- `OverviewTab.tsx` - Layout + Daten

**Daten:**
- `project.output.energy_balance` für KPIs
- `project.meta` für Projekt-Info
- `project.input.building` für Gebäude-Info

---

### **Phase 3: Tab 2 - Zonen** (20 Min)

**Ziel:** Tabellarische Darstellung aller Zonen

**Tabelle:**
| Name | Nutzung | A_N | V | Θ_heiz | Θ_kühl | Luftwechsel | Status |
|------|---------|-----|---|--------|--------|-------------|--------|

**Features:**
- Sortierung pro Spalte
- Klick → Detailpanel rechts
- Badge für Nutzungsprofil
- Copy-Button für ID

**Komponenten:**
- `DataTable.tsx` - Wiederverwendbare Tabelle
- `ZonesTab.tsx` - Zonen-spezifisch

---

### **Phase 4: Tab 3 - Gebäudehülle** (30 Min)

**Ziel:** Opake Bauteile mit U-Wert Ampel

**Sektionen:**
1. Außenwände
2. Dächer
3. Böden
4. Innenwände

**Außenwände-Tabelle:**
| Name | Orient. | Fläche | U-Wert | ΔU | U-eff | α | Randbed. | Status |
|------|---------|--------|--------|----|----|---|----------|--------|

**Features:**
- U-Wert Farbcodierung (grün/gelb/rot)
- Orientierung mit Kompass-Icon
- Boundary Condition Badge
- Wärmebrücken-Typ Badge

**Komponenten:**
- `UValueIndicator.tsx` - U-Wert Ampel
- `EnvelopeTab.tsx` - Hülle-spezifisch

---

### **Phase 5: Tab 4 - Öffnungen** (25 Min)

**Ziel:** Fenster/Türen mit Parent-Child Beziehung

**Tabelle:**
| Name | Typ | Parent | Orient. | Fläche | Ug | Uf | g | fs | Status |
|------|-----|--------|---------|--------|----|----|---|-------|--------|

**Features:**
- Parent-Wall klickbar
- Hover → Highlight im Viewer
- Verschattung-Indikator
- Kompakte technische Labels

**Komponenten:**
- `OpeningsTab.tsx` - Öffnungen-spezifisch

---

### **Phase 6: Tab 5 - Anlagentechnik** (20 Min)

**Ziel:** Modulare Karten für Systeme

**Karten:**
1. Heizung
2. Warmwasser
3. Lüftung
4. Kühlung (optional)

**Heizungskarte:**
- Systemtyp
- Energieträger
- Baujahr
- COP/Kennwerte
- Zonen-Zuordnung

**Komponenten:**
- `SystemsTab.tsx` - Cards statt Tabelle

---

### **Phase 7: Tab 6 - BuildingElements** (15 Min)

**Ziel:** LOD 300+ Elemente

**Tabelle:**
| Name | Typ | LOD | Zone | Bauteile | Kommentar |
|------|-----|-----|------|----------|-----------|

**Features:**
- Nur anzeigen wenn vorhanden
- Relevanz-Badge
- Info-Panel rechts

**Komponenten:**
- `BuildingElementsTab.tsx`

---

### **Phase 8: Interaktionen** (20 Min)

**Ziel:** Nutzbarkeit verbessern

**Features:**
1. ESC schließt Modal ✅
2. Backdrop-Click schließt ✅
3. Tabellenkopf sticky
4. Sortierung pro Spalte
5. Copy-to-Clipboard für IDs
6. Klick auf Zeile → Highlight im Viewer
7. Viewer-Selektion → Modal öffnen

**Komponenten:**
- `CopyButton.tsx`
- `ViewerLinkButton.tsx`

---

### **Phase 9: Responsive Mobile** (25 Min)

**Ziel:** Mobile-optimierte Variante

**Änderungen:**
- Fullscreen (100vw × 100dvh)
- Tabs horizontal scrollbar
- Tabellen → Cards
- Kompakte Werte
- Touch-optimiert

**Breakpoint:** `@media (max-width: 768px)`

---

### **Phase 10: Testing & Polish** (15 Min)

**Ziel:** Qualitätssicherung

**Tasks:**
1. Demo-Projekt laden
2. Alle Tabs durchklicken
3. Sortierung testen
4. Mobile-Ansicht testen
5. Styling verfeinern
6. Performance prüfen

---

## 🎨 CSS-Variablen

```css
:root {
  /* Colors */
  --modal-bg: #ffffff;
  --modal-backdrop: rgba(0, 0, 0, 0.5);
  --text-primary: #1e293b;
  --text-secondary: #64748b;
  --text-muted: #94a3b8;
  
  --accent-blue: #3b82f6;
  --accent-teal: #14b8a6;
  --warning-orange: #f59e0b;
  
  --status-green: #22c55e;
  --status-yellow: #f59e0b;
  --status-red: #ef4444;
  --status-gray: #94a3b8;
  
  --border-color: #e5e7eb;
  --bg-light: #f8fafc;
  
  /* Spacing */
  --modal-padding: 20px;
  --section-gap: 24px;
  
  /* Typography */
  --font-mono: 'SF Mono', 'Consolas', monospace;
}
```

---

## 📊 Status-Logik

**U-Wert Ampel:**
```typescript
function getUValueStatus(uValue: number, elementType: 'wall' | 'roof' | 'floor') {
  const thresholds = {
    wall: { good: 0.24, medium: 0.5 },
    roof: { good: 0.14, medium: 0.35 },
    floor: { good: 0.25, medium: 0.5 }
  }
  
  const t = thresholds[elementType]
  if (uValue <= t.good) return 'green'
  if (uValue <= t.medium) return 'yellow'
  return 'red'
}
```

---

## ✅ Definition of Done

**Pro Phase:**
- [ ] Komponente funktioniert
- [ ] TypeScript ohne Fehler
- [ ] Styling passt zum Mockup
- [ ] Responsive (Desktop + Mobile)
- [ ] Daten aus Store geladen

**Gesamt:**
- [ ] Alle 6 Tabs funktionieren
- [ ] Modal öffnet/schließt smooth
- [ ] Interaktionen funktionieren
- [ ] Mobile-optimiert
- [ ] Demo getestet
- [ ] Code committed

---

## 🚀 Los geht's!

**Geschätzte Zeit:** 2-3 Stunden  
**Start:** Phase 1 - Basis-Komponenten
