# LOD-Scope Definition für DIN 18599 Sidecar

**Datum:** 29. März 2026 (Nachmittag)  
**Thema:** Level of Detail (LOD) Abgrenzung für energetische Gebäudeakte  
**Ziel:** Klare Definition, welche Informationen zu welchem LOD gehören

---

## 🎯 Ausgangslage

**Problem:**
- Aktuelles Schema hat `"lod": "300"` als freien String
- Keine klare Definition, was LOD 100, 200, 300, 400 bedeutet
- Welche Felder sind bei welchem LOD required?
- Wie detailliert müssen Bauteile/Systeme beschrieben werden?

**Referenzen:**
- IFC LOD-Konzept (100-500)
- BIM-Richtlinien (BMVI, planen-bauen 4.0)
- DIN 18599 Anforderungen
- Energieausweise (Bedarfs- vs. Verbrauchsausweis)

---

## 📊 LOD-Stufen im BIM-Kontext

### IFC/BIM LOD-Standard:

| LOD | Name | Geometrie | Attribute | Verwendung |
|-----|------|-----------|-----------|------------|
| **100** | Konzept | Volumenkörper | Grobe Kennwerte | Machbarkeitsstudie |
| **200** | Entwurf | Vereinfachte Geometrie | Typische Werte | Vorentwurf |
| **300** | Ausführung | Detaillierte Geometrie | Spezifische Werte | Genehmigung |
| **400** | Fertigung | Fertigungsgeometrie | As-Built Daten | Ausführung |
| **500** | As-Built | Bestandsgeometrie | Vermessene Daten | Betrieb |

---

## 💡 LOD-Konzept für DIN 18599 Sidecar

### Frage 1: Welche LODs brauchen wir?

**Option A: IFC-LODs übernehmen (100-500)**
- ✅ Standard-konform
- ❌ Zu viele Stufen für Energieberechnung?

**Option B: Vereinfachte LODs (100, 300, 500)**
- ✅ Fokus auf relevante Stufen
- ✅ Weniger Komplexität

**Option C: Energie-spezifische LODs**
- LOD-E1: Energieausweis Bedarfsausweis (vereinfacht)
- LOD-E2: Energieausweis Bedarfsausweis (detailliert)
- LOD-E3: Energieberatung (DIN 18599 vollständig)
- LOD-E4: Monitoring (Verbrauchsdaten)

---

## 🔍 Detaillierte Analyse: Was gehört zu welchem LOD?

### LOD 100: Konzept / Machbarkeitsstudie

**Ziel:** Grobe Energieabschätzung, Variantenvergleich

**Geometrie:**
- Brutto-Grundfläche (BGF)
- Brutto-Rauminhalt (BRI)
- Hüllfläche (pauschal: A/V-Verhältnis)
- KEINE detaillierten Bauteile

**Bauphysik:**
- Pauschalwerte U-Wert (z.B. "unsanierter Altbau")
- Keine Schichtaufbauten
- Keine Wärmebrücken

**Systeme:**
- Heizungstyp (z.B. "Gaskessel")
- Baujahr
- KEINE Verteilung/Übergabe

**Nutzung:**
- Gebäudetyp (Wohn/Nichtwohn)
- Grobe Nutzung (z.B. "Büro")

**Beispiel:**
```json
{
  "lod": "100",
  "building": {
    "type": "residential",
    "gross_floor_area": 500,
    "gross_volume": 1500,
    "av_ratio": 0.8,
    "construction_year": 1978,
    "u_value_avg_estimated": 1.2
  },
  "systems": {
    "heating": {
      "type": "gas_boiler",
      "installation_year": 1995
    }
  }
}
```

**Verwendung:**
- Machbarkeitsstudie
- Grobe Kostenabschätzung
- Variantenvergleich (Sanierung ja/nein)

---

### LOD 200: Vorentwurf / Energieausweis (vereinfacht)

**Ziel:** Energieausweis Bedarfsausweis nach Tabellenwerten

**Geometrie:**
- Nettogrundfläche (NGF) nach Zonen
- Hüllflächen nach Bauteiltyp (Wand, Dach, Boden, Fenster)
- Orientierung (N/O/S/W)
- KEINE detaillierten Schichtaufbauten

**Bauphysik:**
- U-Werte aus Katalog oder Tabellenwerten
- Fensterflächen mit Orientierung
- Wärmebrücken pauschal (ΔU_WB)

**Systeme:**
- Heizung: Typ, Baujahr, Nennleistung
- Warmwasser: Typ
- Lüftung: Typ (wenn vorhanden)

