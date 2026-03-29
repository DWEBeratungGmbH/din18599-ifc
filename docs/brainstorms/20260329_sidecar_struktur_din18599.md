# Brainstorm: Sidecar-Struktur an DIN 18599 anlehnen

**Datum:** 29. März 2026  
**Teilnehmer:** DWE Team + Cascade AI  
**Ziel:** Sidecar-Struktur an DIN 18599 Norm-Systematik anlehnen

---

## 🎯 Ausgangslage

**Was wir jetzt haben:**
- ✅ Vollständige DIN 18599 Registries (222 Begriffe, 562 Symbole, 735 Indizes, 45 Profile)
- ✅ Katalog-System (52 Materialien, 24 Konstruktionen)
- ✅ Aktuelles Schema v2.0 mit generischer Struktur

**Problem:**
- Aktuelle Struktur ist **generisch** (zones, elements, systems)
- DIN 18599 hat eine **klare Systematik** nach Teilen 1-11
- Wir könnten die Norm-Struktur **direkt abbilden**

---

## 📊 DIN 18599 Systematik (11 Teile)

### Teil 1: Allgemeine Bilanzierung
- Zonierung, Begriffe, Primärenergiefaktoren
- **→ Sidecar:** `meta`, `zones`, `primary_energy_factors`

### Teil 2: Heizen & Kühlen (Nutzenergie)
- Heizwärmebedarf, Kühlbedarf
- Transmissionswärmeverluste, solare Gewinne
- **→ Sidecar:** `thermal_envelope`, `heat_gains`, `heat_losses`

### Teil 3: Luftaufbereitung (RLT)
- Lüftungsanlagen, Wärmerückgewinnung
- **→ Sidecar:** `ventilation_systems`

### Teil 4: Beleuchtung
- Beleuchtungsenergie, Tageslichtnutzung
- **→ Sidecar:** `lighting_systems`

### Teil 5: Heizsysteme (Endenergie)
- Wärmeerzeuger, Verteilung, Übergabe
- **→ Sidecar:** `heating_systems`

### Teil 6: Lüftung Wohnungsbau
- Lüftungsanlagen, Luftheizung
- **→ Sidecar:** `ventilation_residential`

### Teil 7: RLT Nichtwohnungsbau
- Klimakältesysteme
- **→ Sidecar:** `hvac_non_residential`

### Teil 8: Warmwasser
- Trinkwarmwasserbereitung
- **→ Sidecar:** `domestic_hot_water`

### Teil 9: Stromerzeugung
- PV, KWK, Eigennutzung
- **→ Sidecar:** `electricity_generation`

### Teil 10: Nutzungsrandbedingungen
- Nutzungsprofile, Klimadaten
- **→ Sidecar:** `usage_conditions`, `climate_data`

### Teil 11: Gebäudeautomation
- Regelung, Steuerung
- **→ Sidecar:** `building_automation`

---

## 💡 IDEE: Norm-konforme Struktur

### Option A: Flache Struktur (aktuell)
```json
{
  "input": {
    "zones": [...],
    "elements": [...],
    "systems": {
      "heating": [...],
      "ventilation": [...],
      "lighting": [...]
    }
  }
}
```

**Vorteile:**
- ✅ Einfach zu verstehen
- ✅ Kompakt

**Nachteile:**
- ❌ Nicht norm-konform
- ❌ Keine klare Zuordnung zu DIN-Teilen
- ❌ Schwer erweiterbar

---

### Option B: DIN-Teil-basierte Struktur (NEU)
```json
{
  "input": {
    "part_1_general": {
      "zones": [...],
      "primary_energy_factors": {...}
    },
    "part_2_thermal": {
      "envelope": {
        "walls": [...],
        "roofs": [...],
        "floors": [...],
        "windows": [...]
      },
      "heat_gains": {
        "solar": {...},
        "internal": {...}
      },
      "heat_losses": {
        "transmission": {...},
        "ventilation": {...}
      }
    },
    "part_3_ventilation": {
      "systems": [...],
      "heat_recovery": {...}
    },
    "part_4_lighting": {
      "systems": [...],
      "daylight": {...}
    },
    "part_5_heating": {
      "generation": [...],
      "distribution": {...},
      "emission": {...}
    },
    "part_8_dhw": {
      "generation": [...],
      "distribution": {...},
      "circulation": {...}
    },
    "part_9_electricity": {
      "pv": [...],
      "chp": [...],
      "self_consumption": {...}
    },
    "part_10_conditions": {
      "usage_profiles": [...],
      "climate": {...}
    },
    "part_11_automation": {
      "controls": [...],
      "efficiency_factors": {...}
    }
  }
}
```

