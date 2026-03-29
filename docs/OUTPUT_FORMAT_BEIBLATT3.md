# Output-Format nach DIN 18599 Beiblatt 3

**Version:** 1.0  
**Stand:** 29. März 2026  
**Quelle:** DIN/TS 18599 Beiblatt 3 (2018-09)

---

## 🎯 Zweck

Dieses Dokument beschreibt das **standardisierte Ausgabeformat** für Berechnungsergebnisse nach DIN 18599, basierend auf **Beiblatt 3**.

**Titel Beiblatt 3:**
> "Überführung der Berechnungsergebnisse einer Energiebilanz nach DIN/TS 18599 in ein standardisiertes Ausgabeformat"

---

## 📋 Scope: Input vs. Output vs. Kernel

### **Input (Definition) - Unser Datenmodell**
- Gebäudedaten (18 Kategorien, ~120 Felder)
- Systemdaten
- Nutzungsrandbedingungen
- **→ "Source of Truth" für Berechnung**
- **→ Siehe: `docs/brainstorms/20260329_dynamisches_datenmodell.md`**

### **Output (Snapshot) - Beiblatt 3**
- **Berechnungsergebnisse** nach DIN 18599
- **Kennwerte** (flächenbezogen, absolut)
- **Energiebilanzen** (Nutz-, End-, Primärenergie)
- **CO₂-Emissionen**
- **→ Dieses Dokument**

### **Kernel (Blackbox) - Nicht Teil des Formats**
- Berechnungsalgorithmus
- Software-spezifische Logik
- **→ Außerhalb unseres Scopes**

---

## 📊 Output-Struktur nach Beiblatt 3

### **Hauptabschnitte des Ausgabebogens:**

| Abschnitt | Tabellen | Inhalt |
|-----------|----------|--------|
| **1. Deckblatt** | - | Projekt, Auftraggeber, Bearbeiter |
| **2. Objektbeschreibung** | T.2.1 - T.2.5 | Gebäudedaten, Lage, Geometrie |
| **3. Bilanzierungsgrundlagen** | T.3.1 - T.3.4 | Gebäudeart, Flächen, Zonen, Systeme |
| **4. Energiebilanzen** | T.4.1 - T.4.4 | Nutz-, End-, Primärenergie, CO₂ |
| **5. Detaildaten Zonen** | T.5.1 - T.5.x | Zonierung, Nutzung, Geometrie |
| **6. Detaildaten Bauteile** | T.6.1 - T.6.x | Gebäudehülle, U-Werte |
| **7. Detaildaten Anlagen** | T.7.1 - T.7.x | Heizung, Lüftung, Kühlung, etc. |

---

## 🔢 Energiebilanzen (Abschnitt 8 / Kapitel 4)

### **8.1 Nutzenergiebedarf nach Zonen und Gewerken**

**Tabelle 32 (T.4.1.1): Flächenbezogen [kWh/(m²a)]**
```json
{
  "useful_energy": {
    "per_zone": [
      {
        "zone_id": "zone_eg",
        "heating": 45.2,
        "cooling": 0.0,
        "ventilation": 12.5,
        "lighting": 8.3,
        "dhw": 15.0
      }
    ]
  }
}
```

**Tabelle 33 (T.4.1.2): Absolut [kWh/a]**
```json
{
  "useful_energy_absolute": {
    "per_zone": [
      {
        "zone_id": "zone_eg",
        "heating": 3276,
        "cooling": 0,
        "ventilation": 906,
        "lighting": 602,
        "dhw": 1088
      }
    ]
  }
}
```

---

### **8.2 Endenergiebedarf**

#### **8.2.1 Bezugssystem (Tabelle 34)**
```json
{
  "final_energy": {
    "reference_system": "gross_calorific_value"  // Brennwert (Hs) oder Heizwert (Hi)
  }
}
```

#### **8.2.2 Nach Energieträgern**

**Tabelle 35: Nutzbar gemachte Umweltenergien [kWh/a]**
```json
{
  "final_energy": {
    "environmental_energy": {
      "solar_thermal": 1250,
      "ambient_heat": 3500,
      "geothermal": 0
    }
  }
}
```

**Tabelle 36: Strom [kWh/a]**
```json
{
  "final_energy": {
    "electricity": {
      "heating": 2500,
      "cooling": 0,
      "ventilation": 450,
      "lighting": 1200,
      "dhw": 800,
      "auxiliary": 350,
      "total_demand": 5300,
      "pv_production": -2100,
      "net_demand": 3200
    }
  }
}
```

