# Phase 3: Viewer/Editor Implementierungs-Plan

**Stand:** 31. März 2026  
**Deadline:** 12. Mai 2026 (Berlin-Präsentation)  
**Stack:** React Three Fiber + Drei + shadcn/ui + Zustand  
**Basis:** Bestehender Three.js Viewer (900 Zeilen) → Migration zu R3F

---

## 🎓 Was wir von den Besten lernen

### Von FloorspaceJS (NREL) lernen

**1. Zonen-Modell: Story-by-Story**
```
FloorspaceJS macht es so:
  Story (Stockwerk) → Spaces (Räume) → Thermal Zones (Gruppen)

Wir übernehmen:
  Zone (DIN 18599) = Raum-Gruppe mit gleicher Nutzung
  → Tree: Building → Zones → Bauteile
```

**2. Assignments-Tab: Nutzungsprofil-Zuweisung per Klick**
```
FloorspaceJS macht es so:
  Space auswählen → "Space Type" aus Dropdown → sofort assigned

Wir übernehmen:
  Bauteil klicken → Inspector → "Nutzungsprofil" Dropdown
  → usage_profile_ref aus unserem Katalog (45 Profile)
```

**3. Construction Sets: Schichtaufbauten zuweisen**
```
FloorspaceJS macht es so:
  Construction Set erstellen → Surfaces zuweisen → U-Wert auto-berechnet

Wir übernehmen:
  Wand/Dach/Boden klicken → Inspector → construction_ref Dropdown
  → U-Wert kommt automatisch aus Katalog
  → Override möglich (eigener U-Wert)
```

**4. Image Import für Floor Plans**
```
FloorspaceJS macht es so:
  Grundriss-Bild importieren → als Textur unter 3D-Modell
  → Berater zeichnet nach

Wir übernehmen (Phase 2):
  IFC importieren → Geometrie automatisch übernehmen
  → Sidecar JSON wird automatisch erstellt
```

**5. Fokus-UX: Keine CAD-Komplexität**
```
FloorspaceJS macht es so:
  Nur was für Energieberatung nötig ist
  → Keine Bemaßungen, keine CAD-Features
  → Schnell, fokussiert, energieberater-freundlich

Wir übernehmen:
  Inspector zeigt ONLY energierelevante Felder
  (U-Wert, Orientierung, Fläche, Nutzungsprofil)
  → Kein "Farbe", kein "Material-ID" als Hauptfeature
```

---

### Von xeokit (BIM/IFC Viewer) lernen

**6. Object Tree: IFC-Hierarchie spiegelt Schema wider**
```
xeokit macht es so:
  IfcBuilding > IfcBuildingStorey > IfcSpace > IfcWall

Wir übernehmen:
  Building > Zones > Envelope > walls_external > wall_sued
  → Tree = exakt unser Schema v2.1!
  → Klick im Tree = Highlight im 3D
  → Klick im 3D = Auswahl im Tree
```

**7. Picking via Raycasting + Material Override**
```
xeokit macht es so:
  Maus-Klick → Raycast → getroffenes Mesh → Material-Override (Glow/Outline)

Wir übernehmen in R3F:
  onPointerDown auf jedem Mesh → setSelected(id)
  → Zustand-Store → andere Farbe (gelb = selected, grün = modified)
  → Outline-Effekt via @react-three/postprocessing
```

**8. Performance: Instancing + LOD**
```
xeokit macht es so:
  InstancedMesh für alle Fenster (gleiche Geometrie, verschiedene Positionen)
  Culling (sichtbare Objekte berechnen)

Wir übernehmen:
  <InstancedMesh> für identische Bauteile
  <Suspense> für lazy loading
  Komprimierung: GLTF + Draco
  Ziel: < 50k Triangles für Demo-Gebäude
```

**9. Section Cuts (Querschnitt)**
```
xeokit macht es so:
  ClipPlane API → dynamischer Schnitt durch Modell

Wir übernehmen (Nice-to-Have):
  <ClippingPlane> aus Drei
  → Demo-Effekt: "Sehen Sie den Schichtaufbau von innen"
  → Perfekt für Berlin-Präsentation!
```

**10. 3D-Labels direkt am Objekt**
```
xeokit macht es so:
  HTML-Annotations direkt im 3D-Raum (z.B. "U=1.2 W/m²K")

Wir übernehmen mit R3F <Html>:
  <Html position={wall.center}>
    <div className="label">U: {wall.u_value}</div>
  </Html>
  → Hover → Label erscheint
  → Click → Inspector öffnet sich
```

---

