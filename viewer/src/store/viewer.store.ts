import { create } from 'zustand'

// ============================================================================
// DIN 18599 JSON Schema v2.1 - TypeScript Types
// ============================================================================

// ── Meta ────────────────────────────────────────────────────────────────────

export interface Meta {
  schema_version: string
  project_name: string
  project_id: string
  software_name: string
  software_version: string
  norm_version: string
  calculation_date: string
  created_by?: string
  last_modified?: string
}

// ── Building ────────────────────────────────────────────────────────────────

export interface Building {
  name: string
  address?: string
  construction_year?: number
  building_type?: string
  num_floors?: number
  num_units?: number
}

// ── Zones ───────────────────────────────────────────────────────────────────

export interface Zone {
  id: string
  name: string
  type?: 'LIVING' | 'OFFICE' | 'STAIRCASE' | 'CORRIDOR' | 'BASEMENT'
  is_heated: boolean
  
  // Geometrie
  area_an: number              // Nutzfläche (m²)
  volume: number               // Volumen (m³)
  clear_height?: number        // Lichte Höhe (m)
  
  // Nutzung
  usage_profile?: string
  internal_gains?: number      // W/m²
  
  // Lüftung
  air_change_rate?: number     // 1/h
  
  // IFC-Referenz
  ifc_guid?: string
}

// ── Envelope: Walls ─────────────────────────────────────────────────────────

export type BoundaryCondition = 'EXTERNAL' | 'GROUND' | 'UNHEATED' | 'HEATED'
export type ThermalBridgeType = 'DEFAULT' | 'REDUCED' | 'DETAILED'

export interface WallExternal {
  id: string
  name: string
  ifc_guid?: string
  
  // Geometrie
  boundary_condition: BoundaryCondition
  orientation: number          // Azimut (0=Nord, 90=Ost, 180=Süd, 270=West)
  inclination?: number         // Neigung (90=vertikal, 0=horizontal)
  area: number                 // Brutto-Fläche (inkl. Fenster/Türen)
  
  // Thermische Eigenschaften
  u_value_undisturbed: number  // W/(m²K)
  thermal_bridge_delta_u: number
  thermal_bridge_type?: ThermalBridgeType  // v2.1: NEU
  
  // v2.1: NEU - Solargewinne
  solar_absorption?: number    // α (0.3=hell, 0.6=mittel, 0.9=dunkel)
  
  // Katalog
  construction_catalog_ref?: string
  layer_structure?: LayerStructure
}

export interface WallInternal {
  id: string
  name: string
  ifc_guid?: string
  
  boundary_condition: 'UNHEATED' | 'HEATED'
  area: number
  u_value_undisturbed: number
  thermal_bridge_delta_u: number
  
  construction_catalog_ref?: string
}

// ── Envelope: Roofs ─────────────────────────────────────────────────────────

export interface Roof {
  id: string
  name: string
  ifc_guid?: string
  
  boundary_condition: 'EXTERNAL' | 'UNHEATED'
  orientation: number
  inclination: number          // Dachneigung (Grad)
  area: number
  
  u_value_undisturbed: number
  thermal_bridge_delta_u: number
  thermal_bridge_type?: ThermalBridgeType
  
  // v2.1: NEU - Solargewinne
  solar_absorption?: number
  
  construction_catalog_ref?: string
  layer_structure?: LayerStructure
}

// ── Envelope: Floors/Slabs ──────────────────────────────────────────────────

export interface Floor {
  id: string
  name: string
  ifc_guid?: string
  
  boundary_condition: BoundaryCondition
  area: number
  
  // v2.1: NEU - Für Fx-Faktor Berechnung
  perimeter?: number                    // Umfang P (m)
  characteristic_dimension_b?: number   // B' = A / (0.5 × P)
  
  u_value_undisturbed: number
  thermal_bridge_delta_u: number
  
  construction_catalog_ref?: string
}

// ── Envelope: Openings ──────────────────────────────────────────────────────

export type OpeningType = 'WINDOW' | 'DOOR' | 'SKYLIGHT' | 'OPENING' | 'NICHE' | 'HATCH'
export type ParentElementType = 'WALL_EXT' | 'WALL_INT' | 'ROOF' | 'SLAB_FLR' | 'SLAB_CLG' | 'DOOR'

export interface Opening {
  id: string
  name: string
  type: OpeningType
  ifc_guid?: string
  