**Tabelle 37: Andere Energieträger [kWh/a]**
```json
{
  "final_energy": {
    "other_carriers": {
      "natural_gas": {
        "heating": 15000,
        "dhw": 3500,
        "total": 18500
      },
      "district_heating": 0,
      "oil": 0,
      "wood_pellets": 0
    }
  }
}
```

#### **8.2.3 Nach Zonen und Gewerken (ohne Umweltenergien)**

**Tabellen 38-41: Detaillierte Aufschlüsselung**
```json
{
  "final_energy": {
    "by_zone_and_application": {
      "per_zone": [
        {
          "zone_id": "zone_eg",
          "heating": {
            "electricity": 1250,
            "natural_gas": 7500
          },
          "cooling": 0,
          "ventilation": 225,
          "lighting": 600,
          "dhw": 1750
        }
      ],
      "total": {
        "heating": 18500,
        "cooling": 0,
        "ventilation": 450,
        "lighting": 1200,
        "dhw": 3500
      }
    }
  }
}
```

#### **8.2.4 Nach Zonen und Gewerken (mit Umweltenergien)**

**Tabellen 42-45: Inkl. Umweltenergien**
```json
{
  "final_energy_with_environmental": {
    "per_zone": [
      {
        "zone_id": "zone_eg",
        "heating_total": 12250,  // inkl. Umweltwärme
        "environmental_share": 3500
      }
    ]
  }
}
```

---

### **8.3 Primärenergiebedarf**

#### **8.3.1 Bezugssystem (Tabelle 46)**
```json
{
  "primary_energy": {
    "reference_system": "non_renewable",  // nicht erneuerbar
    "factors_source": "GEG_2024"
  }
}
```

#### **8.3.2 Nach Energieträgern (nicht erneuerbar)**

**Tabellen 47-50: Primärenergie nach Energieträgern**
```json
{
  "primary_energy": {
    "non_renewable": {
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
        }
      },
      "total": 26110
    }
  }
}
```

#### **8.3.3 Nach Zonen und Gewerken**

**Tabellen 51-54: Detaillierte Aufschlüsselung**
```json
{
  "primary_energy": {
    "by_zone_and_application": {
      "per_zone": [
        {
          "zone_id": "zone_eg",
          "heating": 22850,
          "cooling": 0,
          "ventilation": 810,
          "lighting": 2160,
          "dhw": 4750
        }
      ],
      "total": {
        "heating": 22850,
        "cooling": 0,
        "ventilation": 810,
        "lighting": 2160,
        "dhw": 4750,
        "sum": 30570
      }
    }
  }
}
```

---

### **8.4 CO₂-Emissionen**

**Tabellen 55-58: CO₂-Emissionen nach Energieträgern**
```json
{
  "co2_emissions": {
    "by_carrier": {
      "electricity": {
        "final_energy": 3200,
        "factor": 0.485,
        "emissions": 1552
      },
      "natural_gas": {
        "final_energy": 18500,
        "factor": 0.201,
        "emissions": 3719
      }
    },
    "total": 5271
  }
}
```

**Tabellen 59-62: CO₂-Emissionen nach Zonen und Gewerken**
```json
{
  "co2_emissions": {
    "by_zone_and_application": {
      "per_zone": [
        {
          "zone_id": "zone_eg",
          "heating": 3719,
          "cooling": 0,
          "ventilation": 218,
          "lighting": 582,
          "dhw": 752
        }
      ],
      "total": 5271
    }
  }
}
```

---

## 📐 Kennwerte (flächenbezogen)

### **Spezifische Kennwerte [kWh/(m²a)]**

```json
{
  "specific_values": {
    "reference_area": 145.5,  // m²
    "useful_energy": {
      "heating": 45.2,
      "cooling": 0.0,
      "ventilation": 12.5,
      "lighting": 8.3,
      "dhw": 15.0,
      "total": 81.0
    },
    "final_energy": {
      "total": 163.4
    },
    "primary_energy": {
      "non_renewable": 179.5
    },
    "co2_emissions": {
      "total": 36.2  // kg/(m²a)
    }
  }
}
```

---

## 🏢 Zonendaten (Abschnitt 5)

### **Tabelle 70: Nutzungsrandbedingungen**

