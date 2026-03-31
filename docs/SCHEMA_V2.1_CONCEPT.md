# Schema v2.1 - Konzept & Architektur

**Version:** 2.1.0  
**Stand:** 31. März 2026  
**Status:** Finalized

---

## 🎯 Zielsetzung

Schema v2.1 ist eine **komplette Neustrukturierung** des DIN 18599 IFC Sidecar Formats mit folgenden Zielen:

1. **Maximale Norm-Konformität** - Struktur folgt DIN 18599 Teilen 1-11
2. **Snapshot-Modell** - Input + Output + Scenarios in einer Datei
3. **Versionierung & Validierung** - Input-Hash für Aktualitätsprüfung
4. **Katalog-Integration** - Referenzen zu Materials, Constructions, Usage Profiles
5. **Robustheit** - Strikte Validierung, keine Duplikate, klare Constraints

---

## 🏗️ Architektur-Entscheidungen

### **1. Snapshot-Modell: Eine Datei = Input + Output + Scenarios**

**Problem v2.0:**
- Input und Output waren getrennt oder unklar strukturiert
- Keine Versionierung → Output konnte veraltet sein
- Keine klare Trennung zwischen Definition und Ergebnis

**Lösung v2.1:**
```json
{
  "input": {
    // Definition (Source of Truth) - PFLICHT
  },
  "scenarios": [
    // Varianten (Delta-Modell) - OPTIONAL
  ],
  "output": {
    // Berechnungsergebnisse - OPTIONAL
    "base": {...},
    "scenario_xyz": {...}
  }
}
```

**Vorteile:**
- ✅ Alles in einer Datei (keine Synchronisationsprobleme)
- ✅ Output pro Szenario (Vergleich möglich)
- ✅ Versionierung via Input-Hash
- ✅ Klare Trennung: Input (PFLICHT) vs. Output (OPTIONAL)

---

### **2. Input-Struktur: Hierarchisch nach DIN 18599**

**Problem v2.0:**
- Flache `elements[]` Array-Struktur
- Keine Unterscheidung zwischen opaken/transparenten Bauteilen
- Keine System-Detaillierung (Erzeugung/Verteilung/Übergabe)

**Lösung v2.1:**
```json
"input": {
  "building": {
    "zones": [...],
    "climate": {...}
  },
  "envelope": {
    "opaque_elements": {
      "walls_external": [...],
      "roofs": [...],
      "floors": [...]
    },
    "transparent_elements": {
      "windows": [...],
      "doors": [...]
    },
    "thermal_bridges": {...}
  },
  "systems": {
    "heating": {
      "generation": {...},
      "distribution": {...},
      "emission": {...},
      "control": {...}
    },
    "ventilation": {...},
    "cooling": {...},
    "lighting": {...},
    "dhw": {...}
  },
  "electricity": {...},
  "automation": {...},
  "primary_energy": {...}
}
```

**Vorteile:**
- ✅ Struktur folgt DIN 18599 Systematik
- ✅ Opak/Transparent getrennt (DIN 18599-2)
- ✅ System-Detaillierung (DIN 18599-5: e_g, e_d, e_ce)
- ✅ Neue Kategorien: Automation (Teil 11), Primary Energy

---

### **3. Output-Struktur: Nach Beiblatt 3**

**Problem v2.0:**
- Nur einfache Summen (final_energy_kwh_a, primary_energy_kwh_a)
- Keine Aufschlüsselung nach Zonen/Gewerken/Energieträgern
- Nicht standardisiert

**Lösung v2.1:**
```json
"output": {
  "base": {
    "meta": {
      "calculated_by": "Software XYZ",
      "calculation_date": "2026-03-31T10:00:00Z",
      "input_hash": "sha256:abc123...",
      "valid": true
    },
    "useful_energy": {
      // 8.1 Nutzenergiebedarf
      "per_zone": [...],
      "total": {...}
    },
    "final_energy": {
      // 8.2 Endenergiebedarf
      "by_carrier": {...},
      "by_zone_and_application": {...}
    },
    "primary_energy": {
      // 8.3 Primärenergiebedarf
      "by_carrier": {...},
      "by_zone_and_application": {...}
    },
    "co2_emissions": {
      // 8.4 CO₂-Emissionen
      "by_carrier": {...},
      "by_zone_and_application": {...}
    },
    "specific_values": {
      // Flächenbezogene Kennwerte
      "reference_area": 145.5,
      "final_energy": {"total": 163.4},
      "primary_energy": {"non_renewable": 179.5}
    }
  }
}
```

