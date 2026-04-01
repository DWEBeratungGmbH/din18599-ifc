# DIN 18599 JSON Schema v2.1 - Final Specification

> **Version:** 2.1  
> **Datum:** 2026-04-01  
> **Status:** Implementiert  
> **Autor:** DWE Beratung GmbH

---

## 🎯 Überblick

Das DIN 18599 JSON Schema v2.1 ist ein **offener Standard** für die Speicherung und den Austausch von energetischen Gebäudedaten nach DIN V 18599.

### **Kern-Features v2.1:**

1. ✅ **Parent-Child Beziehungen** - Eindeutige Zuordnung von Fenstern/Türen zu Wänden
2. ✅ **Solargewinne** - Opake (`solar_absorption`) und transparente (`shading_factor_fs`) Bauteile
3. ✅ **Wärmebrücken-Typ** - Dokumentation der Berechnungsgenauigkeit
4. ✅ **B' für Fx-Faktor** - Charakteristische Dimension für erdberührte Bauteile
5. ✅ **BuildingElement** - Add-On für LOD 300+ (Treppen, Gauben, Anbauten)
6. ✅ **Maßnahmen mit Kosten** - Wirtschaftlichkeitsberechnung
7. ✅ **Szenario-Output** - Einsparungen und Vergleiche

---

## 📊 Datenmodell-Hierarchie

```
DIN18599Data
├── meta                          # Metadaten
├── input                         # Definition (Source of Truth)
│   ├── building                  # Gebäudedaten
│   ├── zones[]                   # Thermische Zonen
│   ├── envelope                  # Gebäudehülle
│   │   ├── walls_external[]      # Außenwände
│   │   ├── walls_internal[]      # Innenwände
│   │   ├── roofs[]               # Dächer
│   │   ├── floors[]              # Böden/Decken
│   │   └── openings[]            # Fenster, Türen, etc.
│   ├── systems[]                 # Anlagentechnik
│   └── building_elements[]       # Add-On für LOD 300+ (Treppen, Gauben)
├── output                        # Berechnungsergebnisse
│   ├── energy_balance            # Energiebilanz
│   ├── indicators                # Kennwerte
│   └── sectors                   # Sektoren
└── scenarios[]                   # Sanierungsszenarien
    ├── measures[]                # Maßnahmen
    ├── building_elements[]       # Neue Elemente (Gaube, Anbau)
    ├── delta                     # Änderungen
    └── output                    # Berechnete Ergebnisse
```

---

## 🔧 Änderungen v2.0 → v2.1

### **1. Parent-Child Beziehungen**

**Problem v2.0:**
- Fenster nur über `orientation` zugeordnet
- Bei mehreren Wänden gleicher Orientierung nicht eindeutig

**Lösung v2.1:**
```typescript
interface Opening {
  parent_element_id: string      // z.B. "wall_sued"
  parent_element_type: string    // z.B. "WALL_EXT", "ROOF"
}
```

**Beispiel:**
```json
{
  "id": "window_sued_1",
  "type": "WINDOW",
  "parent_element_id": "wall_sued",
  "parent_element_type": "WALL_EXT",
  "area": 6.0
}
```

---

### **2. Solargewinne**

**Opake Bauteile:**
```typescript
interface Wall/Roof {
  solar_absorption?: number      // α (0.3=hell, 0.6=mittel, 0.9=dunkel)
}
```

**Transparente Bauteile:**
```typescript
interface Opening {
  shading_factor_fs?: number     // Verschattung (1.0 = keine)
  horizon_angle?: number         // Detailliert (optional)
  overhang_angle?: number        // Detailliert (optional)
}
```

**Wichtigkeit:** ~5-10% der Solargewinne fehlen ohne diese Felder

---

### **3. Wärmebrücken-Typ**

```typescript
type ThermalBridgeType = 'DEFAULT' | 'REDUCED' | 'DETAILED'

interface Wall/Roof/Floor {
  thermal_bridge_type?: ThermalBridgeType
}
```

