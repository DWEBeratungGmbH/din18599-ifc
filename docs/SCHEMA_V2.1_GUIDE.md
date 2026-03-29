# Schema v2.1 - Vollständiger Guide

**Version:** 2.1.0  
**Stand:** 29. März 2026  
**Status:** Production Ready

---

## 🎯 Überblick

Schema v2.1 ist das **vollständige Datenformat** für energetische Gebäudedaten nach DIN 18599 mit:

- ✅ **Input (Definition):** 18 Kategorien, ~120 Felder - Source of Truth
- ✅ **Output (Snapshot):** Berechnungsergebnisse nach Beiblatt 3 - OPTIONAL
- ✅ **Scenarios (Varianten):** Delta-Modell für Sanierungsszenarien
- ✅ **Versionierung:** Input-Hash für Validierung
- ✅ **Katalog-System:** Referenzen zu Materials, Constructions, Usage Profiles

---

## 📋 Grundstruktur

```json
{
  "schema_info": {
    "url": "https://din18599-ifc.de/schema/v2.1/complete",
    "version": "2.1.0"
  },
  
  "meta": {
    "project_name": "...",
    "version": "1.0.0",
    "lod": "300"
  },
  
  "input": {
    // PFLICHT: Gebäudedaten (18 Kategorien)
  },
  
  "scenarios": [
    // OPTIONAL: Varianten (Delta-Modell)
  ],
  
  "output": {
    // OPTIONAL: Berechnungsergebnisse
    "base": {...},
    "scenario_xyz": {...}
  }
}
```

---

## 🏗️ Input-Struktur (18 Kategorien)

### **1. Building (Gebäude-Stammdaten)**
```json
"input": {
  "building": {
    "address": {
      "street": "Musterstraße 1",
      "zip": "10115",
      "city": "Berlin",
      "country": "DE"
    },
    "construction_year": 1978,
    "heated_area": 145.5,
    "zones": [...]
  }
}
```

### **2. Envelope (Gebäudehülle)**
```json
"envelope": {
  "opaque_elements": {
    "walls_external": [
      {
        "id": "wall_ext_sued",
        "ifc_guid": "2Uj8Lq3Vr9QxPkXr4bN8FD",
        "construction_ref": "WALL_EXT_BRICK_UNINSULATED",
        "area": 35.2,
        "orientation": 180
      }
    ]
  },
  "transparent_elements": {
    "windows": [...]
  },
  "thermal_bridges": {
    "method": "SIMPLIFIED",
    "delta_u_wb": 0.05
  }
}
```

### **3. Systems (Technische Anlagen)**
```json
"systems": {
  "heating": {
    "generation": {
      "type": "gas_boiler",
      "nominal_power_kw": 15.0,
      "efficiency": 0.85
    },
    "distribution": {...},
    "emission": {...},
    "control": {...}
  },
  "ventilation": {...},
  "cooling": {...},
  "lighting": {...},
  "dhw": {...}
}
```

### **4. Automation (Gebäudeautomation)**
```json
"automation": {
  "installed": true,
  "bacs_class": "C",
  "efficiency_factor_heating": 0.95
}
```

### **5. Primary Energy (Primärenergiefaktoren)**
```json
"primary_energy": {
  "source": "GEG_2024",
  "reference_year": 2024,
  "factors": {
    "electricity": 1.8,
    "natural_gas": 1.1
  },
  "co2_factors": {
    "electricity": 0.485,
    "natural_gas": 0.201
  }
}
```

---

## 🎭 Scenarios (Delta-Modell)

```json
"scenarios": [
  {
    "id": "sanierung_stufe1",
    "name": "Sanierung Stufe 1: WDVS + Fenster",
    "priority": 1,
    "timeline": 2026,
    "delta": {
      "elements": [
        {
          "id": "wall_ext_sued",
          "construction_ref": "WALL_EXT_BRICK_WDVS_160"  // Änderung!
        },
        {
          "id": "window_sued_01",
          "construction_ref": "WINDOW_TRIPLE_GLAZING"  // Änderung!
        }
      ]
    }
  }
]
```

**Prinzip:**
- Base Input = Ist-Zustand
- Scenario = Base + Delta
- Output wird für Base UND jedes Scenario berechnet

---

## 📊 Output-Struktur (nach Beiblatt 3)

```json
"output": {
  "base": {
    "meta": {
      "calculated_by": "Hottgenroth EnEV",
      "calculation_date": "2026-03-29T14:30:00Z",
      "input_hash": "sha256:abc123...",
      "valid": true
    },
    "useful_energy": {
      "per_zone": [...],
      "total": {
        "heating": 3276,
        "cooling": 0,
        "ventilation": 906,
        "lighting": 602,
        "dhw": 1088
      }
    },
    "final_energy": {
      "by_carrier": {
        "electricity": {
          "total_demand": 5300,
          "pv_production": -2100,
          "net_demand": 3200
        },
        "natural_gas": {
          "total": 18500
        }
      }
    },
    "primary_energy": {
      "by_carrier": {
        "electricity": {
          "final_energy": 3200,
          "factor": 1.8,
          "primary_energy": 5760
        },
        "natural_gas": {
          "final_energy": 18500,
          "factor": 1.1,
          "primary_energy": 20350
        },
        "total": 26110
      }
    },
    "co2_emissions": {
      "total": 5271
    },
    "specific_values": {
      "reference_area": 145.5,
      "final_energy": {
        "total": 163.4  // kWh/(m²a)
      },
      "primary_energy": {
        "non_renewable": 179.5
      }
    }
  },
  
  "scenario_sanierung_stufe1": {
    "meta": {...},
    "useful_energy": {...},
    "final_energy": {...},
    "primary_energy": {
      "total": 18650  // Reduziert!
    },
    "savings": {
      "final_energy_percent": 42.8,
      "co2_percent": 42.8,
      "cost_annual_euro": 870
    }
  }
}
```

