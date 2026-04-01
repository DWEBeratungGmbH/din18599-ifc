import type { 
  DIN18599Data, 
  BuildingElement, 
  WallExternal, 
  Roof, 
  Floor,
  Opening,
  BuildingElementComponent
} from '../store/viewer.store'

/**
 * Wendet BuildingElements auf die Input-Daten an (Correction Layer)
 * 
 * BuildingElements modifizieren Flächen/Volumen ohne die Originaldaten zu ändern.
 * Beispiele: Treppen, Gauben, Anbauten
 */
export function applyBuildingElements(
  data: DIN18599Data,
  buildingElements: BuildingElement[]
): DIN18599Data {
  const result = structuredClone(data)

  for (const element of buildingElements) {
    // 1. Zonen-Anpassungen
    if (element.affects_zones && result.input.zones) {
      for (const zoneEffect of element.affects_zones) {
        const zone = result.input.zones.find(z => z.id === zoneEffect.zone_id)
        if (zone) {
          zone.area_an = (zone.area_an || 0) + zoneEffect.area_delta
          zone.volume = (zone.volume || 0) + zoneEffect.volume_delta
        }
      }
    }

    // 2. Bauteil-Anpassungen
    if (element.affects_elements && result.input.envelope) {
      for (const elementEffect of element.affects_elements) {
        const affectedElement = findElementById(
          result.input.envelope,
          elementEffect.element_id
        )
        if (affectedElement) {
          affectedElement.area = (affectedElement.area || 0) + elementEffect.area_delta
        }
      }
    }

    // 3. Komponenten zur Hülle hinzufügen (z.B. Gaube)
    if (element.components && result.input.envelope) {
      for (const component of element.components) {
        addComponentToEnvelope(result.input.envelope, component, element.id)
      }
    }
  }

  return result
}

/**
 * Findet ein Bauteil in der Envelope nach ID
 */
function findElementById(
  envelope: DIN18599Data['input']['envelope'],
  elementId: string
): WallExternal | Roof | Floor | undefined {
  if (!envelope) return undefined
  
  const allElements = [
    ...(envelope.walls_external || []),
    ...(envelope.walls_internal || []),
    ...(envelope.roofs || []),
    ...(envelope.floors || [])
  ]
  return allElements.find(el => el.id === elementId)
}

/**
 * Fügt eine Komponente zur Envelope hinzu (z.B. Gaube)
 */
function addComponentToEnvelope(
  envelope: NonNullable<DIN18599Data['input']['envelope']>,
  component: BuildingElementComponent,
  parentId: string
): void {
  const componentId = `${parentId}_${component.type.toLowerCase()}`

  switch (component.type) {
    case 'WALL':
      if (!envelope.walls_external) envelope.walls_external = []
      envelope.walls_external.push({
        id: componentId,
        ifc_guid: `generated_${componentId}`,
        name: `${parentId} - Wand`,
        boundary_condition: 'EXTERNAL',
        area: component.area,
        u_value_undisturbed: component.u_value || 0.24,
        thermal_bridge_delta_u: 0.05,
        orientation: 180,
        inclination: 90,
        solar_absorption: 0.6,
        thermal_bridge_type: 'REDUCED'
      })
      break

    case 'ROOF':
      if (!envelope.roofs) envelope.roofs = []
      envelope.roofs.push({
        id: componentId,
        ifc_guid: `generated_${componentId}`,
        name: `${parentId} - Dach`,
        boundary_condition: 'EXTERNAL',
        area: component.area,
        u_value_undisturbed: component.u_value || 0.14,
        thermal_bridge_delta_u: 0.05,
        orientation: 180,
        inclination: 45,
        solar_absorption: 0.6,
        thermal_bridge_type: 'REDUCED'
      })
      break

    case 'WINDOW':
      if (!envelope.openings) envelope.openings = []
      envelope.openings.push({
        id: componentId,
        type: 'WINDOW',
        ifc_guid: `generated_${componentId}`,
        name: `${parentId} - Fenster`,
        parent_element_id: `${parentId}_wall`,
        parent_element_type: 'WALL_EXT',
        orientation: 180,
        area: component.area,
        u_value_glass: component.u_value || 0.95,
        u_value_frame: 1.0,
        g_value: 0.6,
        frame_fraction: 0.3,
        psi_spacer: 0.04,
        shading_factor_fs: 1.0
      })
      break

    case 'DOOR':
      if (!envelope.openings) envelope.openings = []
      envelope.openings.push({
        id: componentId,
        type: 'DOOR',
        ifc_guid: `generated_${componentId}`,
        name: `${parentId} - Tür`,
        parent_element_id: `${parentId}_wall`,
        parent_element_type: 'WALL_EXT',
        orientation: 180,
        area: component.area,
        u_value_glass: component.u_value || 1.3,
        u_value_frame: 1.5,
        g_value: 0.5,
        frame_fraction: 0.4,
        psi_spacer: 0.06,
        shading_factor_fs: 1.0
      })
      break
  }
}

/**
 * Berechnet die Netto-Fläche einer Wand (Brutto - Fenster - Türen)
 */
export function calculateNetArea(
  wall: WallExternal,
  openings?: Opening[]
): number {
  const wallOpenings = openings?.filter(
    (o: Opening) => o.parent_element_id === wall.id
  ) || []
  
  const openingsArea = wallOpenings.reduce((sum: number, o: Opening) => sum + o.area, 0)
  return Math.max(0, wall.area - openingsArea)
}

/**
 * Berechnet den effektiven U-Wert einer Wand (mit Wärmebrücken)
 */
export function calculateEffectiveUValue(
  element: WallExternal | Roof | Floor
): number {
  const deltaU = element.thermal_bridge_delta_u || 0
  return element.u_value_undisturbed + deltaU
}

/**
 * Berechnet den Transmissionswärmeverlust eines Bauteils
 */
export function calculateTransmissionLoss(
  element: WallExternal | Roof | Floor,
  openings?: Opening[]
): number {
  let area = element.area
  
  // Netto-Fläche für Wände
  if ('orientation' in element && openings) {
    area = calculateNetArea(element as WallExternal, openings)
  }
  
  const uEff = calculateEffectiveUValue(element)
  return area * uEff
}