**Vorteile:**
- ✅ **Norm-konform** - direkte Zuordnung zu DIN-Teilen
- ✅ **Klar strukturiert** - jeder Teil hat seinen Bereich
- ✅ **Erweiterbar** - neue Teile einfach hinzufügbar
- ✅ **Validierbar** - Teil-spezifische Schemas möglich
- ✅ **Dokumentierbar** - Verweis auf DIN-Teil direkt

**Nachteile:**
- ❌ Komplexer
- ❌ Breaking Change von v2.0
- ❌ Mehr Verschachtelung

---

### Option C: Hybrid (EMPFEHLUNG)
```json
{
  "input": {
    "building": {
      "zones": [...],
      "climate": {...}
    },
    "envelope": {
      "walls": [...],
      "roofs": [...],
      "floors": [...],
      "windows": [...],
      "thermal_bridges": {...}
    },
    "systems": {
      "heating": {
        "generation": [...],
        "distribution": {...},
        "emission": {...}
      },
      "ventilation": {
        "systems": [...],
        "heat_recovery": {...}
      },
      "cooling": [...],
      "lighting": [...],
      "dhw": {
        "generation": [...],
        "distribution": {...}
      }
    },
    "electricity": {
      "pv": [...],
      "chp": [...],
      "battery": [...]
    },
    "automation": {
      "controls": [...],
      "efficiency_factors": {...}
    }
  }
}
```

**Vorteile:**
- ✅ **Norm-angelehnt** aber nicht starr
- ✅ **Lesbar** - logische Gruppierung
- ✅ **Flexibel** - kann erweitert werden
- ✅ **Migrierbar** - sanfter Übergang von v2.0

**Nachteile:**
- ⚠️ Kompromiss zwischen Norm und Usability

---

## 🔍 Detaillierte Analyse: Envelope-Struktur

### Aktuell (v2.0):
```json
{
  "elements": [
    {"id": "wall_1", "type": "wall", "u_value": 0.24, ...},
    {"id": "roof_1", "type": "roof", "u_value": 0.18, ...},
    {"id": "window_1", "type": "window", "u_value": 0.95, ...}
  ]
}
```

### Norm-konform (DIN 18599-2):
```json
{
  "envelope": {
    "opaque_elements": {
      "walls_external": [
        {
          "id": "wall_ext_sued",
          "construction_ref": "WALL_EXT_BRICK_WDVS_160",
          "area": 35.2,
          "orientation": 180,
          "adjacent_zone": "zone_eg",
          "boundary_condition": "exterior",
          "temperature_correction_factor": 1.0
        }
      ],
      "roofs": [...],
      "floors_ground": [...],
      "floors_basement_ceiling": [...]
    },
    "transparent_elements": {
      "windows": [
        {
          "id": "window_sued_01",
          "construction_ref": "WINDOW_TRIPLE_GLAZING",
          "area": 4.2,
          "orientation": 180,
          "g_value": 0.5,
          "frame_factor": 0.3,
          "shading": {
            "external": 0.7,
            "internal": 1.0
          }
        }
      ],
      "doors": [...]
    },
    "thermal_bridges": {
      "delta_u_wb": 0.05,
      "type": "DETAILED",
      "linear_bridges": [...]
    }
  }
}
```

**Vorteile der Norm-Struktur:**
- ✅ Klare Trennung opak/transparent
- ✅ Alle DIN 18599-2 Parameter direkt abbildbar
- ✅ Temperatur-Korrekturfaktoren (F_x) pro Element
- ✅ Wärmebrücken separat

---

## 🔧 Systems-Struktur (DIN 18599-5 bis -9)

### Aktuell (v2.0):
```json
{
  "systems": {
    "heating": [
      {"type": "gas_boiler", "efficiency": 0.85}
    ]
  }
}
```

### Norm-konform (DIN 18599-5):
```json
{
  "heating_system": {
    "generation": {
      "type": "gas_condensing_boiler",
      "fuel": "natural_gas",
      "nominal_power": 18.0,
      "efficiency_nominal": 0.95,
      "efficiency_part_load": 0.98,
      "installation_year": 2020,
      "location": "heated_space"
    },
    "distribution": {
      "type": "two_pipe_system",
      "insulation": "standard",
      "length_heated": 25.0,
      "length_unheated": 5.0,
      "temperature_supply": 55,
      "temperature_return": 45
    },
    "emission": {
      "type": "radiators",
      "control": "thermostatic_valves",
      "exponent": 1.3
    },
    "control": {
      "type": "weather_compensated",
      "night_setback": true,
      "room_temperature_control": "individual"
    },
    "zones_served": ["zone_eg", "zone_og"]
  }
}
```