### Von React Three Fiber lernen

**11. Deklaratives 3D = Wartbarer Code**
```javascript
// Three.js (imperativ - unser aktueller Code)
const geometry = new THREE.BoxGeometry(w, h, d)
const material = new THREE.MeshStandardMaterial({ color })
const mesh = new THREE.Mesh(geometry, material)
mesh.position.set(x, y, z)
scene.add(mesh)

// R3F (deklarativ - was wir bauen)
<Wall id={wall.id} data={wall} selected={selectedId === wall.id}>
  <meshStandardMaterial color={getWallColor(wall)} />
</Wall>
```

**12. Zustand-Store für 3D-State**
```typescript
// Ein Store für alles (mit Zustand)
const useViewerStore = create((set) => ({
  // Daten
  project: null,
  activeScenario: 'base',
  
  // UI-State
  selectedId: null,
  hoveredId: null,
  
  // Editor-State
  editMode: false,
  pendingDeltas: [],
  
  // Actions
  selectElement: (id) => set({ selectedId: id }),
  applyDelta: (delta) => set((s) => ({ pendingDeltas: [...s.pendingDeltas, delta] })),
  switchScenario: (id) => set({ activeScenario: id }),
}))
```

**13. OrbitControls + TransformControls**
```jsx
// Navigation (immer aktiv)
<OrbitControls makeDefault />

// Editor-Mode (nur wenn editMode=true)
{editMode && selectedId && (
  <TransformControls mode="translate" />
)}
```

**14. Html-Labels für Energiedaten**
```jsx
// Direkt am Bauteil (von xeokit-Idee + R3F umgesetzt)
function WallLabel({ wall }) {
  return (
    <Html position={wall.centerPoint} occlude>
      <div className="wall-label">
        <span>{wall.u_value} W/(m²K)</span>
        {wall.u_value > 0.5 && <span className="warning">⚠️</span>}
      </div>
    </Html>
  )
}
```

---

## 🏗️ Architektur

```
viewer/
├── src/
│   ├── App.tsx                    # Root: Layout
│   ├── store/
│   │   └── viewer.store.ts        # Zustand Store (zentraler State)
│   ├── components/
│   │   ├── layout/
│   │   │   ├── TopBar.tsx
│   │   │   ├── Sidebar.tsx        # Tree-Navigation (von xeokit lernen)
│   │   │   ├── Inspector.tsx      # Detail-Panel (von FloorspaceJS lernen)
│   │   │   └── BottomBar.tsx      # Energie-Kennwerte
│   │   ├── viewer3d/
│   │   │   ├── Scene.tsx          # R3F Canvas + OrbitControls
│   │   │   ├── Building.tsx       # Gebäude-Container
│   │   │   ├── Wall.tsx           # Einzel-Bauteil (Mesh + Picking + Label)
│   │   │   ├── Window.tsx
│   │   │   ├── Roof.tsx
│   │   │   └── WallLabel.tsx      # Html-Label (von xeokit)
│   │   ├── catalog/
│   │   │   ├── CatalogBrowser.tsx # Konstruktionen/Materialien
│   │   │   └── LayerStack.tsx     # Schichtaufbau-Visualisierung
│   │   └── scenarios/
│   │       ├── ScenarioBar.tsx    # Base ↔ Szenario wechseln
│   │       └── CompareTable.tsx   # Vergleichs-Modus
│   ├── lib/
│   │   ├── merge.ts               # Delta-Merge Algorithmus
│   │   ├── schema.ts              # Zod-Validator für DIN 18599
│   │   └── catalog.ts             # Katalog-Loader
│   └── types/
│       └── din18599.ts            # TypeScript Types (aus Schema v2.1)
├── public/
│   └── demo/
│       └── efh-1978.din18599.json # Demo-Projekt
└── package.json
```

---

## 📅 Implementierungs-Plan (6 Wochen)

### **Woche 0 (1. April): Setup + Migration (1 Tag)**

**Ziel:** React-Projekt aufsetzen, Three.js → R3F migrieren

```bash
# Setup
npm create vite@latest viewer -- --template react-ts
cd viewer
npm install @react-three/fiber @react-three/drei three zustand
npm install @react-three/postprocessing  # Outline-Effekte
npm install zod                           # Schema-Validierung
npm install -D tailwindcss @shadcn/ui     # UI
```

**Tasks:**
- [ ] Vite + React + TypeScript Setup
- [ ] Three.js Code (900 Zeilen) → R3F-Komponenten konvertieren
- [ ] Grundlayout: TopBar + Sidebar + Canvas + Inspector
- [ ] Demo-JSON laden und 3D-Box pro Bauteil anzeigen
- [ ] OrbitControls (Navigation)

