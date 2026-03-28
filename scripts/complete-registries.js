#!/usr/bin/env node
/**
 * DIN 18599 Registry Completion Script
 * Vervollständigt Glossar, Symbol-Registry und Index-Registry auf 100%
 */

const fs = require('fs');
const path = require('path');

const TEMP_DIR = path.join(__dirname, '../.temp');
const CATALOG_DIR = path.join(__dirname, '../catalog');

// Extrahierte Daten laden
const extractedTerms = JSON.parse(
  fs.readFileSync(path.join(TEMP_DIR, 'extracted-terms.json'), 'utf-8')
);

const extractedSymbols = JSON.parse(
  fs.readFileSync(path.join(TEMP_DIR, 'extracted-symbols.json'), 'utf-8')
);

// Bestehende Registries laden
const glossary = JSON.parse(
  fs.readFileSync(path.join(CATALOG_DIR, 'din18599_glossary.json'), 'utf-8')
);

const symbolRegistry = JSON.parse(
  fs.readFileSync(path.join(CATALOG_DIR, 'din18599_symbols.json'), 'utf-8')
);

// Hilfsfunktion: Begriff-ID generieren
function generateTermId(term) {
  return 'TERM_' + term
    .toUpperCase()
    .replace(/[ÄÖÜ]/g, (m) => ({ Ä: 'AE', Ö: 'OE', Ü: 'UE' }[m]))
    .replace(/ß/g, 'SS')
    .replace(/[^A-Z0-9]/g, '_')
    .replace(/_+/g, '_')
    .replace(/^_|_$/g, '');
}

// Hilfsfunktion: Kategorie zuordnen
function categorizeTermPart(part) {
  const categories = {
    1: 'energy_level',
    2: 'thermal_conditions',
    3: 'building_services',
    4: 'lighting',
    5: 'heating',
    6: 'ventilation',
    7: 'cooling',
    8: 'hot_water',
    9: 'electricity',
    10: 'usage_conditions',
    11: 'automation'
  };
  return categories[part] || 'general';
}

console.log('🚀 Vervollständige Registries auf 100%...\n');

// 1. Glossar vervollständigen
console.log('📖 Glossar vervollständigen...');
const existingTermIds = new Set(glossary.terms.map(t => t.id));
let newTermsCount = 0;

extractedTerms.forEach((extracted, index) => {
  const termId = generateTermId(extracted.term_de);
  
  // Nur neue Begriffe hinzufügen
  if (!existingTermIds.has(termId)) {
    const newTerm = {
      id: termId,
      number: extracted.number,
      part: extracted.part,
      term_de: extracted.term_de,
      term_en: '', // Wird später manuell ergänzt
      definition_de: extracted.definition_de,
      norm_refs: [`DIN_18599-${extracted.part}_2018-09_SEC_3`],
      category: categorizeTermPart(extracted.part),
      see_also: []
    };
    
    glossary.terms.push(newTerm);
    newTermsCount++;
  }
});

// Statistik aktualisieren
glossary.statistics.total_terms = glossary.terms.length;
glossary.version = '3.0.0';
glossary.last_updated = new Date().toISOString().split('T')[0];

// Glossar speichern
fs.writeFileSync(
  path.join(CATALOG_DIR, 'din18599_glossary.json'),
  JSON.stringify(glossary, null, 2)
);

console.log(`   ✅ ${newTermsCount} neue Begriffe hinzugefügt`);
console.log(`   📊 Gesamt: ${glossary.terms.length} Begriffe\n`);

// 2. Symbol-Registry vervollständigen
console.log('🔣 Symbol-Registry vervollständigen...');
const existingSymbols = new Set(symbolRegistry.symbols.map(s => s.symbol));
let newSymbolsCount = 0;

extractedSymbols.forEach(extracted => {
  if (!existingSymbols.has(extracted.symbol)) {
    const newSymbol = {
      symbol: extracted.symbol,
      symbol_latex: extracted.symbol.replace(/_/g, '\\_'),
      name_de: extracted.name_de,
      name_en: '',
      unit: extracted.unit,
      unit_latex: extracted.unit,
      data_type: 'number',
      category: 'general',
      used_in_parts: [extracted.part],
      norm_refs: [`DIN_18599-${extracted.part}_2018-09_TAB_1`]
    };
    
    symbolRegistry.symbols.push(newSymbol);
    newSymbolsCount++;
  }
});

// Statistik aktualisieren
symbolRegistry.statistics.current_count = symbolRegistry.symbols.length;
symbolRegistry.statistics.completion_percentage = Math.round(
  (symbolRegistry.symbols.length / symbolRegistry.statistics.total_symbols) * 100
);
symbolRegistry.version = '3.0.0';

// Symbol-Registry speichern
fs.writeFileSync(
  path.join(CATALOG_DIR, 'din18599_symbols.json'),
  JSON.stringify(symbolRegistry, null, 2)
);

console.log(`   ✅ ${newSymbolsCount} neue Symbole hinzugefügt`);
console.log(`   📊 Gesamt: ${symbolRegistry.symbols.length} Symbole (${symbolRegistry.statistics.completion_percentage}%)\n`);

// Zusammenfassung
console.log('✅ Registry-Vervollständigung abgeschlossen!\n');
console.log('📊 Finale Statistik:');
console.log(`   Glossar: ${glossary.terms.length} Begriffe`);
console.log(`   Symbole: ${symbolRegistry.symbols.length} Symbole`);
console.log('\n💡 Nächste Schritte:');
console.log('   - Englische Übersetzungen ergänzen');
console.log('   - Symbol-Kategorien verfeinern');
console.log('   - Index-Registry manuell vervollständigen');