  // v2.1: NEU - Parent-Child Beziehung
  parent_element_id: string
  parent_element_type: ParentElementType
  
  // Geometrie
  orientation?: number
  area: number
  
  // Thermische Eigenschaften (je nach Typ)
  u_value?: number             // Für Türen, Gesamt-U-Wert
  u_value_glass?: number       // Für Fenster
  u_value_frame?: number       // Für Fenster
  psi_spacer?: number          // Für Fenster
  g_value?: number             // Für Fenster/Glas
  frame_fraction?: number      // Für Fenster
  
  // v2.1: NEU - Solargewinne/Verschattung
  shading_factor_fs?: number   // Pauschal (1.0 = keine Verschattung)
  horizon_angle?: number       // Detailliert (optional)
  overhang_angle?: number      // Detailliert (optional)
  
  // Katalog
  catalog_ref?: string
  
  // Source (für BuildingElement)
  source?: 'IFC' | 'CORRECTION' | 'MANUAL' | 'BUILDING_ELEMENT'
}

// ── Layer Structure (optional) ──────────────────────────────────────────────

export interface LayerStructure {
  layers: Layer[]
}

export interface Layer {
  material: string
  thickness: number            // m
  lambda: number               // W/(mK)
}

// ── Systems ─────────────────────────────────────────────────────────────────

export interface System {
  id: string
  type: 'HEATING' | 'COOLING' | 'VENTILATION' | 'DHW' | 'LIGHTING'
  name: string
  // ... weitere Felder je nach Typ
}

// ── Building Elements (v2.1: NEU - Add-On für LOD 300+) ────────────────────

export type BuildingElementType = 'STAIR' | 'DORMER' | 'EXTENSION' | 'BAY_WINDOW' | 'SHAFT'
export type BuildingElementSource = 'IFC' | 'CORRECTION' | 'MANUAL'

export interface BuildingElement {
  id: string
  type: BuildingElementType
  name: string
  source: BuildingElementSource
  
  // IFC-Referenz (falls vorhanden)
  ifc_reference?: {
    guid: string
    entity_type: string        // z.B. "IfcStair", "IfcRoof"
    file?: string
  }
  
  // Geometrie
  geometry: {
    location?: [number, number, number]  // [x, y, z]
    dimensions: {
      width?: number
      depth?: number
      height?: number
      area?: number
      volume?: number
    }
  }
  
  // Effekt auf Zonen (automatisch berechnet)
  affects_zones: {
    zone_id: string
    area_delta: number         // + oder -
    volume_delta: number       // + oder -
  }[]
  
  // Effekt auf Bauteile (optional)
  affects_elements?: {
    element_id: string         // z.B. "slab_og", "roof_main"
    element_type: string       // z.B. "SLAB_FLR", "ROOF"
    area_delta: number         // z.B. -4.0 (Treppenloch)
  }[]
  
  // Thermische Eigenschaften (falls relevant)
  thermal?: {
    is_inside_envelope: boolean
    boundary_condition?: string
    u_value?: number
  }
  
  // Komponenten (für komplexe Elemente wie Gaube)
  components?: BuildingElementComponent[]
  
  // Beschreibung
  description?: string
  reason?: string              // Warum wurde dieses Element hinzugefügt?
}

export interface BuildingElementComponent {
  id: string
  type: 'WALL' | 'ROOF' | 'WINDOW' | 'DOOR'
  area: number
  u_value?: number
  g_value?: number
  solar_absorption?: number
}

// ── Output ──────────────────────────────────────────────────────────────────

export interface Output {
  energy_balance: EnergyBalance
  indicators: Indicators
  sectors?: Sectors
}

export interface EnergyBalance {
  final_energy_kwh_a: number
  primary_energy_kwh_a: number
  co2_emissions_kg_a?: number
  
  // Detailliert
  heating_demand_kwh_a?: number
  cooling_demand_kwh_a?: number
  dhw_demand_kwh_a?: number
  lighting_demand_kwh_a?: number
  ventilation_demand_kwh_a?: number
}

export interface Indicators {
  efficiency_class: string     // A+ bis H
  specific_final_energy?: number
  specific_primary_energy?: number
}

export interface Sectors {
  heating?: number
  cooling?: number
  dhw?: number
  lighting?: number
  ventilation?: number
}