**Vorteile:**
- ✅ Standardisiert nach DIN 18599 Beiblatt 3
- ✅ Detaillierte Aufschlüsselung
- ✅ Vergleichbarkeit zwischen Software
- ✅ Audit-Trail (wer, wann, womit berechnet)

---

### **4. Versionierung & Validierung**

**Problem v2.0:**
- Keine Möglichkeit zu prüfen, ob Output noch aktuell ist
- Input-Änderungen → Output veraltet, aber nicht erkennbar

**Lösung v2.1:**
```json
"output": {
  "base": {
    "meta": {
      "input_hash": "sha256:abc123...",
      "valid": true  // false wenn Input geändert wurde
    }
  }
}
```

**Workflow:**
1. Input wird geändert
2. Neuer Hash wird berechnet
3. Hash ≠ gespeicherter Hash → `valid: false`
4. Software warnt: "⚠️ Berechnung veraltet - neu berechnen?"

**Vorteile:**
- ✅ Automatische Validierung
- ✅ Keine veralteten Ergebnisse
- ✅ Audit-Trail (Änderungshistorie)

---

### **5. Katalog-Integration**

**Problem v2.0:**
- Keine standardisierten Material-/Konstruktionsdaten
- Jeder Nutzer muss U-Werte selbst eingeben
- Keine Wiederverwendbarkeit

**Lösung v2.1:**
```json
// Input: Referenz zu Katalog
{
  "id": "wall_ext_sued",
  "construction_ref": "WALL_EXT_BRICK_WDVS_160"
}

// Katalog: catalog/constructions.json
{
  "id": "WALL_EXT_BRICK_WDVS_160",
  "name": "Außenwand Ziegel + WDVS 160mm",
  "u_value": 0.21,
  "layers": [...]
}
```

**Override-Mechanismus:**
```json
{
  "construction_ref": "WALL_EXT_BRICK_WDVS_160",
  "u_value": 0.18  // Override: Abweichung vom Katalog
}
```

**Vorteile:**
- ✅ Standardisierte Daten (52 Materialien, 24 Konstruktionen)
- ✅ Einfache Nutzung (Referenz statt manuelle Eingabe)
- ✅ Flexibilität (Override möglich)
- ✅ Wiederverwendbarkeit

---

## 📊 18 Kategorien (Input-Datenmodell)

### **Kategorie-Übersicht:**

| # | Kategorie | Beschreibung | DIN 18599 Teil |
|---|-----------|--------------|----------------|
| 1 | **Building** | Gebäude-Stammdaten | Teil 1 |
| 2 | **Zones** | Zonierung & Nutzung | Teil 1, 10 |
| 3 | **Envelope** | Gebäudehülle | Teil 2 |
| 4 | **Thermal Bridges** | Wärmebrücken | Teil 2 |
| 5 | **Heating** | Heizsystem | Teil 5 |
| 6 | **Ventilation** | Lüftung & Luftdichtheit | Teil 2, 6, 7 |
| 7 | **Cooling** | Kühlung | Teil 7 |
| 8 | **Lighting** | Beleuchtung | Teil 4 |
| 9 | **DHW** | Warmwasser | Teil 8 |
| 10 | **Electricity** | Stromerzeugung (PV) | Teil 9 |
| 11 | **Automation** | Gebäudeautomation (BACS) | Teil 11 |
| 12 | **Primary Energy** | Primärenergiefaktoren | Teil 1 |
| 13 | **Climate** | Klimadaten & Standort | Teil 10 |
| 14 | **Energy Data** | Energiekennwerte | - |
| 15 | **Consumption** | Verbrauchsdaten | Beiblatt 1 |
| 16 | **Internal Loads** | Interne Lasten | Teil 10 |
| 17 | **Heating Load** | Heizlast (DIN EN 12831) | - |
| 18 | **Measures** | Sanierungsmaßnahmen | - |

---

## 🔄 Delta-Modell für Szenarien

### **Konzept:**

```
Base Input (Ist-Zustand)
    ↓
    + Delta 1 (Änderungen) → Szenario 1
    + Delta 2 (Änderungen) → Szenario 2
```

### **Beispiel:**

```json
{
  "input": {
    // Base: Bestand (ungedämmt)
    "envelope": {
      "opaque_elements": {
        "walls_external": [
          {
            "id": "wall_ext_sued",
            "construction_ref": "WALL_EXT_BRICK_UNINSULATED"
          }
        ]
      }
    }
  },
  
  "scenarios": [
    {
      "id": "sanierung_stufe1",
      "name": "WDVS 160mm",
      "delta": {
        "elements": [
          {
            "id": "wall_ext_sued",
            "construction_ref": "WALL_EXT_BRICK_WDVS_160"  // Änderung!
          }
        ]
      }
    }
  ]
}
```

