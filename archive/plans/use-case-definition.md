# Use-Case Definition: Geometrie für DIN 18599 Sidecar

**Datum:** 01.04.2026  
**Status:** DRAFT - Zur Diskussion

---

## 🎯 PROBLEM-STATEMENT

**Ausgangssituation:**
- DIN 18599 Sidecar benötigt Gebäudegeometrie für energetische Berechnungen
- Geometrie wird für Flächenberechnung, Orientierung und Visualisierung benötigt
- Zwei Szenarien: (1) Neubau/Planung, (2) Bestandsgebäude mit IFC

**Fragen:**
1. **Wer** erstellt die Geometrie?
2. **Wann** wird die Geometrie erstellt?
3. **Wo** wird die Geometrie gespeichert?
4. **Wie** wird die Geometrie verwendet?
5. **Warum** brauchen wir Geometrie überhaupt?

---

## 👥 STAKEHOLDER & USE-CASES

### Stakeholder 1: **Energieberater (DWE Beratung)**

**Szenario A: Neubau/Planung (kein IFC vorhanden)**
- Berater erstellt Gebäudemodell von Grund auf
- Einfache Geometrie (Rechteckige Geschosse, Satteldach)
- Schnelle Eingabe wichtiger als Details
- Ziel: Energieausweis, Förderantrag

**Anforderungen:**
- ✅ Schnelle Eingabe (Parametrisch: Länge, Breite, Höhe)
- ✅ Visualisierung (3D-Viewer für Plausibilitätsprüfung)
- ✅ Automatische Flächenberechnung
- ✅ Automatische Orientierung (Himmelsrichtung)
- ❌ Keine CAD-Kenntnisse erforderlich
- ❌ Keine komplexen Formen nötig

**Workflow:**
```
1. Berater öffnet DWEapp
2. Erstellt neues Projekt
3. Gibt Parameter ein:
   - Geschosse: EG (10m × 8m × 2.5m)
   - Dach: Satteldach (Neigung 37°)
   - Ausrichtung: Süd
4. System generiert Geometrie
5. Berater ergänzt U-Werte, Fenster, etc.
6. System berechnet Energiebedarf
7. Export: PDF (Energieausweis), JSON (Sidecar)
```

---

**Szenario B: Bestandsgebäude (IFC vorhanden)**
- Architekt liefert IFC-Datei (aus Revit/ArchiCAD)
- Komplexe Geometrie (Gauben, L-Form, etc.)
- Berater importiert IFC
- Ziel: Sanierungskonzept, Förderantrag

**Anforderungen:**
- ✅ IFC-Import
- ✅ Geometrie-Extraktion (Wände, Dächer, Flächen)
- ✅ Orientierung aus IFC
- ✅ Visualisierung (IFC-Viewer)
- ⚠️ Optional: Vereinfachung zu Parametric (für Editierbarkeit)
- ❌ Keine manuelle Geometrie-Eingabe

**Workflow:**
```
1. Berater erhält IFC-Datei vom Architekten
2. Importiert IFC in DWEapp
3. System extrahiert:
   - Wände (IFCWALLSTANDARDCASE)
   - Dächer (IFCROOF, IFCSLAB)
   - Flächen, Orientierung
4. Berater ergänzt energetische Daten:
   - U-Werte (aus IFC oder manuell)
   - Fenster (aus IFC oder manuell)
   - Technik (Heizung, Lüftung)
5. System berechnet Energiebedarf
6. Export: PDF, JSON + IFC (verlinkt)
```

---

### Stakeholder 2: **Architekt (Externe Partner)**

**Szenario C: BIM-Workflow (Revit/ArchiCAD → DWEapp)**
- Architekt plant Gebäude in Revit/ArchiCAD
- Exportiert IFC
- Energieberater importiert in DWEapp
- Ziel: Integrierter BIM-Workflow

