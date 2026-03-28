#!/usr/bin/env node
/**
 * Merge Advanced Extracted Data into Registries
 */

const fs = require('fs');
const path = require('path');

const TEMP_DIR = path.join(__dirname, '../.temp');
const CATALOG_DIR = path.join(__dirname, '../catalog');

// Load data
const symbols = JSON.parse(fs.readFileSync(path.join(TEMP_DIR, 'symbols-advanced.json'), 'utf-8'));
const indices = JSON.parse(fs.readFileSync(path.join(TEMP_DIR, 'indices-advanced.json'), 'utf-8'));

const symbolRegistry = JSON.parse(fs.readFileSync(path.join(CATALOG_DIR, 'din18599_symbols.json'), 'utf-8'));
const indexRegistry = JSON.parse(fs.readFileSync(path.join(CATALOG_DIR, 'din18599_indices.json'), 'utf-8'));

console.log('🔄 Merge Advanced Data...\n');

// 1. Merge Symbols (deduplizieren nach Symbol-Name)
const symbolMap = new Map();

// Bestehende Symbole
symbolRegistry.symbols.forEach(s => {
  symbolMap.set(s.symbol, s);
});

// Neue Symbole hinzufügen/mergen
symbols.forEach(extracted => {
  if (symbolMap.has(extracted.symbol)) {
    // Symbol existiert - Parts hinzufügen
    const existing = symbolMap.get(extracted.symbol);
    if (!existing.used_in_parts) existing.used_in_parts = [];
    if (!existing.used_in_parts.includes(extracted.part)) {
      existing.used_in_parts.push(extracted.part);
    }
  } else {
    // Neues Symbol
    symbolMap.set(extracted.symbol, {
      symbol: extracted.symbol,
      symbol_latex: extracted.symbol.replace(/_/g, '\\_'),
      name_de: extracted.name_de,
      name_en: extracted.name_en,
      unit: extracted.unit,
      unit_latex: extracted.unit,
      data_type: 'number',
      category: 'general',
      used_in_parts: [extracted.part],
      norm_refs: [`DIN_18599-${extracted.part}_2018-09_TAB_1`]
    });
  }
});

symbolRegistry.symbols = Array.from(symbolMap.values());
symbolRegistry.statistics.current_count = symbolRegistry.symbols.length;
symbolRegistry.statistics.completion_percentage = Math.round(
  (symbolRegistry.symbols.length / symbolRegistry.statistics.total_symbols) * 100
);

console.log(`✅ Symbole: ${symbolRegistry.symbols.length} (${symbolRegistry.statistics.completion_percentage}%)`);

// 2. Merge Indices
const indexMap = new Map();

indexRegistry.indices.forEach(i => {
  indexMap.set(i.index, i);
});

indices.forEach(extracted => {
  if (indexMap.has(extracted.index)) {
    const existing = indexMap.get(extracted.index);
    if (!existing.used_in_parts) existing.used_in_parts = [];
    if (!existing.used_in_parts.includes(extracted.part)) {
      existing.used_in_parts.push(extracted.part);
    }
  } else {
    indexMap.set(extracted.index, {
      index: extracted.index,
      name_de: extracted.name_de,
      name_en: extracted.name_en,
      type: 'general',
      used_in_parts: [extracted.part],
      examples: []
    });
  }
});

indexRegistry.indices = Array.from(indexMap.values());
indexRegistry.statistics.current_count = indexRegistry.indices.length;
indexRegistry.statistics.completion_percentage = Math.round(
  (indexRegistry.indices.length / indexRegistry.statistics.total_indices) * 100
);

console.log(`✅ Indizes: ${indexRegistry.indices.length} (${indexRegistry.statistics.completion_percentage}%)`);

// Save
fs.writeFileSync(
  path.join(CATALOG_DIR, 'din18599_symbols.json'),
  JSON.stringify(symbolRegistry, null, 2)
);

fs.writeFileSync(
  path.join(CATALOG_DIR, 'din18599_indices.json'),
  JSON.stringify(indexRegistry, null, 2)
);

console.log('\n✅ Registries aktualisiert!');