// ── Scenarios ───────────────────────────────────────────────────────────────

export type MeasureType = 
  | 'INSULATION_FACADE'
  | 'INSULATION_ROOF'
  | 'INSULATION_FLOOR'
  | 'WINDOW_REPLACEMENT'
  | 'DOOR_REPLACEMENT'
  | 'HEATING_REPLACEMENT'
  | 'VENTILATION_INSTALLATION'
  | 'SOLAR_THERMAL'
  | 'PHOTOVOLTAIC'
  | 'DORMER'
  | 'EXTENSION'
  | 'ROOF_EXTENSION'

export interface Scenario {
  id: string
  name: string
  description: string
  
  // v2.1: NEU - Maßnahmen
  measures?: Measure[]
  
  // v2.1: NEU - Building Elements (Add-On für LOD 300+)
  building_elements?: BuildingElement[]
  
  // Delta-Merge (Änderungen)
  delta: {
    input?: Partial<InputData>
  }
  
  // v2.1: NEU - Berechnete Ergebnisse
  output?: ScenarioOutput
}

export interface Measure {
  id: string
  type: MeasureType
  name: string
  description: string
  
  // Betroffene Elemente
  affected_elements?: string[]
  
  // v2.1: NEU - Kosten
  cost_estimate?: number            // Investitionskosten (€)
  cost_annual_savings?: number      // Jährliche Einsparung (€)
  payback_period_years?: number     // Amortisationszeit
  
  // v2.1: NEU - Förderung
  funding_eligible?: boolean
  funding_program?: string          // z.B. "BEG EM"
  funding_amount?: number
  
  // Referenz zu BuildingElements (falls relevant)
  building_element_ids?: string[]
}

export interface ScenarioOutput extends Output {
  // v2.1: NEU - Einsparungen
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

// ── Input Data ──────────────────────────────────────────────────────────────

export interface InputData {
  building?: Building
  zones?: Zone[]
  envelope?: {
    walls_external?: WallExternal[]
    walls_internal?: WallInternal[]
    roofs?: Roof[]
    floors?: Floor[]
    openings?: Opening[]         // v2.1: Vereinheitlicht (windows, doors, etc.)
  }
  systems?: System[]
  
  // v2.1: NEU - Building Elements (Add-On für LOD 300+)
  building_elements?: BuildingElement[]
}

// ── Main Data Structure ─────────────────────────────────────────────────────

export interface DIN18599Data {
  meta: Meta
  input: InputData
  output?: Output
  scenarios?: Scenario[]
}

interface ViewerState {
  // Data
  project: DIN18599Data | null
  activeScenario: string
  
  // UI State
  selectedId: string | null
  hoveredId: string | null
  buildingDataModalOpen: boolean
  
  // Editor State
  editMode: boolean
  
  // Actions
  loadProject: (data: DIN18599Data) => void
  selectElement: (id: string | null) => void
  setHoveredId: (id: string | null) => void
  switchScenario: (id: string) => void
  toggleEditMode: () => void
  openBuildingDataModal: () => void
  closeBuildingDataModal: () => void
  
  // Computed
  getCurrentData: () => DIN18599Data | null
}

export const useViewerStore = create<ViewerState>((set, get) => ({
  // Initial State
  project: null,
  activeScenario: 'base',
  selectedId: null,
  hoveredId: null,
  buildingDataModalOpen: false,
  editMode: false,
  
  // Actions
  loadProject: (data) => set({ project: data }),
  selectElement: (id) => set({ selectedId: id }),
  setHoveredId: (id) => set({ hoveredId: id }),
  switchScenario: (id) => set({ activeScenario: id }),
  toggleEditMode: () => set((state) => ({ editMode: !state.editMode })),
  openBuildingDataModal: () => set({ buildingDataModalOpen: true }),
  closeBuildingDataModal: () => set({ buildingDataModalOpen: false }),
  
  // Computed
  getCurrentData: () => {
    const state = get()
    if (!state.project) return null
    
    // Base Szenario
    if (state.activeScenario === 'base') {
      return state.project
    }
    
    // Szenario anwenden
    const scenario = state.project.scenarios?.find(s => s.id === state.activeScenario)
    if (!scenario) return state.project
    
    // Delta-Merge wird später mit applyScenario() implementiert
    // Für jetzt: Base-Daten zurückgeben
    return state.project
  },
}))