**Anforderungen:**
- ✅ Standard IFC-Import (IFC2x3, IFC4)
- ✅ Rückverfolgbarkeit (IFC-GUIDs)
- ✅ Bidirektional: DWEapp → IFC Export
- ✅ Keine Vendor Lock-in
- ❌ Keine Custom-Formate

**Workflow:**
```
1. Architekt plant in Revit
2. Exportiert IFC
3. Energieberater importiert in DWEapp
4. Berater ergänzt energetische Daten
5. Berater exportiert IFC + Sidecar
6. Architekt importiert zurück in Revit
   → Energetische Daten als IFC-Properties
```

---

### Stakeholder 3: **Software-Entwickler (Drittanbieter)**

**Szenario D: API-Integration (Andere Software → DIN18599 Sidecar)**
- Drittanbieter-Software (z.B. Hottgenroth, Dämmwerk)
- Möchte DIN18599 Sidecar-Format nutzen
- Ziel: Interoperabilität

**Anforderungen:**
- ✅ Offener Standard (JSON Schema)
- ✅ Dokumentation
- ✅ Beispiele
- ✅ Validierung
- ❌ Keine proprietären Formate

---

## 🔍 ANFORDERUNGS-ANALYSE

### Funktionale Anforderungen

**F1: Geometrie-Eingabe (Parametrisch)**
- Einfache Formen: BOX, TRIANGULAR_PRISM, etc.
- Parameter: Länge, Breite, Höhe, Neigung
- Hierarchie: Geschosse, Dächer
- Ausrichtung: Kompass-Offset

**F2: IFC-Import**
- Standard IFC-Formate (IFC2x3, IFC4)
- Extraktion: Wände, Dächer, Flächen, Orientierung
- IFC-GUID Mapping

**F3: IFC-Export**
- Parametric → IFC Konvertierung
- Standard-konform
- Importierbar in Revit/ArchiCAD

**F4: Visualisierung**
- 3D-Viewer (Web-basiert)
- Parametric Geometrie
- IFC-Geometrie
- Orientierung (Kompass)

**F5: Flächenberechnung**
- Automatisch aus Geometrie
- Wände, Dächer, Böden
- Orientierung, Neigung

**F6: Daten-Export**
- JSON (Sidecar)
- IFC (Geometrie)
- PDF (Energieausweis)

---

### Nicht-Funktionale Anforderungen

**NF1: Einfachheit**
- Keine CAD-Kenntnisse erforderlich
- Schnelle Eingabe (<5 Min für EFH)
- Intuitive UI

**NF2: Standard-Konformität**
- IFC ISO 16739
- JSON Schema
- Open Source

**NF3: Performance**
- Geometrie-Generierung <1s
- IFC-Import <5s
- Viewer-Rendering <2s

**NF4: Interoperabilität**
- Import/Export IFC
- API für Drittanbieter
- Keine Vendor Lock-in

---

## 🎯 KERN-FRAGEN (Zur Diskussion)

### 1. **Primärer Use-Case?**

**Option A: Parametric-First (Neubau/Planung)**
- Fokus: Schnelle Eingabe, einfache Formen
- IFC-Export als Feature
- Zielgruppe: Energieberater ohne IFC

**Option B: IFC-First (Bestandsgebäude)**
- Fokus: IFC-Import, komplexe Geometrie
- Parametric als Fallback
- Zielgruppe: Energieberater mit IFC vom Architekten

**Option C: Hybrid (Beides gleichwertig)**
- Beide Modi unterstützen
- User wählt Workflow
- Zielgruppe: Alle

**→ Was ist der häufigste Fall bei DWE Beratung?**

---

### 2. **Geometrie-Speicherung?**

**Option A: JSON (Parametric Solids)**
```json
{
  "geometry": {
    "solids": [
      {"type": "BOX", "dimensions": {...}}
    ]
  }
}
```
- Vorteile: Einfach, editierbar, klein
- Nachteile: Custom-Format, kein Standard