**Nutzung:**
- Nutzungsprofil aus DIN 18599-10
- Betriebszeiten (Standard)

**Beispiel:**
```json
{
  "lod": "200",
  "building": {
    "zones": [
      {
        "usage_profile_ref": "PROFILE_RES_EFH",
        "area": 145.5
      }
    ]
  },
  "envelope": {
    "opaque_elements": {
      "walls_external": [
        {
          "construction_ref": "WALL_EXT_BRICK_UNINSULATED",
          "area": 167.7,
          "orientation_avg": 180
        }
      ]
    },
    "transparent_elements": {
      "windows": [
        {
          "construction_ref": "WINDOW_DOUBLE_GLAZING",
          "area": 21.5,
          "orientation_avg": 180
        }
      ]
    },
    "thermal_bridges": {
      "method": "SIMPLIFIED",
      "delta_u_wb": 0.05
    }
  },
  "systems": {
    "heating": {
      "generation": {
        "type": "gas_boiler",
        "efficiency_nominal": 0.85,
        "installation_year": 1995
      }
    }
  }
}
```

**Verwendung:**
- Energieausweis Bedarfsausweis
- Sanierungsfahrplan (iSFP)
- Förderantrag (BEG)

---

### LOD 300: Ausführungsplanung / Energieberatung (detailliert)

**Ziel:** DIN 18599 vollständige Berechnung, Detailplanung

**Geometrie:**
- Jedes Bauteil einzeln mit IFC GUID
- Exakte Flächen, Orientierung, Neigung
- Detaillierte Schichtaufbauten ODER Katalog-Referenzen
- Wärmebrücken detailliert

**Bauphysik:**
- U-Werte berechnet aus Schichtaufbau
- Fenster: g-Wert, Rahmenanteil, Verschattung
- Wärmebrücken: Lineare Wärmebrücken (Psi-Werte)

**Systeme:**
- Heizung: Erzeugung, Verteilung, Übergabe, Regelung
- Warmwasser: Erzeugung, Verteilung, Zirkulation
- Lüftung: Typ, Wärmerückgewinnung
- Kühlung: (wenn vorhanden)
- Beleuchtung: (Nichtwohngebäude)

**Nutzung:**
- Nutzungsprofil mit Overrides
- Betriebszeiten spezifisch
- Interne Lasten

**Beispiel:**
```json
{
  "lod": "300",
  "building": {
    "zones": [
      {
        "id": "zone_eg",
        "usage_profile_ref": "PROFILE_RES_EFH",
        "usage_conditions": {
          "theta_i_h_soll": 20,
          "operating_hours": {...}
        },
        "area": 72.5,
        "volume": 217.5
      }
    ]
  },
  "envelope": {
    "opaque_elements": {
      "walls_external": [
        {
          "id": "wall_ext_sued",
          "ifc_guid": "2Uj8Lq3Vr9QxPkXr4bN8FD",
          "construction_ref": "WALL_EXT_BRICK_WDVS_160",
          "area": 35.2,
          "orientation": 180,
          "inclination": 90,
          "adjacent_zone_id": "zone_eg"
        }
      ]
    },
    "transparent_elements": {
      "windows": [
        {
          "id": "window_sued_01",
          "ifc_guid": "3Vk9Mr4Ws0RyQlYs5cO9GE",
          "construction_ref": "WINDOW_TRIPLE_GLAZING",
          "area": 4.2,
          "orientation": 180,
          "g_value": 0.5,
          "frame_factor": 0.3,
          "shading": {...}
        }
      ]
    },
    "thermal_bridges": {
      "method": "DETAILED",
      "linear_bridges": [...]
    }
  },
  "systems": {
    "heating": {
      "generation": {
        "type": "air_water_heat_pump",
        "cop_nominal": 3.5,
        "buffer_storage": {...}
      },
      "distribution": {
        "pipe_lengths": {...},
        "insulation": {...}
      },
      "emission": {
        "type": "floor_heating",
        "control": {...}
      },
      "control": {
        "type": "weather_compensated",
        "efficiency_factor": 0.95
      }
    }
  }
}
```

**Verwendung:**
- Detaillierte Energieberatung
- Sanierungsplanung
- KfW-Effizienzhaus Nachweis
- Optimierung

---

### LOD 400: Fertigung / As-Planned

**Ziel:** Ausführungsplanung, Vergabe

**Zusätzlich zu LOD 300:**
- Produktspezifische Daten (Hersteller, Modell)
- Fertigungsdetails
- Kosten