**Output:** Funktionierender R3F-Viewer mit Demo-Gebäude ✅

---

### **Woche 1 (2.-7. April): Object Tree + Picking (xeokit-Lernpunkt)**

**Ziel:** Hierarchische Navigation + 3D-Auswahl

**Tasks:**
- [ ] **Tree-Navigation** (Lernpunkt #6):
  - Komponente: `Sidebar.tsx`
  - Schema: `Building → Zones → Envelope → walls_external[]`
  - Klapp-Logik (expand/collapse)
  - Icons: Lucide (Building2, Layers, Window, Thermometer)
  - Klick auf Tree-Item → `selectElement(id)`

- [ ] **Raycasting/Picking** (Lernpunkt #7):
  - Jedes `<Wall>` Mesh hat `onPointerDown`, `onPointerOver`
  - `selectedId` in Zustand-Store
  - Farbe: Standard=grau, Hover=blau, Selected=gelb, Modified=grün

- [ ] **Bidirektionale Synchronisation:**
  - Tree-Klick → 3D-Highlight → Inspector
  - 3D-Klick → Tree-Scroll-to → Inspector

**Output:** Vollständige Navigation (Tree ↔ 3D ↔ Inspector) ✅

---

### **Woche 2 (8.-14. April): Inspector + Katalog (FloorspaceJS-Lernpunkt)**

**Ziel:** Bauteil-Details anzeigen + Katalog zuweisen

**Tasks:**
- [ ] **Inspector Panel** (Lernpunkt #2, #3):
  - Nur energierelevante Felder (kein UX-Ballast!)
  - Geometrie: Fläche, Orientierung (read-only)
  - Konstruktion: `construction_ref` Dropdown → Katalog
  - U-Wert: Auto aus Katalog + Override-Feld
  - Nutzungsprofil: `usage_profile_ref` Dropdown (Lernpunkt #2)

- [ ] **Katalog-Browser** (Lernpunkt #3):
  - Modal über Inspector-Button
  - Liste: alle 24 Konstruktionen, gefiltert nach Bauteiltyp
  - Schichtaufbau-Visualisierung (proportionale Balken)
  - Auswahl → Inspector → construction_ref wird gesetzt

- [ ] **Zod-Validierung** (kritischer Lernpunkt aus Review):
  - Schema aus `schema/v2.1-complete.json` → TypeScript-Types
  - Validator: `validateDIN18599(data)` → Fehler anzeigen
  - Inspector-Felder mit Validierung (min/max U-Wert etc.)

**Output:** Vollständiger Inspector mit Katalog-Integration ✅

---

### **Woche 3 (15.-21. April): Szenarien + Delta-Modell**

**Ziel:** Szenario-Wechsel + Editor-Funktionen

**Tasks:**
- [ ] **Szenario-Bar** (Dropdown oben):
  - Base | Sanierung Stufe 1 | Sanierung Stufe 2
  - Wechsel → Delta-Merge ausführen → 3D aktualisiert sich
  - Modified-Bauteile werden grün

- [ ] **Delta-Editor** (Lernpunkt #3 FloorspaceJS):
  - Inspector: "Zu Szenario hinzufügen" Button
  - Wenn Szenario aktiv: Änderung → Delta wird erstellt
  - Delta-Liste im Szenario-Panel (Was wurde geändert?)

- [ ] **Delta-Merge Implementierung:**
  - `lib/merge.ts` aus `docs/MERGE_ALGORITHM.md`
  - Base + Delta → Merged → 3D-Update
  - Unit-Tests für alle 8 Test-Cases

**Output:** Vollständiger Szenario-Wechsel mit Delta-Editor ✅

---

### **Woche 4 (22.-28. April): 3D-Labels + Vergleich + Demo-Daten**

**Ziel:** Polish + Vergleichs-Modus + Demo-Projekt

**Tasks:**
- [ ] **Html-Labels** (Lernpunkt #10 xeokit + R3F):
  ```jsx
  // Hover → U-Wert Label direkt am Bauteil
  <Html position={wall.center} occlude>
    <Badge>U: {wall.uValue} W/(m²K)</Badge>
  </Html>
  ```
  - Hover → erscheint
  - ⚠️ Warnung wenn U-Wert > GEG-Grenzwert

- [ ] **Bottom Bar: Energiekennwerte:**
  - Wenn Output vorhanden: Endenergie, Primärenergie, CO₂
  - Wenn kein Output: "Noch nicht berechnet"

- [ ] **Vergleichs-Modus:**
  - Side-by-Side Tabelle: Base ↔ Szenario 1 ↔ Szenario 2
  - Differenz + Prozent
  - Geänderte Bauteile markiert

- [ ] **Demo-Projekt EFH 1978:**
  - Vollständiges DIN 18599 JSON (Schema v2.1)
  - 2 Szenarien (WDVS + Fenster / + Wärmepumpe)
  - Mock-Output-Daten (Kennwerte für Vergleich)

**Output:** Demo-Projekt mit allen Features ✅

---

### **Woche 5 (29. April - 5. Mai): Performance + IFC-Vorbereitung**

**Ziel:** Stabil, performant, Berlin-ready

**Tasks:**
- [ ] **Performance** (Lernpunkt #8 xeokit):
  - Draco-Kompression für GLTF
  - InstancedMesh für gleiche Geometrien
  - < 50k Triangles (Ziel!)
  - FPS-Test: Muss flüssig auf Beamer

- [ ] **Section Cut** (Lernpunkt #9 xeokit - Nice-to-Have):
  - ClipPlane durch Wand → Schichtaufbau sichtbar
  - "Röntgen-Modus" für Demo

- [ ] **web-ifc Proof-of-Concept:**
  - `npm install web-ifc`
  - Einfaches IFC laden → JSON extrahieren
  - Noch kein vollständiges Feature, nur PoC

- [ ] **DSGVO** (kritischer Lernpunkt aus Review):
  - Lokale Verarbeitung bestätigen (kein API-Call)
  - Privacy-Policy-Seite
  - Kein Analytics ohne Consent

**Output:** Performanter, DSGVO-konformer Viewer ✅

---

### **Woche 6 (6.-12. Mai): Berlin-Demo + Testing**

**Ziel:** Live-Demo-fähig, bugfrei, präsentationsbereit

**Tasks:**
- [ ] **Browser-Tests:** Chrome, Firefox, Safari, Edge
- [ ] **Live-Demo-Script** (5 Min Walkthrough):
  - Minute 1: Projekt laden → 3D-Modell
  - Minute 2: Tree → Wall Süd → Inspector → U-Wert 1.2!
  - Minute 3: Katalog → WDVS 160mm → U-Wert 0.21
  - Minute 4: Szenario "Sanierung" → Wände grün → -43%
  - Minute 5: Vergleich + Ausblick
- [ ] **Backup-Video** (falls Live-Demo ausfällt)
- [ ] **GitHub Pages Deployment:**
  - `https://dweberatunggmbh.github.io/din18599-ifc`
- [ ] **Präsentations-Slides** (Konzept, USP, Roadmap)

**Output:** Präsentation READY ✅

---

## 📦 Dependencies (package.json)

```json
{
  "dependencies": {
    "react": "^18",
    "typescript": "^5",
    "@react-three/fiber": "^8",
    "@react-three/drei": "^9",
    "@react-three/postprocessing": "^2",
    "three": "^0.160",
    "zustand": "^4",
    "zod": "^3",
    "web-ifc": "^0.0.51",
    "lucide-react": "latest",
    "tailwindcss": "^3",
    "@radix-ui/react-dropdown-menu": "latest"
  }
}
```

---

## 🎯 Erfolgs-Kriterien (Berlin-Präsentation)

| Kriterium | Muss | Sollte |
|-----------|------|--------|
| 3D-Modell lädt | ✅ Must | |
| Tree-Navigation (↔ 3D) | ✅ Must | |
| Inspector mit U-Wert | ✅ Must | |
| Katalog-Browser | ✅ Must | |
| Szenario-Wechsel | ✅ Must | |
| Energiekennwerte | ✅ Must | |
| Html-Labels (Hover) | | ✅ Should |
| Vergleichs-Tabelle | | ✅ Should |
| Section Cut | | ⏳ Nice |
| IFC-Import | | ⏳ Q3 2026 |

---

## 📚 Referenzen

- **Entscheidung:** `docs/VIEWER_DECISION.md`
- **Brainstorm:** `docs/brainstorms/20260331_phase3_viewer_mvp.md`
- **Schema:** `schema/v2.1-complete.json`
- **Merge-Algorithmus:** `docs/MERGE_ALGORITHM.md`
- **Katalog:** `catalog/`
- **Bestehender Viewer:** `viewer/3d-viewer.html` (Migration-Basis)

---

**Erstellt:** 31. März 2026  
**Status:** READY TO IMPLEMENT 🚀
