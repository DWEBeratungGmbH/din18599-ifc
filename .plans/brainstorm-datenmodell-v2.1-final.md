# Brainstorm: DIN 18599 JSON Schema v2.1 Final

> **Datum:** 2026-03-31  
> **Ziel:** Vollständiges, normkonformes Datenmodell  
> **Scope:** Alle kritischen Felder für energetische Bilanzierung

---

## 🎯 Vision

**Ein Datenmodell, das:**
1. ✅ **Normkonform** ist (DIN V 18599)
2. ✅ **Vollständig** ist (alle Pflichtfelder)
3. ✅ **Hierarchisch** ist (klare Parent-Child-Beziehungen)
4. ✅ **Szenario-fähig** ist (Delta-Merge + Output)
5. ✅ **Viewer-ready** ist (3D-Darstellung möglich)
6. ✅ **Berechnungs-ready** ist (alle Parameter für Kernel)

---

## 📊 Datenmodell-Hierarchie

```
DIN18599Data
├── meta (Metadaten)
├── input (Definition)
│   ├── building (Gebäude)
│   ├── zones[] (Zonen)
│   ├── envelope (Hülle)
│   │   ├── walls_external[] (Außenwände)
│   │   ├── walls_internal[] (Innenwände)
│   │   ├── roofs[] (Dächer)
│   │   ├── floors[] (Böden/Decken)
│   │   ├── windows[] (Fenster) ← PARENT-CHILD zu Wänden!
│   │   └── doors[] (Türen) ← NEU!
│   └── systems[] (Anlagentechnik)
├── output (Ergebnisse)
│   ├── energy_balance (Energiebilanz)
│   ├── indicators (Kennwerte)
│   └── sectors (Sektoren)
└── scenarios[] (Szenarien)
    ├── measures[] (Maßnahmen) ← NEU!
    ├── delta (Änderungen)
    └── output (Berechnete Ergebnisse) ← NEU!
```

---

## 🔧 Kritische Änderungen

### 1. **Fenster → Wand Zuordnung**

**Problem:**
- Aktuell: Zuordnung nur über `orientation`
- Bei mehreren Wänden gleicher Orientierung nicht eindeutig

**Lösung:**
```typescript
interface Window {
  id: string
  ifc_guid?: string
  name: string
  
  // ← NEU: Parent-Child Beziehung
  parent_element_id: string        // z.B. "wall_sued"
  parent_element_type: "wall" | "roof" | "door"
  
  // Geometrie
  orientation: number               // Redundant, aber für Plausibilität
  area: number
  
  // Thermische Eigenschaften
  u_value_glass: number
  u_value_frame: number
  psi_spacer: number
  g_value: number
  frame_fraction: number
  
  // ← NEU: Solargewinne
  shading_factor_fs?: number        // Pauschal (1.0 = keine Verschattung)
  horizon_angle?: number            // Detailliert (optional)
  overhang_angle?: number           // Detailliert (optional)
  
  // Katalog
  window_type_catalog_ref?: string
}
```

**Vorteile:**
- ✅ Eindeutige Zuordnung
- ✅ Mehrere Wände gleicher Orientierung möglich
- ✅ Hierarchie klar (für Tree-View)
- ✅ Türen können auch Fenster haben (Glaselement)

---

### 2. **Wände: Solargewinne + Wärmebrücken**

```typescript
interface WallExternal {
  id: string
  ifc_guid?: string
  name: string
  
  // Geometrie
  boundary_condition: "EXTERNAL" | "GROUND" | "UNHEATED" | "HEATED"
  orientation: number
  inclination?: number              // ← NEU: 90=vertikal, 0=horizontal
  area: number                      // Brutto-Fläche (inkl. Fenster)
  
  // Thermische Eigenschaften
  u_value_undisturbed: number
  thermal_bridge_delta_u: number
  thermal_bridge_type?: "DEFAULT" | "REDUCED" | "DETAILED"  // ← NEU
  
  // ← NEU: Solargewinne
  solar_absorption: number          // α (0.3=hell, 0.6=mittel, 0.9=dunkel)
  
  // Katalog
  construction_catalog_ref?: string
  layer_structure?: LayerStructure  // Optional: Schichtaufbau
}
```

**Wichtigkeit:**
- **Solargewinne opak:** Q_s = A × α × I_sol × F_sh
- Ohne `solar_absorption` fehlen ~5-10% der Gewinne
- Ohne `thermal_bridge_type` ist Genauigkeit unklar

---

### 3. **Dächer: Wie Wände**

```typescript
interface Roof {
  id: string
  ifc_guid?: string
  name: string
  
  boundary_condition: "EXTERNAL" | "UNHEATED"
  orientation: number               // Für Satteldach: Süd/Nord
  inclination: number               // Dachneigung (35°)
  area: number
  
  u_value_undisturbed: number
  thermal_bridge_delta_u: number
  thermal_bridge_type?: "DEFAULT" | "REDUCED" | "DETAILED"
  
  solar_absorption: number          // ← NEU: Wichtig für Dachgewinne!
  
  construction_catalog_ref?: string
}
```