```json
{
  "zones": [
    {
      "id": "zone_eg",
      "name": "Erdgeschoss Wohnbereich",
      "usage_profile_ref": "PROFILE_RES_EFH",
      "area": 72.5,
      "volume": 217.5,
      "height": 3.0,
      "usage_conditions": {
        "setpoint_heating_c": 20,
        "setpoint_cooling_c": 26,
        "internal_loads_w_m2": 5.0,
        "air_change_rate_h": 0.5,
        "operating_hours_weekday": "00:00-24:00",
        "operating_hours_weekend": "00:00-24:00"
      }
    }
  ]
}
```

---

## 🏗️ Bauteil-Daten (Abschnitt 6)

### **Gebäudehülle**

```json
{
  "building_envelope": {
    "opaque_elements": {
      "walls_external": [
        {
          "id": "wall_ext_sued",
          "construction_ref": "WALL_EXT_BRICK_WDVS_160",
          "u_value": 0.21,
          "area": 35.2,
          "orientation": 180
        }
      ]
    },
    "transparent_elements": {
      "windows": [
        {
          "id": "window_sued_01",
          "construction_ref": "WINDOW_TRIPLE_GLAZING",
          "u_value": 0.7,
          "g_value": 0.5,
          "area": 4.2,
          "orientation": 180
        }
      ]
    },
    "thermal_bridges": {
      "method": "SIMPLIFIED",
      "delta_u_wb": 0.05
    }
  }
}
```

---

## ⚙️ Anlagen-Daten (Abschnitt 7)

### **Heizsystem**

```json
{
  "heating_system": {
    "generation": {
      "type": "air_water_heat_pump",
      "nominal_power_kw": 8.0,
      "cop_nominal": 3.5,
      "installation_year": 2024
    },
    "distribution": {
      "type": "two_pipe_system",
      "insulation_standard": "EnEV_2014"
    },
    "emission": {
      "type": "floor_heating",
      "control_type": "room_thermostat"
    },
    "control": {
      "type": "weather_compensated",
      "efficiency_factor": 0.95
    }
  }
}
```

---

## 📋 Vollständiges Output-Schema (JSON)

```json
{
  "schema_info": {
    "url": "https://din18599-ifc.de/schema/v2.1/output",
    "version": "2.1.0",
    "source": "DIN/TS 18599 Beiblatt 3"
  },
  
  "meta": {
    "calculation_date": "2026-03-29",
    "software": "DIN 18599 Reference Implementation",
    "software_version": "1.0.0",
    "norm_version": "DIN/TS 18599:2018-09",
    "climate_location": "TRY_2015_DE_04"
  },
  
  "output": {
    "useful_energy": {
      "per_zone": [...],
      "total": {...}
    },
    "final_energy": {
      "reference_system": "gross_calorific_value",
      "environmental_energy": {...},
      "electricity": {...},
      "other_carriers": {...},
      "by_zone_and_application": {...}
    },
    "primary_energy": {
      "reference_system": "non_renewable",
      "factors_source": "GEG_2024",
      "non_renewable": {...},
      "by_zone_and_application": {...}
    },
    "co2_emissions": {
      "by_carrier": {...},
      "by_zone_and_application": {...}
    },
    "specific_values": {
      "reference_area": 145.5,
      "useful_energy": {...},
      "final_energy": {...},
      "primary_energy": {...},
      "co2_emissions": {...}
    }
  }
}
```

---

## 🎯 Verwendung

### **Für Software-Entwickler:**
- Output-Format nach Beiblatt 3 implementieren
- Einheitliche Dokumentation unabhängig von Software
- Validierung gegen standardisiertes Format

### **Für Energieberater:**
- Vergleichbarkeit von Berechnungsergebnissen
- Nachvollziehbare Dokumentation
- Basis für Energieausweise und Nachweise

### **Für Behörden:**
- Standardisierte Nachweisführung
- Prüfbarkeit der Berechnungen
- GEG/BEG-Konformität

---

## 📚 Referenzen

- **DIN/TS 18599 Beiblatt 3** (2018-09) - Standardisiertes Ausgabeformat
- **DIN/TS 18599 Teil 1-11** - Berechnungsverfahren
- **Input-Datenmodell:** `docs/brainstorms/20260329_dynamisches_datenmodell.md`
- **Katalog-System:** `docs/CATALOG_GUIDE.md`

---

**Erstellt:** 29. März 2026  
**Version:** 1.0  
**Status:** Basierend auf Beiblatt 3 Analyse
