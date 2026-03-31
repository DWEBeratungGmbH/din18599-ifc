#!/usr/bin/env node

/**
 * Migration Script: v2.0 → v2.1
 * 
 * Konvertiert DIN 18599 Sidecar Dateien von v2.0 zu v2.1
 * 
 * Usage:
 *   node scripts/migrate-v2.0-to-v2.1.js input.json output.json
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// ============================================================================
// Hauptfunktion
// ============================================================================

function migrate(v20Data) {
  console.log('🔄 Migration v2.0 → v2.1 gestartet...');
  
  const v21Data = {
    schema_info: {
      url: "https://din18599-ifc.de/schema/v2.1/complete",
      version: "2.1.0"
    },
    
    meta: migrateMeta(v20Data.meta || {}),
    
    input: migrateInput(v20Data),
    
    scenarios: migrateScenarios(v20Data.scenarios || []),
    
    // Output wird NICHT migriert (muss neu berechnet werden)
  };
  
  console.log('✅ Migration abgeschlossen');
  return v21Data;
}

// ============================================================================
// Meta-Daten
// ============================================================================

function migrateMeta(oldMeta) {
  return {
    project_name: oldMeta.project_name || "Unnamed Project",
    project_id: oldMeta.project_id || generateUUID(),
    created: oldMeta.created || new Date().toISOString(),
    last_modified: new Date().toISOString(),
    version: "1.0.0",
    version_history: [
      {
        version: "1.0.0",
        date: new Date().toISOString(),
        changes: "Migration von v2.0 zu v2.1",
        author: "Migration Script"
      }
    ],
    ifc_file_ref: oldMeta.ifc_file_ref,
    lod: determineLOD(oldMeta)
  };
}

function determineLOD(meta) {
  // LOD aus alten Daten ableiten
  if (meta.lod) return meta.lod;
  return "200"; // Default
}

// ============================================================================
// Input-Daten
// ============================================================================

function migrateInput(v20Data) {
  const input = {
    building: migrateBuilding(v20Data),
    envelope: migrateEnvelope(v20Data),
    systems: migrateSystems(v20Data),
  };
  
  // Optional: Electricity
  if (v20Data.electricity || v20Data.pv) {
    input.electricity = migrateElectricity(v20Data);
  }
  
  // Optional: Automation (neu in v2.1)
  if (v20Data.automation) {
    input.automation = v20Data.automation;
  }
  
  // Optional: Primary Energy (neu in v2.1)
  if (v20Data.output?.primary_energy_factors || v20Data.primary_energy) {
    input.primary_energy = migratePrimaryEnergy(v20Data);
  }
  
  // Optional: Climate
  if (v20Data.climate || v20Data.location) {
    input.climate = migrateClimate(v20Data);
  }
  
  return input;
}

// ============================================================================
// Building
// ============================================================================

function migrateBuilding(v20Data) {
  const building = {
    address: v20Data.address || {
      zip: "00000",
      city: "Unknown"
    },
    construction_year: v20Data.construction_year || 1900,
    heated_area: v20Data.heated_area || v20Data.area || 0,
  };
  
  // Optional
  if (v20Data.renovation_year) building.renovation_year = v20Data.renovation_year;
  if (v20Data.type) building.type = v20Data.type;
  if (v20Data.gross_floor_area) building.gross_floor_area = v20Data.gross_floor_area;
  if (v20Data.heated_volume) building.heated_volume = v20Data.heated_volume;
  if (v20Data.av_ratio) building.av_ratio = v20Data.av_ratio;
  
  // Zonen
  if (v20Data.zones && v20Data.zones.length > 0) {
    building.zones = v20Data.zones.map(migrateZone);
  }
  
  return building;
}

function migrateZone(oldZone) {
  const zone = {
    id: oldZone.id || generateID('zone'),
    name: oldZone.name,
    usage_profile_ref: oldZone.usage_profile || oldZone.usage_profile_ref,
    area: oldZone.area || 0,
  };
  
  // Optional
  if (oldZone.volume) zone.volume = oldZone.volume;
  if (oldZone.height) zone.height = oldZone.height;
  if (oldZone.setpoint_heating_c) zone.setpoint_heating_c = oldZone.setpoint_heating_c;
  if (oldZone.setpoint_cooling_c) zone.setpoint_cooling_c = oldZone.setpoint_cooling_c;
  if (oldZone.air_change_rate_h) zone.air_change_rate_h = oldZone.air_change_rate_h;
  if (oldZone.conditioned !== undefined) zone.conditioned = oldZone.conditioned;
  
  return zone;
}

// ============================================================================
// Envelope (BREAKING CHANGE: Hierarchisch)
// ============================================================================

function migrateEnvelope(v20Data) {
  const envelope = {
    opaque_elements: {},
    transparent_elements: {},
  };
  
  // v2.0: Flaches elements[] Array
  // v2.1: Hierarchisch nach Bauteiltyp
  
  if (v20Data.elements && Array.isArray(v20Data.elements)) {
    const opaque = {
      walls_external: [],
      walls_internal: [],
      roofs: [],
      floors: []
    };
    
    const transparent = {
      windows: [],
      doors: []
    };
    
    for (const element of v20Data.elements) {
      const migrated = migrateElement(element);
      
      // Klassifizierung nach Typ
      const type = element.type || 'wall_external';
      
      if (type.includes('window')) {
        transparent.windows.push(migrated);
      } else if (type.includes('door')) {
        transparent.doors.push(migrated);
      } else if (type.includes('roof')) {
        opaque.roofs.push(migrated);
      } else if (type.includes('floor') || type.includes('basement')) {
        opaque.floors.push(migrated);
      } else if (type.includes('internal')) {
        opaque.walls_internal.push(migrated);
      } else {
        opaque.walls_external.push(migrated);
      }
    }
    
    envelope.opaque_elements = opaque;
    envelope.transparent_elements = transparent;
  }
  
  // Wärmebrücken
  if (v20Data.thermal_bridges) {
    envelope.thermal_bridges = v20Data.thermal_bridges;
  }
  
  return envelope;
}

function migrateElement(oldElement) {
  const element = {
    id: oldElement.id || generateID('element'),
  };
  
  // Optional
  if (oldElement.ifc_guid) element.ifc_guid = oldElement.ifc_guid;
  if (oldElement.construction_ref) element.construction_ref = oldElement.construction_ref;
  if (oldElement.u_value) element.u_value = oldElement.u_value;
  if (oldElement.area) element.area = oldElement.area;
  if (oldElement.orientation) element.orientation = oldElement.orientation;
  if (oldElement.inclination) element.inclination = oldElement.inclination;
  
  // Fenster-spezifisch
  if (oldElement.g_value) element.g_value = oldElement.g_value;
  if (oldElement.shading_factor_f_sh) element.shading_factor_f_sh = oldElement.shading_factor_f_sh;
  
  return element;
}

// ============================================================================
// Systems (BREAKING CHANGE: Detailliert)
// ============================================================================

function migrateSystems(v20Data) {
  const systems = {};
  
  // Heizung
  if (v20Data.heating || v20Data.systems?.heating) {
    systems.heating = migrateHeating(v20Data.heating || v20Data.systems.heating);
  }
  
  // Lüftung
  if (v20Data.ventilation || v20Data.systems?.ventilation) {
    systems.ventilation = migrateVentilation(v20Data.ventilation || v20Data.systems.ventilation);
  }
  
  // Kühlung
  if (v20Data.cooling || v20Data.systems?.cooling) {
    systems.cooling = migrateCooling(v20Data.cooling || v20Data.systems.cooling);
  }
  
  // Beleuchtung
  if (v20Data.lighting || v20Data.systems?.lighting) {
    systems.lighting = migrateLighting(v20Data.lighting || v20Data.systems.lighting);
  }
  
  // Warmwasser
  if (v20Data.dhw || v20Data.systems?.dhw) {
    systems.dhw = migrateDHW(v20Data.dhw || v20Data.systems.dhw);
  }
  
  return systems;
}

function migrateHeating(oldHeating) {
  // v2.1: Detailliert (generation/distribution/emission/control)
  return {
    generation: {
      type: oldHeating.type || oldHeating.generation?.type,
      installation_year: oldHeating.installation_year || oldHeating.generation?.installation_year,
      nominal_power_kw: oldHeating.nominal_power_kw || oldHeating.generation?.nominal_power_kw,
      efficiency: oldHeating.efficiency || oldHeating.generation?.efficiency
    },
    distribution: oldHeating.distribution || {},
    emission: oldHeating.emission || {},
    control: oldHeating.control || {}
  };
}

function migrateVentilation(oldVentilation) {
  return {
    type: oldVentilation.type,
    n50_value: oldVentilation.n50_value,
    heat_recovery: oldVentilation.heat_recovery,
    heat_recovery_efficiency: oldVentilation.heat_recovery_efficiency,
    air_flow_rate_m3h: oldVentilation.air_flow_rate_m3h
  };
}

function migrateCooling(oldCooling) {
  return {
    installed: oldCooling.installed || false,
    type: oldCooling.type,
    nominal_power_kw: oldCooling.nominal_power_kw,
    eer: oldCooling.eer
  };
}

function migrateLighting(oldLighting) {
  return {
    applicable: oldLighting.applicable !== false,
    installed_power_w_m2: oldLighting.installed_power_w_m2,
    control_type: oldLighting.control_type
  };
}

function migrateDHW(oldDHW) {
  return {
    type: oldDHW.type,
    storage_volume_l: oldDHW.storage_volume_l,
    circulation: oldDHW.circulation
  };
}

// ============================================================================
// Electricity
// ============================================================================

function migrateElectricity(v20Data) {
  const electricity = {};
  
  if (v20Data.pv || v20Data.electricity?.pv) {
    const oldPV = v20Data.pv || v20Data.electricity.pv;
    electricity.pv = {
      installed: oldPV.installed !== false,
      peak_power_kwp: oldPV.peak_power_kwp || oldPV.kwp,
      area_m2: oldPV.area_m2 || oldPV.area,
      orientation: oldPV.orientation,
      inclination: oldPV.inclination
    };
  }
  
  return electricity;
}

// ============================================================================
// Primary Energy (NEU in v2.1)
// ============================================================================

function migratePrimaryEnergy(v20Data) {
  // v2.0: Primärenergiefaktoren waren im Output
  // v2.1: Primärenergiefaktoren sind im Input (Randbedingungen)
  
  const factors = v20Data.output?.primary_energy_factors || v20Data.primary_energy?.factors || {};
  
  return {
    source: v20Data.primary_energy?.source || "GEG_2024",
    reference_year: v20Data.primary_energy?.reference_year || 2024,
    factors: {
      electricity: factors.electricity || 1.8,
      natural_gas: factors.natural_gas || 1.1,
      oil: factors.oil || 1.1,
      district_heating: factors.district_heating || 0.0,
      wood_pellets: factors.wood_pellets || 0.2
    },
    co2_factors: v20Data.primary_energy?.co2_factors || {}
  };
}

// ============================================================================
// Climate
// ============================================================================

function migrateClimate(v20Data) {
  return {
    try_region: v20Data.climate?.try_region || v20Data.location?.try_region,
    heating_degree_days: v20Data.climate?.heating_degree_days
  };
}

// ============================================================================
// Scenarios
// ============================================================================

function migrateScenarios(oldScenarios) {
  return oldScenarios.map(scenario => ({
    id: scenario.id || generateID('scenario'),
    name: scenario.name,
    description: scenario.description,
    priority: scenario.priority,
    timeline: scenario.timeline,
    delta: scenario.delta || {}
  }));
}

// ============================================================================
// Hilfsfunktionen
// ============================================================================

function generateUUID() {
  return crypto.randomUUID();
}

function generateID(prefix) {
  return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

// ============================================================================
// CLI
// ============================================================================

function main() {
  const args = process.argv.slice(2);
  
  if (args.length < 2) {
    console.error('Usage: node migrate-v2.0-to-v2.1.js <input.json> <output.json>');
    process.exit(1);
  }
  
  const inputFile = args[0];
  const outputFile = args[1];
  
  console.log(`📂 Lese ${inputFile}...`);
  
  // Datei einlesen
  const v20Data = JSON.parse(fs.readFileSync(inputFile, 'utf8'));
  
  // Migration durchführen
  const v21Data = migrate(v20Data);
  
  // Datei schreiben
  console.log(`💾 Schreibe ${outputFile}...`);
  fs.writeFileSync(outputFile, JSON.stringify(v21Data, null, 2), 'utf8');
  
  console.log('✅ Migration erfolgreich!');
  console.log('');
  console.log('⚠️  WICHTIG:');
  console.log('   - Output-Daten wurden NICHT migriert (müssen neu berechnet werden)');
  console.log('   - Bitte validieren Sie die migrierte Datei gegen Schema v2.1');
  console.log('   - Prüfen Sie die Katalog-Referenzen (construction_ref, usage_profile_ref)');
}

if (require.main === module) {
  main();
}

module.exports = { migrate };
