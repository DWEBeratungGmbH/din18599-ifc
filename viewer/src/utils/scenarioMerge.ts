import type { DIN18599Data, Scenario } from '../store/viewer.store'
import { applyBuildingElements } from './buildingElements'

/**
 * Wendet ein Szenario auf die Basis-Daten an (Delta-Merge)
 * 
 * Prinzip: Nur geänderte Felder werden überschrieben, der Rest bleibt gleich.
 */
export function applyScenario(
  baseData: DIN18599Data,
  scenario: Scenario
): DIN18599Data {
  // 1. Deep-Clone der Basis-Daten
  const result = structuredClone(baseData)

  // 2. Delta-Merge: Input-Daten
  if (scenario.delta?.input) {
    result.input = deepMerge(result.input, scenario.delta.input)
  }

  // 3. BuildingElements anwenden (falls vorhanden)
  if (scenario.building_elements && scenario.building_elements.length > 0) {
    return applyBuildingElements(result, scenario.building_elements)
  }

  // 4. Output überschreiben (falls vorhanden)
  if (scenario.output) {
    result.output = scenario.output
  }

  return result
}

/**
 * Deep-Merge von zwei Objekten
 * 
 * Arrays werden nach ID gemergt (nicht konkateniert!)
 */
function deepMerge<T>(target: T, source: Partial<T>): T {
  if (!source) return target
  if (!target) return source as T

  const result = { ...target }

  for (const key in source) {
    const sourceValue = source[key]
    const targetValue = result[key]

    // Array-Merge by ID
    if (Array.isArray(sourceValue) && Array.isArray(targetValue)) {
      result[key] = mergeArraysById(targetValue, sourceValue) as any
    }
    // Objekt-Merge (rekursiv)
    else if (isObject(sourceValue) && isObject(targetValue)) {
      result[key] = deepMerge(targetValue, sourceValue as any) as any
    }
    // Primitiv-Wert überschreiben
    else if (sourceValue !== undefined) {
      result[key] = sourceValue as any
    }
  }

  return result
}

/**
 * Merged zwei Arrays nach ID
 * 
 * Beispiel:
 * Base: [{ id: 'w1', u_value: 1.2 }]
 * Delta: [{ id: 'w1', u_value: 0.24 }]
 * Result: [{ id: 'w1', u_value: 0.24 }]
 */
function mergeArraysById<T extends { id: string }>(
  target: T[],
  source: Partial<T>[]
): T[] {
  const result = [...target]

  for (const sourceItem of source) {
    if (!sourceItem.id) continue

    const targetIndex = result.findIndex(t => t.id === sourceItem.id)

    if (targetIndex >= 0) {
      // Item existiert → Merge
      result[targetIndex] = deepMerge(result[targetIndex], sourceItem)
    } else {
      // Item neu → Hinzufügen
      result.push(sourceItem as T)
    }
  }

  return result
}

/**
 * Prüft ob ein Wert ein Objekt ist (kein Array, kein null)
 */
function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

/**
 * Berechnet die Einsparungen zwischen zwei Outputs
 */
export function calculateSavings(
  baseOutput: DIN18599Data['output'],
  scenarioOutput: DIN18599Data['output']
) {
  if (!baseOutput?.energy_balance || !scenarioOutput?.energy_balance) {
    return undefined
  }

  const baseFinal = baseOutput.energy_balance.final_energy_kwh_a
  const scenarioFinal = scenarioOutput.energy_balance.final_energy_kwh_a

  const basePrimary = baseOutput.energy_balance.primary_energy_kwh_a
  const scenarioPrimary = scenarioOutput.energy_balance.primary_energy_kwh_a

  const baseCO2 = baseOutput.energy_balance.co2_emissions_kg_a || 0
  const scenarioCO2 = scenarioOutput.energy_balance.co2_emissions_kg_a || 0

  return {
    final_energy_kwh_a: baseFinal - scenarioFinal,
    final_energy_percent: ((baseFinal - scenarioFinal) / baseFinal) * 100,
    primary_energy_kwh_a: basePrimary - scenarioPrimary,
    primary_energy_percent: ((basePrimary - scenarioPrimary) / basePrimary) * 100,
    co2_kg_a: baseCO2 - scenarioCO2,
    co2_percent: baseCO2 > 0 ? ((baseCO2 - scenarioCO2) / baseCO2) * 100 : 0,
    cost_annual_eur: 0 // TODO: Berechnung aus Energiepreisen
  }
}

/**
 * Vergleicht zwei Szenarien
 */
export function compareScenarios(
  baseData: DIN18599Data,
  scenario1: Scenario,
  scenario2: Scenario
): {
  scenario1: DIN18599Data
  scenario2: DIN18599Data
  comparison: {
    final_energy_diff_kwh_a: number
    primary_energy_diff_kwh_a: number
    co2_diff_kg_a: number
    cost_diff_eur: number
  }
} {
  const data1 = applyScenario(baseData, scenario1)
  const data2 = applyScenario(baseData, scenario2)

  const comparison = {
    final_energy_diff_kwh_a: 
      (data1.output?.energy_balance?.final_energy_kwh_a || 0) -
      (data2.output?.energy_balance?.final_energy_kwh_a || 0),
    primary_energy_diff_kwh_a:
      (data1.output?.energy_balance?.primary_energy_kwh_a || 0) -
      (data2.output?.energy_balance?.primary_energy_kwh_a || 0),
    co2_diff_kg_a:
      (data1.output?.energy_balance?.co2_emissions_kg_a || 0) -
      (data2.output?.energy_balance?.co2_emissions_kg_a || 0),
    cost_diff_eur: 0 // TODO
  }

  return { scenario1: data1, scenario2: data2, comparison }
}