**Bedeutung:**
- `DEFAULT`: Pauschale Zuschläge (ΔU = 0.10-0.15 W/(m²K))
- `REDUCED`: Reduzierte Zuschläge bei guter Ausführung (ΔU = 0.05 W/(m²K))
- `DETAILED`: Detaillierte Berechnung nach DIN EN ISO 10211

---

### **4. B' für Fx-Faktor**

```typescript
interface Floor {
  perimeter?: number                    // Umfang P (m)
  characteristic_dimension_b?: number   // B' = A / (0.5 × P)
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

### **5. BuildingElement (NEU - Add-On für LOD 300+)**

**Konzept:** Einheitliches System für Treppen, Gauben, Anbauten, Schächte

```typescript
interface BuildingElement {
  id: string
  type: 'STAIR' | 'DORMER' | 'EXTENSION' | 'BAY_WINDOW' | 'SHAFT'
  source: 'IFC' | 'CORRECTION' | 'MANUAL'
  
  // Effekt auf Zonen
  affects_zones: {
    zone_id: string
    area_delta: number         // + oder -
    volume_delta: number
  }[]
  
  // Effekt auf Bauteile
  affects_elements?: {
    element_id: string
    area_delta: number
  }[]
  
  // Komponenten (für Gaube)
  components?: {
    type: 'WALL' | 'ROOF' | 'WINDOW' | 'DOOR'
    area: number
    u_value?: number
  }[]
}
```

**Beispiel: Treppe**
```json
{
  "id": "stair_keller_eg",
  "type": "STAIR",
  "source": "CORRECTION",
  "affects_zones": [
    { "zone_id": "zone_wohnen", "area_delta": -4.0, "volume_delta": -10.0 }
  ],
  "affects_elements": [
    { "element_id": "floor_keller", "area_delta": -4.0 }
  ],
  "thermal": {
    "is_inside_envelope": false,
    "u_value": 0.25
  }
}
```

**Beispiel: Gaube (in Szenario)**
```json
{
  "id": "dormer_sued",
  "type": "DORMER",
  "source": "CORRECTION",
  "affects_zones": [
    { "zone_id": "zone_dg", "area_delta": 1.8, "volume_delta": 3.6 }
  ],
  "affects_elements": [
    { "element_id": "roof_main", "area_delta": -1.8 }
  ],
  "components": [
    { "type": "WALL", "area": 3.0, "u_value": 0.20 },
    { "type": "WINDOW", "area": 1.2, "u_value": 0.95 },
    { "type": "ROOF", "area": 1.8, "u_value": 0.14 }
  ]
}
```

**Vorteil:** Original-Daten bleiben unverändert (Correction Layer)

---

### **6. Maßnahmen mit Kosten**

```typescript
interface Measure {
  id: string
  type: MeasureType
  name: string
  description: string
  
  affected_elements?: string[]
  
  // NEU: Kosten
  cost_estimate?: number            // Investitionskosten (€)
  cost_annual_savings?: number      // Jährliche Einsparung (€)
  payback_period_years?: number     // Amortisationszeit
  
  // NEU: Förderung
  funding_eligible?: boolean
  funding_program?: string          // z.B. "BEG EM"
  funding_amount?: number
  