**Option B: IFC (Standard)**
```json
{
  "meta": {
    "ifc_file": "building.ifc"
  }
}
```
- Vorteile: Standard, interoperabel
- Nachteile: Komplex, groß, nicht editierbar

**Option C: Hybrid (JSON + IFC)**
```json
{
  "geometry": {
    "solids": [...],
    "ifc_file": "building.ifc"
  }
}
```
- Vorteile: Flexibel
- Nachteile: Doppelte Datenhaltung, Sync-Probleme

**→ Was ist die Single Source of Truth?**

---

### 3. **Viewer-Technologie?**

**Option A: Custom Three.js (Parametric Solids)**
- Vorteile: Volle Kontrolle, einfach
- Nachteile: Maintenance, kein IFC-Support

**Option B: IFC.js (Standard IFC-Viewer)**
- Vorteile: Standard, IFC-Support, Community
- Nachteile: Komplex, Parametric muss zu IFC konvertiert werden

**Option C: Hybrid (Beide)**
- Vorteile: Flexibel
- Nachteile: Doppelte Maintenance

**→ Welche Geometrie wird häufiger visualisiert?**

---

### 4. **Editierbarkeit?**

**Szenario: User möchte Geometrie ändern**

**Option A: Parametric (Editierbar)**
```
User ändert: Länge 10m → 12m
System regeneriert: Geometrie + Flächen
```
- Vorteile: Einfach, schnell
- Nachteile: Nur einfache Formen

**Option B: IFC (Nicht editierbar)**
```
User muss: IFC in Revit öffnen → ändern → neu exportieren
```
- Vorteile: Volle Kontrolle in CAD
- Nachteile: Umständlich, CAD-Software nötig

**Option C: IFC-Simplified (Approximation editierbar)**
```
User ändert: Parametric Approximation
System regeneriert: IFC
```
- Vorteile: Editierbar + IFC-Export
- Nachteile: Verlust von Details

**→ Wie oft wird Geometrie nach Import geändert?**

---

### 5. **Scope: MVP vs. Full**

**MVP (Minimal Viable Product):**
- Parametric Solids (BOX + TRIANGULAR_PRISM)
- JSON Storage
- Custom Three.js Viewer
- Flächenberechnung
- Keine IFC-Integration

**Full (Alle Features):**
- Parametric Solids (4 Typen)
- IFC-Import/Export
- IFC.js Viewer
- Bidirektional: Parametric ↔ IFC
- API für Drittanbieter

**→ Was brauchen wir JETZT vs. SPÄTER?**

---

## 📊 ENTSCHEIDUNGS-MATRIX

| Kriterium | Parametric-First | IFC-First | Hybrid |
|-----------|------------------|-----------|--------|
| **Einfachheit** | ✅✅✅ | ⚠️ | ⚠️⚠️ |
| **Standard-Konformität** | ❌ | ✅✅✅ | ✅✅ |
| **Editierbarkeit** | ✅✅✅ | ❌ | ✅✅ |
| **Interoperabilität** | ❌ | ✅✅✅ | ✅✅ |
| **Performance** | ✅✅✅ | ⚠️ | ⚠️ |
| **Maintenance** | ✅✅ | ✅✅✅ | ❌ |
| **Time-to-Market** | ✅✅✅ | ⚠️⚠️ | ❌❌ |

---

## ✅ NÄCHSTE SCHRITTE

**Bitte beantworten:**

1. **Primärer Use-Case:** Neubau (Parametric) oder Bestand (IFC)?
2. **Häufigkeit:** Wie oft haben Projekte bereits IFC-Dateien?
3. **Editierbarkeit:** Wie oft wird Geometrie nach Import geändert?
4. **Priorität:** MVP schnell oder Full-Feature später?
5. **Zielgruppe:** Nur DWE intern oder auch externe Partner?

**Dann können wir entscheiden:**
- Architektur (Parametric vs. IFC vs. Hybrid)
- Technologie-Stack (Three.js vs. IFC.js)
- MVP-Scope (Was jetzt, was später)
