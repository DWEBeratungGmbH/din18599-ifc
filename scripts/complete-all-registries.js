#!/usr/bin/env node
/**
 * Complete All Registries to 100%
 * Extrahiert ALLE Begriffe, Symbole und Indizes aus Markdown-Quellen
 */

const fs = require('fs');
const path = require('path');

const SOURCES_DIR = path.join(__dirname, '../sources/markdown');
const CATALOG_DIR = path.join(__dirname, '../catalog');

function readMarkdown(partNumber) {
  const filename = `DIN18599-${partNumber.toString().padStart(2, '0')}.md`;
  const filepath = path.join(SOURCES_DIR, filename);
  if (!fs.existsSync(filepath)) return null;
  return fs.readFileSync(filepath, 'utf-8');
}

// Extrahiere ALLE Begriffe aus Abschnitt 3.1
function extractAllTerms(markdown, partNumber) {
  const terms = [];
  
  // Finde Abschnitt 3.1
  const section31Match = markdown.match(/## 3\.1 Begriffe\s*\n([\s\S]*?)(?=\n## 3\.2|## 4|# 4|$)/);
  if (!section31Match) return terms;
  
  const section = section31Match[1];
  
  // Extrahiere alle nummerierten Begriffe (### 3.1.X)
  const termRegex = /### (3\.1\.\d+)\s*\n\s*\n\*\*(.*?)\*\*\s*\n\s*\n([\s\S]*?)(?=\n### 3\.1\.\d+|## 3\.2|$)/g;
  
  let match;
  while ((match = termRegex.exec(section)) !== null) {
    const number = match[1];
    let term = match[2].trim();
    let definition = match[3].trim();
    
    // Bereinige Definition (nur erste Zeile, keine Anmerkungen)
    definition = definition.split('\n')[0].trim();
    
    // Entferne Markdown-Formatierung aus Begriff
    term = term.replace(/\*\*/g, '');
    
    if (term && definition) {
      terms.push({
        number,
        term_de: term,
        definition_de: definition,
        part: partNumber
      });
    }
  }
  
  return terms;
}

// Extrahiere ALLE Symbole aus Tabelle 1
function extractAllSymbols(markdown, partNumber) {
  const symbols = [];
  
  // Finde Tabelle 1
  const tableMatch = markdown.match(/### Tabelle 1.*?\n([\s\S]*?)(?=\n### Tabelle 2|## 4|# 4|$)/);
  if (!tableMatch) return symbols;
  
  const tableContent = tableMatch[1];
  const lines = tableContent.split('\n');
  
  let currentSymbol = null;
  let currentNameDe = '';
  let currentNameEn = '';
  let currentUnit = '';
  
  for (const line of lines) {
    // Überspringe Trennlinien und Header
    if (line.match(/^[\s-]+$/) || line.includes('Symbol') || line.includes('Deutsch')) continue;
    
    // Parse Zeilen mit mindestens 2 Spalten
    const cols = line.split(/\s{2,}/).map(c => c.trim()).filter(c => c);
    
    if (cols.length >= 3) {
      // Zeile mit Symbol, Deutsch, English, Einheit
      const symbol = cols[0].replace(/\*/g, '').replace(/\\/g, '').trim();
      
      // Nur gültige Symbole (max 20 Zeichen, keine Beschreibungen)
      if (symbol && symbol.length <= 20 && !symbol.includes('Bedeutung')) {
        currentSymbol = symbol;
        currentNameDe = cols[1] || '';
        currentNameEn = cols[2] || '';
        currentUnit = cols[3] || '---';
        
        symbols.push({
          symbol: currentSymbol,
          name_de: currentNameDe,
          name_en: currentNameEn,
          unit: currentUnit,
          part: partNumber
        });
      }
    } else if (cols.length === 2 && !cols[0].includes('Symbol')) {
      // Zeile nur mit Deutsch, English (Symbol in vorheriger Zeile)
      currentNameDe = cols[0] || '';
      currentNameEn = cols[1] || '';
    }
  }
  
  return symbols;
}

// Extrahiere ALLE Indizes aus Tabelle 2
function extractAllIndices(markdown, partNumber) {
  const indices = [];
  
  // Finde Tabelle 2
  const tableMatch = markdown.match(/### Tabelle 2.*?\n([\s\S]*?)(?=\n### Tabelle 3|## 4|# 4|# 5|$)/);
  if (!tableMatch) return indices;
  
  const tableContent = tableMatch[1];
  const lines = tableContent.split('\n');
  
  for (const line of lines) {
    // Überspringe Trennlinien und Header
    if (line.match(/^[\s-]+$/) || line.includes('Index') || line.includes('Deutsch')) continue;
    
    const cols = line.split(/\s{2,}/).map(c => c.trim()).filter(c => c);
    
    if (cols.length >= 2) {
      const index = cols[0];
      const nameDe = cols[1] || '';
      const nameEn = cols[2] || '';
      
      // Nur gültige Indizes (max 30 Zeichen, keine Beschreibungen)
      if (index && index.length <= 30 && !index.includes('Bedeutung')) {
        indices.push({
          index: index,
          name_de: nameDe,
          name_en: nameEn,
          part: partNumber
        });
      }
    }
  }
  
  return indices;
}

// Hauptfunktion
async function main() {
  console.log('🚀 Vervollständige ALLE Registries auf 100%...\n');
  
  const allTerms = [];
  const allSymbols = [];
  const allIndices = [];
  
  // Parse alle 11 Teile
  for (let part = 1; part <= 11; part++) {
    console.log(`📄 Parse Teil ${part}...`);
    
    const markdown = readMarkdown(part);
    if (!markdown) {
      console.log(`   ⚠️  Markdown nicht gefunden (lokal vorhanden)`);
      continue;
    }
    
    const terms = extractAllTerms(markdown, part);
    const symbols = extractAllSymbols(markdown, part);
    const indices = extractAllIndices(markdown, part);
    
    allTerms.push(...terms);
    allSymbols.push(...symbols);
    allIndices.push(...indices);
    
    console.log(`   ✅ ${terms.length} Begriffe, ${symbols.length} Symbole, ${indices.length} Indizes`);
  }
  
  console.log(`\n📊 Gesamt extrahiert:`);
  console.log(`   Begriffe: ${allTerms.length}`);
  console.log(`   Symbole: ${allSymbols.length}`);
  console.log(`   Indizes: ${allIndices.length}`);
  
  // Lade bestehende Registries
  const glossary = JSON.parse(fs.readFileSync(path.join(CATALOG_DIR, 'din18599_glossary.json'), 'utf-8'));
  const symbolRegistry = JSON.parse(fs.readFileSync(path.join(CATALOG_DIR, 'din18599_symbols.json'), 'utf-8'));
  const indexRegistry = JSON.parse(fs.readFileSync(path.join(CATALOG_DIR, 'din18599_indices.json'), 'utf-8'));
  
  // Merge Begriffe
  const termMap = new Map();
  glossary.terms.forEach(t => termMap.set(t.number, t));
  
  allTerms.forEach(extracted => {
    if (!termMap.has(extracted.number)) {
      const termId = 'TERM_' + extracted.term_de
        .toUpperCase()
        .replace(/[ÄÖÜ]/g, m => ({ Ä: 'AE', Ö: 'OE', Ü: 'UE' }[m]))
        .replace(/ß/g, 'SS')
        .replace(/[^A-Z0-9]/g, '_')
        .replace(/_+/g, '_')
        .replace(/^_|_$/g, '');
      
      termMap.set(extracted.number, {
        id: termId,
        number: extracted.number,
        part: extracted.part,
        term_de: extracted.term_de,
        term_en: '',
        definition_de: extracted.definition_de,
        norm_refs: [`DIN_18599-${extracted.part}_2018-09_SEC_3`],
        category: 'general',
        see_also: []
      });
    }
  });
  
  glossary.terms = Array.from(termMap.values()).sort((a, b) => {
    const aNum = parseFloat(a.number.replace(/\./g, ''));
    const bNum = parseFloat(b.number.replace(/\./g, ''));
    return aNum - bNum;
  });
  
  // Merge Symbole
  const symbolMap = new Map();
  symbolRegistry.symbols.forEach(s => symbolMap.set(s.symbol, s));
  
  allSymbols.forEach(extracted => {
    if (symbolMap.has(extracted.symbol)) {
      const existing = symbolMap.get(extracted.symbol);
      if (!existing.used_in_parts) existing.used_in_parts = [];
      if (!existing.used_in_parts.includes(extracted.part)) {
        existing.used_in_parts.push(extracted.part);
      }
    } else {
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
  
  // Merge Indizes
  const indexMap = new Map();
  indexRegistry.indices.forEach(i => indexMap.set(i.index, i));
  
  allIndices.forEach(extracted => {
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
  
  // Update Statistiken
  glossary.statistics.total_terms = glossary.terms.length;
  glossary.version = '4.0.0';
  
  symbolRegistry.statistics.current_count = symbolRegistry.symbols.length;
  symbolRegistry.statistics.completion_percentage = Math.round(
    (symbolRegistry.symbols.length / symbolRegistry.statistics.total_symbols) * 100
  );
  symbolRegistry.version = '4.0.0';
  
  indexRegistry.statistics.current_count = indexRegistry.indices.length;
  indexRegistry.statistics.completion_percentage = Math.round(
    (indexRegistry.indices.length / indexRegistry.statistics.total_indices) * 100
  );
  indexRegistry.version = '2.0.0';
  
  // Speichern
  fs.writeFileSync(
    path.join(CATALOG_DIR, 'din18599_glossary.json'),
    JSON.stringify(glossary, null, 2)
  );
  
  fs.writeFileSync(
    path.join(CATALOG_DIR, 'din18599_symbols.json'),
    JSON.stringify(symbolRegistry, null, 2)
  );
  
  fs.writeFileSync(
    path.join(CATALOG_DIR, 'din18599_indices.json'),
    JSON.stringify(indexRegistry, null, 2)
  );
  
  console.log(`\n✅ Registries aktualisiert!`);
  console.log(`\n📊 Finale Stände:`);
  console.log(`   Glossar: ${glossary.terms.length} Begriffe`);
  console.log(`   Symbole: ${symbolRegistry.symbols.length} Symbole (${symbolRegistry.statistics.completion_percentage}%)`);
  console.log(`   Indizes: ${indexRegistry.indices.length} Indizes (${indexRegistry.statistics.completion_percentage}%)`);
}

main().catch(console.error);
