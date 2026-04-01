# 📚 Quellen-Index - DIN 18599 IFC Projekt

> **Letzte Aktualisierung:** 2026-03-31  
> **Zweck:** Zentrale Übersicht aller Quellen, Normen und Referenzdokumente

---

## 📖 Normative Dokumente

### DIN V 18599 (Energetische Bewertung von Gebäuden)

| Dokument | Typ | Pfad | Beschreibung |
|----------|-----|------|--------------|
| **Leitfaden Bilanzierung DIN V 18599 (2023)** | PDF | `/sources/Leitfaden_Bilanzierung_DIN_V_18599_2023_WEB.pdf` | Offizieller Leitfaden zur energetischen Gebäudebilanzierung nach DIN V 18599 |

**Wichtige Kapitel:**
- **Kapitel 6:** Berechnung der thermischen Hüllfläche
  - 6.1: Abmessungen und Maßbezüge (horizontal/vertikal)
  - 6.1.3: Vorteile und Konsequenzen
  - 6.1.4: Innenbauteile zu benachbarten konditionierten Zonen
  - 6.1.5: Charakteristisches Bodenplattenmaß

**Zitiert in:**
- `/viewer/src/App.tsx` - Netto-Wandflächen-Berechnung
- `/.cascade/rules.md` - Thermische Hüllfläche Definition

---

## 📁 Verzeichnisstruktur

```
/opt/din18599-ifc/sources/
├── INDEX.md                                           # Dieser Index
├── Leitfaden_Bilanzierung_DIN_V_18599_2023_WEB.pdf   # Hauptquelle
├── docx/                                              # Word-Dokumente (leer)
├── images/                                            # Bilder/Diagramme (leer)
└── markdown/                                          # Markdown-Konvertierungen (gitignored)
```

---

## 🔗 Verwandte Dokumentation

### Projekt-Dokumentation
- `/docs/ROADMAP.md` - Projekt-Roadmap und Meilensteine
- `/docs/PARAMETER_MATRIX.md` - Parameter-Definition für JSON Schema
- `/docs/BREP_GEOMETRY.md` - B-Rep Geometrie-Konzepte
- `/docs/brainstorms/20260331_phase3_viewer_mvp.md` - Viewer MVP Brainstorm

### Implementierung
- `/viewer/` - React Three Fiber Viewer (Phase 3)
- `/api/` - FastAPI Backend für Berechnungen
- `/schema/` - JSON Schema Definitionen (v2.1)

---

## 📝 Verwendungshinweise

### Zitierformat
Bei Referenzierung von Quellen in Code oder Dokumentation:

```typescript
// Quelle: Leitfaden DIN V 18599 (2023), Kapitel 6.1 - Maßbezüge
const netWallArea = wall.area - windowArea
```

### Markdown-Konvertierung
Die `/sources/markdown/` Ordner enthält automatisch generierte Markdown-Versionen der PDFs (gitignored). Diese werden für:
- Schnelle Textsuche
- Code-Referenzierung
- AI-Kontext

**Konvertierung:**
```bash
# PDF → Markdown (falls benötigt)
# Tool: pdf2md oder ähnlich
```

---

## 🔄 Aktualisierung

**Neue Quelle hinzufügen:**
1. Datei in `/sources/` ablegen
2. Diesen Index aktualisieren
3. Relevante Kapitel/Abschnitte dokumentieren
4. Verwendung in Code/Docs verlinken

**Änderungsprotokoll:**
- `2026-03-31` - Initiale Erstellung mit Leitfaden DIN V 18599 (2023)

---

## 📊 Statistik

- **PDFs:** 1
- **Markdown:** 0 (gitignored)
- **Bilder:** 0
- **Word-Docs:** 0

---

## 🎯 Nächste Schritte

- [ ] Weitere Norm-Teile hinzufügen (DIN V 18599-1 bis -10)
- [ ] Katalog-Quellen dokumentieren (EVEBI, etc.)
- [ ] Beispiel-Projekte als Referenz
- [ ] IFC-Spezifikationen (ISO 16739)

---

**Maintainer:** DWE Beratung GmbH  
**Lizenz:** MIT (siehe `/LICENSE`)
