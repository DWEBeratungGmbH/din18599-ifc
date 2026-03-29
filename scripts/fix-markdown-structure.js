#!/usr/bin/env node
/**
 * Markdown Structure Fixer für DIN 18599
 * Formatiert Überschriften korrekt ohne Text zu ändern
 */

const fs = require('fs');
const path = require('path');

const SOURCES_DIR = path.join(__dirname, '../sources/markdown');

function fixMarkdownStructure(content, partNumber) {
  let lines = content.split('\n');
  let result = [];
  
  for (let i = 0; i < lines.length; i++) {
    let line = lines[i];
    
    // Hauptabschnitte: **1Anwendungsbereich** → # 1 Anwendungsbereich
    if (line.match(/^\*\*(\d+)([A-ZÄÖÜ].*?)\*\*$/)) {
      const match = line.match(/^\*\*(\d+)([A-ZÄÖÜ].*?)\*\*$/);
      result.push(`# ${match[1]} ${match[2]}`);
      continue;
    }
    
    // Unterabschnitte: **3.1Begriffe** → ## 3.1 Begriffe
    if (line.match(/^\*\*(\d+\.\d+)([A-ZÄÖÜ].*?)\*\*$/)) {
      const match = line.match(/^\*\*(\d+\.\d+)([A-ZÄÖÜ].*?)\*\*$/);
      result.push(`## ${match[1]} ${match[2]}`);
      continue;
    }
    
    // Unter-Unterabschnitte: **3.1.1** → ### 3.1.1
    if (line.match(/^\*\*(\d+\.\d+\.\d+)\*\*$/)) {
      const match = line.match(/^\*\*(\d+\.\d+\.\d+)\*\*$/);
      result.push(`### ${match[1]}`);
      continue;
    }
    
    // Unter-Unter-Unterabschnitte: **3.1.1.1** → #### 3.1.1.1
    if (line.match(/^\*\*(\d+\.\d+\.\d+\.\d+)\*\*$/)) {
      const match = line.match(/^\*\*(\d+\.\d+\.\d+\.\d+)\*\*$/);
      result.push(`#### ${match[1]}`);
      continue;
    }
    
    // Spezielle Abschnitte ohne Nummer
    if (line.match(/^\*\*(Vorwort|Änderungen|Frühere Ausgaben|Einleitung)\*\*$/)) {
      const match = line.match(/^\*\*(.*?)\*\*$/);
      result.push(`# ${match[1]}`);
      continue;
    }
    
    // Tabellen-Überschriften: **Tabelle 1 --- ...** → ### Tabelle 1 --- ...
    if (line.match(/^\*\*Tabelle \d+.*?\*\*$/)) {
      const match = line.match(/^\*\*(Tabelle \d+.*?)\*\*$/);
      result.push(`### ${match[1]}`);
      continue;
    }
    
    // Bild-Überschriften: **Bild 1 --- ...** → ### Bild 1 --- ...
    if (line.match(/^\*\*Bild \d+.*?\*\*$/)) {
      const match = line.match(/^\*\*(Bild \d+.*?)\*\*$/);
      result.push(`### ${match[1]}`);
      continue;
    }
    
    // Anhänge: **Anhang A** → # Anhang A
    if (line.match(/^\*\*Anhang [A-Z].*?\*\*$/)) {
      const match = line.match(/^\*\*(Anhang [A-Z].*?)\*\*$/);
      result.push(`# ${match[1]}`);
      continue;
    }
    
    // Literaturhinweise
    if (line.match(/^\*\*Literaturhinweise\*\*$/)) {
      result.push(`# Literaturhinweise`);
      continue;
    }
    
    // Alle anderen Zeilen unverändert übernehmen
    result.push(line);
  }
  
  return result.join('\n');
}

async function main() {
  console.log('🔧 Markdown-Struktur wird korrigiert...\n');
  
  for (let part = 1; part <= 11; part++) {
    const filename = `DIN18599-${part.toString().padStart(2, '0')}.md`;
    const filepath = path.join(SOURCES_DIR, filename);
    
    console.log(`📄 Verarbeite ${filename}...`);
    
    try {
      const content = fs.readFileSync(filepath, 'utf-8');
      const fixed = fixMarkdownStructure(content, part);
      
      // Backup erstellen
      const backupPath = filepath + '.backup';
      fs.writeFileSync(backupPath, content);
      
      // Korrigierte Version speichern
      fs.writeFileSync(filepath, fixed);
      
      console.log(`   ✅ Struktur korrigiert (Backup: ${filename}.backup)`);
      
    } catch (error) {
      console.error(`   ❌ Fehler: ${error.message}`);
    }
  }
  
  console.log('\n✅ Alle Markdown-Dateien strukturiert!');
  console.log('\n📝 Änderungen:');
  console.log('   - Hauptabschnitte: # 1 Anwendungsbereich');
  console.log('   - Unterabschnitte: ## 3.1 Begriffe');
  console.log('   - Nummerierte Begriffe: ### 3.1.1');
  console.log('   - Tabellen/Bilder: ### Tabelle 1 ---');
  console.log('   - Anhänge: # Anhang A');
  console.log('\n💾 Backups erstellt: *.md.backup');
}

main().catch(console.error);
