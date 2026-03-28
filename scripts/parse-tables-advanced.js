#!/usr/bin/env node
/**
 * Advanced Table Parser für DIN 18599
 * Extrahiert Symbole und Indizes aus Markdown-Tabellen
 */

const fs = require('fs');
const path = require('path');

const SOURCES_DIR = path.join(__dirname, '../sources/markdown');
const OUTPUT_DIR = path.join(__dirname, '../.temp');

function readMarkdown(partNumber) {
  const filename = `DIN18599-${partNumber.toString().padStart(2, '0')}.md`;
  return fs.readFileSync(path.join(SOURCES_DIR, filename), 'utf-8');
}

// Extrahiere Symbol-Tabellen (Tabelle 1)
function extractSymbolTable(markdown, partNumber) {
  const symbols = [];
  
  // Suche nach "Tabelle 1" oder "Symbole und Einheiten"
  const tableMatch = markdown.match(/\*\*Tabelle 1.*?Symbole.*?\*\*\s*\n([\s\S]*?)(?=\n\*\*Tabelle 2|\n\*\*[A-Z]|$)/i);
  
  if (!tableMatch) return symbols;
  
  const tableContent = tableMatch[1];
  const lines = tableContent.split('\n');
  
  let currentSymbol = null;
  let currentNameDe = '';
  let currentNameEn = '';
  let currentUnit = '';
  
  for (const line of lines) {
    // Überspringe Trennlinien
    if (line.match(/^[\s-]+$/)) continue;
    if (line.includes('Symbol') && line.includes('Bedeutung')) continue;
    if (line.includes('Deutsch') && line.includes('English')) continue;
    
    // Parse Zeilen mit Daten
    const cols = line.split(/\s{2,}/).map(c => c.trim()).filter(c => c);
    
    if (cols.length >= 3) {
      // Zeile mit Symbol, Deutsch, English, Einheit
      const symbol = cols[0].replace(/\*/g, '').trim();
      if (symbol && symbol.length <= 10) {
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
    } else if (cols.length === 2 && !currentSymbol) {
      // Zeile nur mit Deutsch, English (Symbol fehlt - griechische Buchstaben)
      currentNameDe = cols[0] || '';
      currentNameEn = cols[1] || '';
    } else if (cols.length === 1 && currentSymbol) {
      // Fortsetzungszeile
      if (cols[0].match(/^[a-z]/)) {
        currentNameEn += ' ' + cols[0];
      }
    }
  }
  
  return symbols;
}

// Extrahiere Index-Tabellen (Tabelle 2)
function extractIndexTable(markdown, partNumber) {
  const indices = [];
  
  const tableMatch = markdown.match(/\*\*Tabelle 2.*?Indizes.*?\*\*\s*\n([\s\S]*?)(?=\n\*\*Tabelle 3|\n\*\*[A-Z]|\n## |$)/i);
  
  if (!tableMatch) return indices;
  
  const tableContent = tableMatch[1];
  const lines = tableContent.split('\n');
  
  for (const line of lines) {
    if (line.match(/^[\s-]+$/)) continue;
    if (line.includes('Index') && line.includes('Bedeutung')) continue;
    if (line.includes('Deutsch') && line.includes('English')) continue;
    
    const cols = line.split(/\s{2,}/).map(c => c.trim()).filter(c => c);
    
    if (cols.length >= 2) {
      const index = cols[0];
      const nameDe = cols[1] || '';
      const nameEn = cols[2] || '';
      
      if (index && index.length <= 20 && !index.includes('Bedeutung')) {
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
  console.log('🔍 Advanced Table Parser gestartet...\n');
  
  const allSymbols = [];
  const allIndices = [];
  
  for (let part = 1; part <= 11; part++) {
    console.log(`📄 Parse Teil ${part}...`);
    
    try {
      const markdown = readMarkdown(part);
      
      const symbols = extractSymbolTable(markdown, part);
      const indices = extractIndexTable(markdown, part);
      
      allSymbols.push(...symbols);
      allIndices.push(...indices);
      
      console.log(`   ✅ ${symbols.length} Symbole, ${indices.length} Indizes`);
      
    } catch (error) {
      console.error(`   ❌ Fehler: ${error.message}`);
    }
  }
  
  console.log(`\n📊 Gesamt:`);
  console.log(`   Symbole: ${allSymbols.length}`);
  console.log(`   Indizes: ${allIndices.length}`);
  
  // Speichern
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }
  
  fs.writeFileSync(
    path.join(OUTPUT_DIR, 'symbols-advanced.json'),
    JSON.stringify(allSymbols, null, 2)
  );
  
  fs.writeFileSync(
    path.join(OUTPUT_DIR, 'indices-advanced.json'),
    JSON.stringify(allIndices, null, 2)
  );
  
  console.log(`\n✅ Gespeichert in .temp/`);
}

main().catch(console.error);