---

### 4. **Böden: B' für Fx-Faktor**

```typescript
interface Floor {
  id: string
  ifc_guid?: string
  name: string
  
  boundary_condition: "GROUND" | "UNHEATED" | "EXTERNAL"
  area: number
  
  // ← NEU: Für Fx-Faktor Berechnung
  perimeter?: number                // Umfang P (m)
  characteristic_dimension_b?: number  // B' = A / (0.5 × P)
  
  u_value_undisturbed: number
  thermal_bridge_delta_u: number
  
  construction_catalog_ref?: string
}
```

**Berechnung:**
```
B' = A_floor / (0.5 × P)

Fx = f(B', boundary_condition)
  - GROUND: Tabelle 3, DIN V 18599-2
  - UNHEATED: Tabelle 4, DIN V 18599-2

Q_T = A × U × Fx × ΔT
```

---

### 5. **Türen als eigener Typ**

```typescript
interface Door {
  id: string
  ifc_guid?: string
  name: string
  
  parent_element_id: string         // Wand, in der die Tür ist
  parent_element_type: "wall"
  
  orientation: number
  area: number
  
  u_value: number                   // U-Wert der Tür
  
  // Optional: Glaselement in Tür
  has_glazing: boolean
  glazing_area?: number
  glazing_u_value?: number
  glazing_g_value?: number
  
  door_type_catalog_ref?: string
}
```

**Wichtigkeit:**
- Türen haben andere U-Werte als Wände
- Türen mit Glas haben Solargewinne
- Türen müssen von Wandfläche abgezogen werden

---

### 6. **Szenarien: Vollständig**

```typescript
interface Scenario {
  id: string
  name: string
  description: string
  
  // ← NEU: Maßnahmen-Liste
  measures: Measure[]
  
  // Delta-Merge (Änderungen)
  delta: {
    input: Partial<InputData>       // Nur geänderte Felder
  }
  
  // ← NEU: Berechnete Ergebnisse
  output?: {
    energy_balance: EnergyBalance
    indicators: Indicators
    sectors: Sectors
    
    // ← NEU: Einsparungen
    savings?: {
      final_energy_kwh_a: number
      final_energy_percent: number
      primary_energy_kwh_a: number
      primary_energy_percent: number
      co2_kg_a: number
      co2_percent: number
      cost_annual_eur: number
    }
  }
}

interface Measure {
  id: string
  type: MeasureType                 // INSULATION_FACADE, WINDOW_REPLACEMENT, ...
  name: string
  description: string
  
  affected_elements: string[]       // IDs der betroffenen Bauteile
  
  // ← NEU: Kosten
  cost_estimate?: number            // Investitionskosten (€)
  cost_annual_savings?: number      // Jährliche Einsparung (€)
  payback_period_years?: number     // Amortisationszeit
  
  // ← NEU: Förderung
  funding_eligible?: boolean
  funding_program?: string          // z.B. "BEG EM"
  funding_amount?: number
}

type MeasureType = 
  | "INSULATION_FACADE"             // WDVS
  | "INSULATION_ROOF"               // Dachdämmung
  | "INSULATION_FLOOR"              // Kellerdämmung
  | "WINDOW_REPLACEMENT"            // Fenstertausch
  | "DOOR_REPLACEMENT"              // Türtausch
  | "HEATING_REPLACEMENT"           // Heizungstausch
  | "VENTILATION_INSTALLATION"      // Lüftungsanlage
  | "SOLAR_THERMAL"                 // Solarthermie
  | "PHOTOVOLTAIC"                  // PV-Anlage
```

**Wichtigkeit:**
- **Maßnahmen** sind die Grundlage für Sanierungsfahrplan
- **Kosten** sind wichtig für Wirtschaftlichkeit
- **Förderung** ist wichtig für Beratung
- **Output** zeigt Verbesserung direkt

---

## 🔄 Delta-Merge Algorithmus

**Prinzip:**
```typescript
function applyScenario(base: DIN18599Data, scenario: Scenario): DIN18599Data {
  // 1. Deep-Clone von base
  const result = JSON.parse(JSON.stringify(base))
  
  // 2. Merge delta.input (nur geänderte Felder)
  result.input = deepMerge(result.input, scenario.delta.input)
  
  // 3. Überschreibe output mit Szenario-Output (falls vorhanden)
  if (scenario.output) {
    result.output = scenario.output
  }
  
  return result
}

function deepMerge(target: any, source: any): any {
  // Arrays: Merge by ID
  if (Array.isArray(target) && Array.isArray(source)) {
    return target.map(item => {
      const update = source.find(s => s.id === item.id)
      return update ? { ...item, ...update } : item
    })
  }
  
  // Objects: Recursive merge
  if (typeof target === 'object' && typeof source === 'object') {
    const result = { ...target }
    for (const key in source) {
      result[key] = deepMerge(target[key], source[key])
    }
    return result
  }
  
  // Primitives: Overwrite
  return source
}
```