**Beispiel:**
```json
{
  "lod": "400",
  "envelope": {
    "opaque_elements": {
      "walls_external": [
        {
          "construction_ref": "WALL_EXT_BRICK_WDVS_160",
          "product_details": {
            "insulation_manufacturer": "BASF",
            "insulation_product": "Styrodur 3035 CS",
            "thickness_actual": 0.16,
            "lambda_declared": 0.032
          }
        }
      ]
    }
  }
}
```

**Verwendung:**
- Ausschreibung
- Vergabe
- Qualitätssicherung

---

### LOD 500: As-Built / Bestand

**Ziel:** Bestandsdokumentation, Monitoring

**Zusätzlich zu LOD 400:**
- Vermessene Geometrie
- Tatsächlich verbaute Produkte
- Verbrauchsdaten
- Abweichungen von Planung

**Beispiel:**
```json
{
  "lod": "500",
  "envelope": {
    "opaque_elements": {
      "walls_external": [
        {
          "construction_ref": "WALL_EXT_BRICK_WDVS_160",
          "as_built": {
            "installation_date": "2024-08-15",
            "thickness_measured": 0.158,
            "deviations": "Dämmstärke -2mm"
          }
        }
      ]
    }
  },
  "monitoring": {
    "consumption_data": {
      "heating_kwh_a": 8500,
      "period": "2024-01-01/2024-12-31"
    }
  }
}
```

**Verwendung:**
- Bestandsdokumentation
- Monitoring
- Performance-Vergleich (Soll vs. Ist)

---

## 📋 LOD-Matrix: Required Fields

| Feld | LOD 100 | LOD 200 | LOD 300 | LOD 400 | LOD 500 |
|------|---------|---------|---------|---------|---------|
| **building.gross_floor_area** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **building.zones[].area** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **building.zones[].usage_profile_ref** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **envelope.opaque_elements** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **envelope.*.ifc_guid** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **envelope.*.construction_ref** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **envelope.*.orientation** | ❌ | Optional | ✅ | ✅ | ✅ |
| **envelope.thermal_bridges.method** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **systems.heating.generation** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **systems.heating.distribution** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **systems.heating.emission** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **product_details** | ❌ | ❌ | ❌ | ✅ | ✅ |
| **as_built** | ❌ | ❌ | ❌ | ❌ | ✅ |
| **monitoring.consumption_data** | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## ❓ OFFENE FRAGEN

1. **LOD-Stufen:**
   - Brauchen wir alle 5 LODs (100-500)?
   - Oder reichen 3 (100, 300, 500)?
   - Oder energie-spezifische LODs (LOD-E1, E2, E3)?

2. **LOD-Validierung:**
   - Soll das Schema LOD-spezifisch validieren?
   - Oder nur Hinweise geben?

3. **LOD-Übergänge:**
   - Wie wird von LOD 200 → 300 migriert?
   - Automatisch oder manuell?

4. **LOD-Mischung:**
   - Können verschiedene Bauteile unterschiedliche LODs haben?
   - Z.B. Wände LOD 300, Fenster LOD 200?

5. **LOD vs. Genauigkeit:**
   - LOD 300 mit Katalog-Referenzen = gleiche Genauigkeit wie mit Custom-Schichtaufbau?
   - Oder ist Katalog = LOD 200?

---

## 💡 EMPFEHLUNG

**Option: 3 Haupt-LODs + 2 optionale**

| LOD | Name | Verwendung | Required in Schema |
|-----|------|------------|-------------------|
| **100** | Konzept | Machbarkeitsstudie | Optional |
| **200** | Energieausweis | Bedarfsausweis, iSFP | **Empfohlen** |
| **300** | Energieberatung | DIN 18599 vollständig | **Standard** |
| **400** | Ausführung | Vergabe, QS | Optional |
| **500** | As-Built | Monitoring | Optional |

**Begründung:**
- LOD 200: Minimum für Energieausweis
- LOD 300: Standard für Energieberatung
- LOD 100, 400, 500: Spezialfälle

---

## 🚀 NÄCHSTE SCHRITTE

1. **Entscheidung:** Welche LODs brauchen wir wirklich?
2. **Schema:** LOD-spezifische required-Felder definieren
3. **Validierung:** LOD-Checker implementieren
4. **Dokumentation:** LOD-Guide schreiben
5. **Beispiele:** Pro LOD ein Demo-Projekt

---

**Status:** Brainstorming  
**Nächster Schritt:** Entscheidungen treffen
