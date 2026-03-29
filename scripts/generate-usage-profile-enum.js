#!/usr/bin/env node
/**
 * Generate usage_profile Enum from DIN 18599 Registry
 * Erstellt JSON Schema Enum für alle 45 Nutzungsprofile
 */

const fs = require('fs');
const path = require('path');

const CATALOG_DIR = path.join(__dirname, '../catalog');
const OUTPUT_DIR = path.join(__dirname, '../schema');

// Lade Nutzungsprofile
const usageProfiles = JSON.parse(
  fs.readFileSync(path.join(CATALOG_DIR, 'din18599_usage_profiles.json'), 'utf-8')
);

console.log('🏢 Generiere usage_profile Enum für Schema v2.1...\n');

// Erstelle Enum-Array
const enumValues = [];
const enumDescriptions = {};

// Wohngebäude
usageProfiles.residential_profiles.forEach(profile => {
  enumValues.push(profile.id);
  enumDescriptions[profile.id] = `${profile.name_de} (${profile.abbreviation || profile.number})`;
});

// Nichtwohngebäude
usageProfiles.non_residential_profiles.forEach(profile => {
  enumValues.push(profile.id);
  enumDescriptions[profile.id] = `${profile.number}: ${profile.name_de}`;
});

console.log(`✅ ${enumValues.length} Profile gefunden\n`);

// Erstelle Schema-Fragment
const schemaFragment = {
  "usage_profile": {
    "type": "string",
    "enum": enumValues,
    "description": "Nutzungsprofil nach DIN 18599-10. Wohngebäude (PROFILE_RES_*) oder Nichtwohngebäude (PROFILE_NWG_01 bis PROFILE_NWG_43).",
    "examples": ["PROFILE_RES_EFH", "PROFILE_NWG_01", "PROFILE_NWG_17"],
    "$comment": "Generiert aus catalog/din18599_usage_profiles.json - 45 Profile (2 Wohn, 43 Nichtwohn)"
  }
};

// Erstelle Mapping-Datei für Dokumentation
const mapping = {
  "version": "2.1.0",
  "source": "DIN/TS 18599-10:2018-09",
  "total_profiles": enumValues.length,
  "residential": usageProfiles.residential_profiles.length,
  "non_residential": usageProfiles.non_residential_profiles.length,
  "profiles": {}
};

enumValues.forEach(id => {
  mapping.profiles[id] = enumDescriptions[id];
});

// Speichern
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

fs.writeFileSync(
  path.join(OUTPUT_DIR, 'usage_profile_enum.json'),
  JSON.stringify(schemaFragment, null, 2)
);

fs.writeFileSync(
  path.join(OUTPUT_DIR, 'usage_profile_mapping.json'),
  JSON.stringify(mapping, null, 2)
);

console.log('📄 Dateien erstellt:');
console.log('   schema/usage_profile_enum.json - Schema-Fragment');
console.log('   schema/usage_profile_mapping.json - Dokumentation');

console.log('\n📊 Profile-Übersicht:');
console.log(`   Wohngebäude: ${usageProfiles.residential_profiles.length}`);
usageProfiles.residential_profiles.forEach(p => {
  console.log(`      - ${p.id}: ${p.name_de}`);
});

console.log(`\n   Nichtwohngebäude: ${usageProfiles.non_residential_profiles.length}`);
console.log(`      - PROFILE_NWG_01 bis PROFILE_NWG_43`);
console.log(`      - Kategorien: ${usageProfiles.categories.length} (office, education, healthcare, etc.)`);

console.log('\n✅ Enum-Generierung abgeschlossen!');