**Merge-Regel:** Base + Delta = Szenario (siehe MERGE_ALGORITHM.md)

---

## 🎯 Breaking Changes v2.0 → v2.1

### **Strukturelle Änderungen:**

1. **`elements[]` → `envelope.opaque_elements.*[]`**
   - Hierarchische Struktur statt flaches Array
   - Trennung opak/transparent

2. **`systems[]` → `systems.heating/ventilation/...`**
   - Detaillierte System-Struktur
   - Erzeugung/Verteilung/Übergabe/Regelung

3. **`output` → `output.base` + `output.scenario_*`**
   - Output pro Szenario
   - Struktur nach Beiblatt 3

4. **Primärenergiefaktoren verschoben**
   - Von `output` nach `input.primary_energy`
   - Randbedingungen gehören zu Input

### **Neue Felder:**

- `automation.*` - Gebäudeautomation (BACS)
- `primary_energy.factors.*` - Primärenergiefaktoren
- `primary_energy.co2_factors.*` - CO₂-Faktoren
- `output.*.meta.input_hash` - Validierung
- `output.*.savings.*` - Einsparungen vs. Base

### **Strikte Validierung:**

- `required: ["id"]` auf allen Bauteilen
- `uniqueItems: true` auf ID-Arrays
- `additionalProperties: false` (keine unbekannten Felder)
- Enum-Constraints (usage_profile, BACS-Klasse, etc.)

---

## 📐 LOD (Level of Detail)

### **Dynamisches Modell:**

LOD ergibt sich aus **Vollständigkeit der Daten**, nicht aus starren Levels:

| LOD | Beschreibung | Typische Felder |
|-----|--------------|-----------------|
| **100** | Energieausweis-Daten | Adresse, Baujahr, Fläche, Energiekennwerte |
| **200** | + Bauteil-Übersicht | Zonen, Ø U-Werte, Heizungssystem |
| **300** | + Detaillierte Bauteile | Einzelne Bauteile mit IFC GUID, Orientierungen |

**Vorteil:** Gleiche Datei kann von LOD 100 → 300 erweitert werden

---

## 🔗 IFC-Verknüpfung

### **GUID-basiertes Mapping:**

```json
{
  "id": "wall_ext_sued",
  "ifc_guid": "2Uj8Lq3Vr9QxPkXr4bN8FD",  // Verknüpfung zu IFC
  "construction_ref": "WALL_EXT_BRICK_WDVS_160"
}
```

**Vorteile:**
- ✅ Eindeutige Zuordnung Sidecar ↔ IFC
- ✅ Geometrie aus IFC, Physik aus Sidecar
- ✅ Software-neutral

---

## 🎯 Erfolgs-Kriterien

### **Schema v2.1 ist erfolgreich, wenn:**

1. ✅ Alle kritischen Fixes implementiert (required, uniqueItems, etc.)
2. ✅ Struktur folgt DIN 18599 Systematik
3. ✅ Output nach Beiblatt 3 strukturiert
4. ✅ Versionierung funktioniert (Input-Hash)
5. ✅ Katalog-Integration funktioniert
6. ✅ Migration v2.0 → v2.1 möglich
7. ✅ Externe Validierung positiv (min. 1 Reviewer)

---

## 📚 Referenzen

- **JSON Schema:** `schema/v2.1-complete.json`
- **Guide:** `docs/SCHEMA_V2.1_GUIDE.md`
- **Output-Format:** `docs/OUTPUT_FORMAT_BEIBLATT3.md`
- **Merge-Algorithmus:** `docs/MERGE_ALGORITHM.md`
- **Migration:** `docs/MIGRATION_GUIDE_v2.0_to_v2.1.md`
- **Katalog:** `docs/CATALOG_GUIDE.md`

---

## ✅ Status

**Schema v2.1:** ✅ **FINALIZED** (31. März 2026)

- ✅ Konzept definiert
- ✅ JSON Schema erstellt
- ✅ Dokumentation komplett
- ✅ Katalog-System integriert
- ⏳ Migration-Script (in Arbeit)
- ⏳ Demo-Beispiel (in Arbeit)

---

**Erstellt:** 31. März 2026  
**Version:** 2.1.0  
**Status:** Production Ready