  // Referenz zu BuildingElements
  building_element_ids?: string[]
}
```

---

### **7. Szenario-Output mit Einsparungen**

```typescript
interface ScenarioOutput extends Output {
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
```

---

## 📋 Vollständige Type-Definitionen

Siehe: `/opt/din18599-ifc/viewer/src/store/viewer.store.ts`

---

## 🔄 Delta-Merge Algorithmus

**Prinzip:** Szenarien ändern nur die betroffenen Felder, der Rest bleibt gleich.

```typescript
function applyScenario(base: DIN18599Data, scenario: Scenario): DIN18599Data {
  // 1. Deep-Clone
  const result = JSON.parse(JSON.stringify(base))
  
  // 2. Delta-Merge (nur geänderte Felder)
  result.input = deepMerge(result.input, scenario.delta.input)
  
  // 3. Building Elements anwenden
  if (scenario.building_elements) {
    result = applyBuildingElements(result, scenario.building_elements)
  }
  
  // 4. Output überschreiben
  if (scenario.output) {
    result.output = scenario.output
  }
  
  return result
}
```

---

## ✅ Validierung

### **Pflichtfelder nach DIN V 18599:**

**Zonen:**
- ✅ `area_an` (Nutzfläche)
- ✅ `volume` (Volumen)
- ✅ `is_heated` (Beheizt ja/nein)

**Wände:**
- ✅ `area` (Brutto-Fläche)
- ✅ `u_value_undisturbed` (U-Wert)
- ✅ `thermal_bridge_delta_u` (Wärmebrücken-Zuschlag)
- ✅ `orientation` (Ausrichtung)
- ✅ `solar_absorption` (v2.1: Solargewinne)

**Fenster:**
- ✅ `parent_element_id` (v2.1: Zuordnung)
- ✅ `area` (Fläche)
- ✅ `u_value_glass` (U-Wert Glas)
- ✅ `g_value` (Gesamtenergiedurchlassgrad)
- ✅ `shading_factor_fs` (v2.1: Verschattung)

**Böden:**
- ✅ `area` (Fläche)
- ✅ `u_value_undisturbed` (U-Wert)
- ✅ `perimeter` (v2.1: für Fx-Faktor)
- ✅ `characteristic_dimension_b` (v2.1: B')

---

## 🎯 LOD-Stufen

| LOD | Beschreibung | Erforderliche Felder | Building Elements |
|-----|--------------|----------------------|-------------------|
| **100** | Konzept | Zonen, Flächen, U-Werte | ❌ Nicht erforderlich |
| **200** | Entwurf | + Orientierung, Solargewinne | ❌ Nicht erforderlich |
| **300** | Ausführung | + Parent-Child, B', Wärmebrücken-Typ | ✅ **Erforderlich** (iSFP, KfW) |
| **400** | Bestand | + Schichtaufbau, IFC-Referenzen | ✅ **Erforderlich** |

**Hinweis:** `building_elements[]` ist ein **Add-On für LOD 300+** und für iSFP sowie KfW-Sanierungen **Pflicht**.

---

## 📚 Beispiele

### **Minimal (LOD 100):**
```json
{
  "meta": { "schema_version": "2.1" },
  "input": {
    "zones": [{ "id": "z1", "area_an": 100, "volume": 250, "is_heated": true }],
    "envelope": {
      "walls_external": [{ "id": "w1", "area": 40, "u_value_undisturbed": 1.2 }]
    }
  }
}
```

### **Vollständig (LOD 300):**
Siehe: `/opt/din18599-ifc/viewer/public/demo/efh-demo.din18599.json`

---

## 🔗 Referenzen

- **DIN V 18599-1:** Allgemeine Bilanzierungsverfahren
- **DIN V 18599-2:** Nutzenergiebedarf Heizen/Kühlen
- **Leitfaden DIN V 18599 (2023):** Kapitel 6 (Thermische Hüllfläche)
- **IFC4:** Industry Foundation Classes
- **gbXML:** Green Building XML Schema

---

## 📝 Änderungshistorie

| Version | Datum | Änderungen |
|---------|-------|------------|
| **2.1** | 2026-04-01 | Parent-Child, Solargewinne, BuildingElement, Maßnahmen |
| **2.0** | 2026-03-31 | Initial Release |

---

## 📄 Lizenz

**MIT License** - Open Source Standard für energetische Gebäudedaten

---

**Implementierung:**
- TypeScript Types: `/opt/din18599-ifc/viewer/src/store/viewer.store.ts`
- Demo-JSON: `/opt/din18599-ifc/viewer/public/demo/efh-demo.din18599.json`
- GitHub: https://github.com/DWEBeratungGmbH/din18599-ifc
