#!/usr/bin/env node
/**
 * DIN 18599 Source Parser
 * Extrahiert Begriffe, Symbole und Indizes aus Markdown-Dateien
 * und vervollständigt die Registry-Dateien auf 100%
 */

const fs = require('fs');
const path = require('path');

const SOURCES_DIR = path.join(__dirname, '../sources/markdown');
const CATALOG_DIR = path.join(__dirname, '../catalog');

// Hilfsfunktion: Markdown-Datei einlesen
function readMarkdown(partNumber) {
  const filename = `DIN18599-${partNumber.toString().padStart(2, '0')}.md`;
  const filepath = path.join(SOURCES_DIR, filename);
  return fs.readFileSync(filepath, 'utf-8');
}

// Hilfsfunktion: Begriffe aus Abschnitt 3.1 extrahieren
function extractTerms(markdown, partNumber) {
  const terms = [];
  
  // Regex für Begriffsdefinitionen: **3.1.X** gefolgt von **Begriff**
  const termRegex = /\*\*3\.1\.(\d+)\*\*\s*\n\s*\n\s*\*\*(.*?)\*\*\s*\n\s*\n([\s\S]*?)(?=\n\*\*3\.1\.\d+\*\*|\n\*\*3\.2|$)/g;
  
  let match;
  while ((match = termRegex.exec(markdown)) !== null) {
    const number = match[1];
    const term = match[2].trim();
    const definition = match[3].trim().split('\n')[0]; // Erste Zeile der Definition
    
    terms.push({
      number: `3.1.${number}`,
      term_de: term,
      definition_de: definition,
      part: partNumber
    });
  }
  
  return terms;
}

// Hilfsfunktion: Symbole aus Tabelle extrahieren
function extractSymbols(markdown, partNumber) {
  const symbols = [];
  
  // Suche nach Tabellen mit Symbolen (vereinfachte Extraktion)
  // Format: | Symbol | Bedeutung | Einheit |
  const tableRegex = /\|\s*Symbol\s*\|[\s\S]*?\n\|([\s\S]*?)(?=\n\n|\n\*\*|$)/gi;
  
  let match;
  while ((match = tableRegex.exec(markdown)) !== null) {
    const tableContent = match[1];
    const rows = tableContent.split('\n').filter(row => row.trim() && !row.includes('---'));
    
    rows.forEach(row => {
      const cols = row.split('|').map(c => c.trim()).filter(c => c);
      if (cols.length >= 3) {
        symbols.push({
          symbol: cols[0],
          name_de: cols[1],
          unit: cols[2],
          part: partNumber
        });
      }
    });
  }
  
  return symbols;
}

// Hauptfunktion
async function main() {
  console.log('🚀 Starte DIN 18599 Source Parser...\n');
  
  const allTerms = [];
  const allSymbols = [];
  
  // Parse alle 11 Teile
  for (let part = 1; part <= 11; part++) {
    console.log(`📄 Parse Teil ${part}...`);
    
    try {
      const markdown = readMarkdown(part);
      
      // Begriffe extrahieren
      const terms = extractTerms(markdown, part);
      allTerms.push(...terms);
      console.log(`   ✅ ${terms.length} Begriffe gefunden`);
      
      // Symbole extrahieren
      const symbols = extractSymbols(markdown, part);
      allSymbols.push(...symbols);
      console.log(`   ✅ ${symbols.length} Symbole gefunden`);
      
    } catch (error) {
      console.error(`   ❌ Fehler bei Teil ${part}:`, error.message);
    }
  }
  
  console.log(`\n📊 Gesamt:`);
  console.log(`   Begriffe: ${allTerms.length}`);
  console.log(`   Symbole: ${allSymbols.length}`);
  
  // Ergebnisse speichern
  const outputDir = path.join(__dirname, '../.temp');
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  fs.writeFileSync(
    path.join(outputDir, 'extracted-terms.json'),
    JSON.stringify(allTerms, null, 2)
  );
  
  fs.writeFileSync(
    path.join(outputDir, 'extracted-symbols.json'),
    JSON.stringify(allSymbols, null, 2)
  );
  
  console.log(`\n✅ Ergebnisse gespeichert in .temp/`);
  console.log(`   - extracted-terms.json`);
  console.log(`   - extracted-symbols.json`);
}

main().catch(console.error);