---

## 🔄 Versionierung & Validierung

### **Input-Hash für Validierung**

```json
"output": {
  "base": {
    "meta": {
      "input_hash": "sha256:abc123...",
      "valid": true  // ✅ Output ist aktuell
    }
  }
}
```

**Workflow:**
1. Input wird geändert
2. Neuer Hash wird berechnet
3. Wenn Hash ≠ gespeicherter Hash → `valid: false`
4. Software warnt: "⚠️ Berechnung veraltet - neu berechnen?"

### **Versionshistorie**

```json
"meta": {
  "version": "1.2.0",
  "version_history": [
    {
      "version": "1.0.0",
      "date": "2026-03-15T10:00:00Z",
      "changes": "Initiale Erfassung",
      "author": "Max Mustermann"
    },
    {
      "version": "1.1.0",
      "date": "2026-03-20T14:30:00Z",
      "changes": "WDVS-Dämmung hinzugefügt"
    },
    {
      "version": "1.2.0",
      "date": "2026-03-29T09:15:00Z",
      "changes": "Fenster auf Dreifachverglasung"
    }
  ]
}
```

---

## 📐 LOD (Level of Detail)

```json
"meta": {
  "lod": "300"
}
```

| LOD | Beschreibung | Typische Felder |
|-----|--------------|-----------------|
| **100** | Energieausweis-Daten | Adresse, Baujahr, Fläche, Energiekennwerte, Verbrauch |
| **200** | + Bauteil-Übersicht | Zonen, Ø U-Werte, Heizungssystem, Klimaregion |
| **300** | + Detaillierte Bauteile | Einzelne Bauteile mit IFC GUID, exakte Orientierungen |

**Dynamisches Modell:**
- Felder können schrittweise ergänzt werden
- LOD ergibt sich aus Vollständigkeit
- Gleiche Datei kann von LOD 100 → 300 erweitert werden

---

## 🔗 Katalog-Referenzen

### **Construction Reference**
```json
{
  "id": "wall_ext_sued",
  "construction_ref": "WALL_EXT_BRICK_WDVS_160"
}
```

**Katalog:** `catalog/constructions.json`

### **Usage Profile Reference**
```json
{
  "zone_id": "zone_eg",
  "usage_profile_ref": "PROFILE_RES_EFH"
}
```

**Katalog:** `catalog/din18599_usage_profiles.json`

### **Override-Mechanismus**
```json
{
  "construction_ref": "WALL_EXT_BRICK_WDVS_160",
  "u_value": 0.18  // Override: Abweichung vom Katalog
}
```

---

## 🎯 Use Cases

### **Use Case 1: Nur Input (Standard)**
```json
{
  "schema_info": {...},
  "meta": {...},
  "input": {...}
  // Kein output - wird extern berechnet
}
```

### **Use Case 2: Input + Output (Snapshot)**
```json
{
  "schema_info": {...},
  "meta": {...},
  "input": {...},
  "output": {
    "base": {...}
  }
}
```

### **Use Case 3: Input + Scenarios + Output**
```json
{
  "schema_info": {...},
  "meta": {...},
  "input": {...},
  "scenarios": [...],
  "output": {
    "base": {...},
    "scenario_sanierung_stufe1": {...},
    "scenario_sanierung_stufe2": {...}
  }
}
```

---

## 🚀 Migration von v2.0 → v2.1

### **Hauptänderungen:**

1. **Input-Struktur hierarchisch**
   - `elements[]` → `envelope.opaque_elements.*[]`
   - Neue Kategorien: `automation`, `primary_energy`

2. **Output-Struktur nach Beiblatt 3**
   - Detaillierte Aufschlüsselung
   - Nutz-/End-/Primärenergie getrennt
   - Output pro Szenario

3. **Primärenergiefaktoren verschoben**
   - Von `output` nach `input.primary_energy`

4. **Versionierung hinzugefügt**
   - Input-Hash für Validierung
   - Versionshistorie

### **Migration-Script:**
```bash
node scripts/migrate-v2.0-to-v2.1.js input.din18599.json output.din18599.json
```

---

## 📚 Referenzen

- **Schema:** `schema/v2.1-complete.json`
- **Kataloge:** `catalog/`
- **Beispiele:** `examples/`
- **Dokumentation:**
  - `docs/CATALOG_GUIDE.md`
  - `docs/OUTPUT_FORMAT_BEIBLATT3.md`
  - `docs/brainstorms/20260329_dynamisches_datenmodell.md`

---

**Erstellt:** 29. März 2026  
**Version:** 2.1.0  
**Status:** Production Ready