**Beispiel:**
```json
// Base
{
  "input": {
    "envelope": {
      "walls_external": [
        { "id": "wall_sued", "u_value_undisturbed": 1.2 }
      ]
    }
  }
}

// Scenario Delta
{
  "delta": {
    "input": {
      "envelope": {
        "walls_external": [
          { "id": "wall_sued", "u_value_undisturbed": 0.21 }
        ]
      }
    }
  }
}

// Result (nach Merge)
{
  "input": {
    "envelope": {
      "walls_external": [
        { "id": "wall_sued", "u_value_undisturbed": 0.21 }  // ← Überschrieben
      ]
    }
  }
}
```

---

## 📋 Implementierungs-Reihenfolge

### **Phase 1: Datenmodell erweitern (1h)**

1. **TypeScript Types aktualisieren** (`/viewer/src/types/din18599.ts`)
   - Window: `parent_element_id`, `shading_factor_fs`
   - Wall: `solar_absorption`, `thermal_bridge_type`, `inclination`
   - Roof: `solar_absorption`
   - Floor: `perimeter`, `characteristic_dimension_b`
   - Door: Neuer Typ
   - Scenario: `measures[]`, `output`

2. **Demo-JSON aktualisieren** (`/viewer/public/demo/efh-demo.din18599.json`)
   - Alle neuen Felder mit realistischen Werten
   - Szenario mit vollständigem Output
   - Maßnahmen-Beschreibungen

### **Phase 2: Viewer anpassen (30 Min)**

3. **Store erweitern** (`/viewer/src/store/viewer.store.ts`)
   - Neue Felder in Types
   - Delta-Merge Funktion
   - Szenario-Switcher State

4. **Sidebar anpassen** (`/viewer/src/App.tsx`)
   - Türen anzeigen (unter Wänden)
   - Neue Felder in Inspector

### **Phase 3: Szenario-Switcher UI (1h)**

5. **Szenario-Switcher Komponente**
   - Dropdown/Tabs für Szenarien
   - Vergleichs-Tabelle (Vorher/Nachher)
   - Maßnahmen-Liste
   - Kosten/Einsparungen

6. **3D-Viewer Updates**
   - Farbwechsel bei Szenario-Wechsel
   - Animationen (optional)

### **Phase 4: Dokumentation (15 Min)**

7. **Schema dokumentieren**
   - PARAMETER_MATRIX.md aktualisieren
   - Beispiele hinzufügen

---

## ✅ Erfolgs-Kriterien

- [ ] Alle Pflichtfelder nach DIN V 18599 vorhanden
- [ ] Fenster/Türen eindeutig Wänden zugeordnet
- [ ] Solargewinne berechenbar (opak + transparent)
- [ ] Wärmebrücken-Typ definiert
- [ ] Bodenplatte mit B' für Fx-Faktor
- [ ] Szenarien mit vollständigem Output
- [ ] Maßnahmen mit Kosten/Förderung
- [ ] Delta-Merge Algorithmus funktioniert
- [ ] Viewer zeigt alle neuen Felder
- [ ] Szenario-Switcher funktioniert

---

## 🎯 Demo-Szenario (Berlin-Präsentation)

**Base: EFH 1978 (Bestand)**
- Außenwände: U=1.2 W/(m²K), α=0.6 (mittel)
- Fenster: Ug=2.8 W/(m²K) (Zweifach alt)
- Dach: U=0.8 W/(m²K), α=0.6
- Endenergie: 28.500 kWh/a
- Effizienzklasse: F

**Szenario 1: WDVS + Fenster**
- Maßnahme 1: WDVS 160mm EPS 035 → U=0.21 W/(m²K)
- Maßnahme 2: Dreifachverglasung → Ug=1.0 W/(m²K)
- Kosten: 26.000 € (18k WDVS + 8k Fenster)
- Förderung: BEG EM 20% = 5.200 €
- Endenergie: 12.500 kWh/a (-56%)
- Effizienzklasse: C
- Einsparung: 1.600 €/a
- Amortisation: 13 Jahre

**Szenario 2: Vollsanierung (WDVS + Fenster + Dach + Heizung)**
- Zusätzlich: Dachdämmung + Wärmepumpe
- Kosten: 55.000 €
- Förderung: BEG EM 35% = 19.250 €
- Endenergie: 6.500 kWh/a (-77%)
- Effizienzklasse: A+
- Einsparung: 2.200 €/a
- Amortisation: 16 Jahre

---

## 📚 Referenzen

- DIN V 18599-1: Allgemeine Bilanzierungsverfahren
- DIN V 18599-2: Nutzenergiebedarf Heizen/Kühlen
- Leitfaden DIN V 18599 (2023), Kapitel 6
- `/docs/PARAMETER_MATRIX.md`

---

**Nächster Schritt:** TypeScript Types erstellen