**Vorteile:**
- ✅ Vollständige DIN 18599-5 Systematik
- ✅ Erzeugung, Verteilung, Übergabe, Regelung getrennt
- ✅ Alle Aufwandszahlen berechenbar

---

## 📋 Nutzungsprofile (DIN 18599-10)

### Aktuell (v2.0):
```json
{
  "zones": [
    {
      "usage_profile": "17"  // ❌ String, nicht validiert
    }
  ]
}
```

### v2.1 (mit Registry):
```json
{
  "zones": [
    {
      "usage_profile_ref": "PROFILE_NWG_17",  // ✅ Enum
      "usage_conditions": {
        "theta_i_h_soll": 20,
        "theta_i_c_soll": 26,
        "q_I": 7.0,
        "n_nutz": 0.5,
        "operating_hours": {
          "weekday": {"start": "08:00", "end": "18:00"},
          "weekend": {"start": null, "end": null}
        }
      }
    }
  ]
}
```

**Vorteile:**
- ✅ Alle DIN 18599-10 Parameter
- ✅ Betriebszeiten explizit
- ✅ Override möglich

---

## 🎯 VORSCHLAG: Schema v2.1 Struktur

### Top-Level:
```json
{
  "schema_info": {...},
  "meta": {...},
  
  "input": {
    "building": {
      "zones": [...],
      "climate": {...}
    },
    "envelope": {
      "opaque": {...},
      "transparent": {...},
      "thermal_bridges": {...}
    },
    "systems": {
      "heating": {...},
      "ventilation": {...},
      "cooling": {...},
      "lighting": {...},
      "dhw": {...}
    },
    "electricity": {...},
    "automation": {...}
  },
  
  "output": {...},
  "scenarios": [...]
}
```

### Mapping zu DIN-Teilen:
- `building.zones` → Teil 1
- `building.climate` → Teil 10
- `envelope.*` → Teil 2
- `systems.heating` → Teil 5
- `systems.ventilation` → Teil 3, 6, 7
- `systems.lighting` → Teil 4
- `systems.dhw` → Teil 8
- `electricity` → Teil 9
- `automation` → Teil 11

---

## ✅ ENTSCHEIDUNGEN

### 1. Envelope-Struktur
**Frage:** Opak/Transparent trennen oder gemeinsam?

**Optionen:**
- A) `elements: []` (aktuell, flach)
- B) `envelope: {opaque: [], transparent: []}` (norm-konform)
- C) `envelope: {walls: [], windows: []}` (hybrid)

**Empfehlung:** ?

---

### 2. Systems-Struktur
**Frage:** Erzeugung/Verteilung/Übergabe trennen?

**Optionen:**
- A) `heating: [{type, efficiency}]` (aktuell, einfach)
- B) `heating: {generation, distribution, emission, control}` (norm-konform)

**Empfehlung:** ?

---

### 3. Nutzungsprofile
**Frage:** Nur Referenz oder auch Details?

**Optionen:**
- A) `usage_profile_ref: "PROFILE_NWG_17"` (nur Referenz)
- B) `usage_profile_ref + usage_conditions: {...}` (Referenz + Override)

**Empfehlung:** B (bereits in v2.1)

---

### 4. Breaking Changes
**Frage:** Wie viel Breaking Change für v2.1?

**Optionen:**
- A) Minimal (nur Enum + required fields)
- B) Moderat (+ envelope-Struktur)
- C) Maximal (komplette Norm-Struktur)

**Empfehlung:** ?

---

## 🚀 NÄCHSTE SCHRITTE

1. **Entscheidungen treffen** (heute)
2. **Schema v2.1 finalisieren** (nächste Woche)
3. **Migration-Script** schreiben
4. **Demo-Projekt** anpassen
5. **Dokumentation** aktualisieren

---

## 💭 OFFENE FRAGEN

1. Wie wichtig ist **Norm-Konformität** vs. **Usability**?
2. Können wir **Breaking Changes** für v2.1 rechtfertigen?
3. Soll die Struktur **Software-neutral** bleiben oder **DIN-spezifisch** werden?
4. Wie gehen wir mit **IFC-Mapping** um (GUID-basiert bleibt)?

---

**Status:** Brainstorming  
**Nächster Schritt:** Entscheidungen treffen
