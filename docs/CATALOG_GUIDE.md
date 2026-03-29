# Katalog-System - Verwendungsanleitung

**Version:** 2.1.0  
**Stand:** 29. März 2026  
**Projekt:** DIN 18599 IFC Sidecar

---

## 📚 Übersicht

Das Katalog-System ermöglicht die **Wiederverwendung** von standardisierten Bauteilen, Materialien und Nutzungsprofilen. Statt jedes Mal alle Parameter manuell einzugeben, können Sie auf vordefinierte Katalog-Einträge referenzieren.

### Vorteile

✅ **Konsistenz** - Gleiche Bauteile haben immer gleiche Eigenschaften  
✅ **Effizienz** - Schnellere Dateneingabe durch Referenzen  
✅ **Validierung** - Enum-basierte Nutzungsprofile (keine Tippfehler)  
✅ **Wartbarkeit** - Zentrale Pflege der Katalog-Daten  
✅ **Flexibilität** - Override-Mechanismus für Sonderfälle

---

## 🗂️ Verfügbare Kataloge

| Katalog | Datei | Einträge | Beschreibung |
|---------|-------|----------|--------------|
| **Nutzungsprofile** | `catalog/din18599_usage_profiles.json` | 45 | DIN 18599-10 Profile (Wohn + Nichtwohn) |
| **Materialien** | `catalog/materials.json` | 52 | Baustoffe mit λ, ρ, c, μ |
| **Konstruktionen** | `catalog/constructions.json` | 24 | Schichtaufbauten mit U-Werten |

---

## 1️⃣ Nutzungsprofile

### Katalog-Referenz (empfohlen)

```json
{
  "zones": [
    {
      "id": "zone_eg_wohnen",
      "name": "EG Wohnbereich",
      "usage_profile_ref": "PROFILE_RES_EFH",
      "area": 72.5,
      "volume": 217.5
    }
  ]
}
```

### Verfügbare Profile

#### Wohngebäude (2)
- `PROFILE_RES_EFH` - Einfamilienhaus
- `PROFILE_RES_MFH` - Mehrfamilienhaus

#### Nichtwohngebäude (43)
- `PROFILE_NWG_01` - Einzelbüro
- `PROFILE_NWG_02` - Gruppenbüro (2-6 Arbeitsplätze)
- `PROFILE_NWG_03` - Großraumbüro (>6 Arbeitsplätze)
- `PROFILE_NWG_04` - Besprechung, Sitzung, Seminar
- `PROFILE_NWG_05` - Schalterhalle
- `PROFILE_NWG_06` - Klassenzimmer (Schule)
- `PROFILE_NWG_07` - Hörsaal, Auditorium
- `PROFILE_NWG_08` - Kindertagesstätte
- `PROFILE_NWG_17` - Einzelhandel/Kaufhaus
- ... (siehe `catalog/din18599_usage_profiles.json` für alle)

### Custom Profile (nur wenn nicht im Katalog)

```json
{
  "zones": [
    {
      "id": "zone_labor",
      "name": "Labor Spezial",
      "usage_profile_custom": {
        "theta_i_h_soll": 22,
        "theta_i_c_soll": 24,
        "q_I": 12.0,
        "n_nutz": 0.8
      },
      "area": 45.0
    }
  ]
}
```

**Regel:** Entweder `usage_profile_ref` **ODER** `usage_profile_custom`, nicht beides!

---

## 2️⃣ Konstruktionen (Schichtaufbauten)

### Katalog-Referenz (empfohlen)

```json
{
  "elements": [
    {
      "id": "wall_ext_sued",
      "ifc_guid": "2Uj8Lq3Vr9QxPkXr4bN8FD",
      "type": "wall",
      "construction_ref": "WALL_EXT_BRICK_WDVS_160",
      "area": 35.2,
      "orientation": 180
    }
  ]
}
```

### Verfügbare Konstruktionen

#### Außenwände (7)

| ID | Beschreibung | U-Wert | Epoche |
|----|--------------|--------|--------|
| `WALL_EXT_BRICK_UNINSULATED` | Vollziegel ungedämmt | 1.4 | Vor 1978 |
| `WALL_EXT_BRICK_WDVS_100` | Ziegel + WDVS 10cm | 0.32 | 1995-2001 |
| `WALL_EXT_BRICK_WDVS_160` | Ziegel + WDVS 16cm | 0.21 | 2016-2023 |
| `WALL_EXT_BRICK_WDVS_200` | Ziegel + WDVS 20cm | 0.17 | Ab 2024 |
| `WALL_EXT_POROTON_365` | Poroton 36,5cm | 0.28 | 2009-2015 |
| `WALL_EXT_CONCRETE_UNINSULATED` | Beton ungedämmt | 2.8 | Vor 1978 |
| `WALL_EXT_WOOD_FRAME_240` | Holzrahmenbau 24cm | 0.18 | 2016-2023 |

#### Dächer (6)

| ID | Beschreibung | U-Wert | Epoche |
|----|--------------|--------|--------|
| `ROOF_PITCHED_UNINSULATED` | Steildach ungedämmt | 1.8 | Vor 1978 |
| `ROOF_PITCHED_BETWEEN_RAFTERS_160` | Zwischensparren 16cm | 0.28 | 1995-2001 |
| `ROOF_PITCHED_FULL_INSULATION_240` | Aufsparren 24cm | 0.14 | Ab 2024 |
| `ROOF_FLAT_UNINSULATED` | Flachdach ungedämmt | 1.6 | Vor 1978 |
| `ROOF_FLAT_INSULATED_200` | Flachdach 20cm | 0.17 | 2016-2023 |

#### Böden (6)

| ID | Beschreibung | U-Wert | Epoche |
|----|--------------|--------|--------|
| `FLOOR_BASEMENT_UNINSULATED` | Kellerdecke ungedämmt | 1.2 | Vor 1978 |
| `FLOOR_BASEMENT_INSULATED_100` | Kellerdecke 10cm | 0.32 | 2009-2015 |
| `FLOOR_GROUND_SLAB_UNINSULATED` | Bodenplatte ungedämmt | 1.5 | Vor 1978 |
| `FLOOR_GROUND_SLAB_PERIMETER_120` | Bodenplatte Perimeter 12cm | 0.28 | 2016-2023 |
| `FLOOR_TOP_UNINSULATED` | Oberste Geschossdecke ungedämmt | 1.4 | Vor 1978 |
| `FLOOR_TOP_INSULATED_200` | Oberste Geschossdecke 20cm | 0.18 | 2016-2023 |

#### Fenster (3)

| ID | Beschreibung | U-Wert | g-Wert |
|----|--------------|--------|--------|
| `WINDOW_SINGLE_GLAZING` | Einfachverglasung | 5.8 | 0.85 |
| `WINDOW_DOUBLE_GLAZING` | Zweifachverglasung | 2.8 | 0.75 |
| `WINDOW_TRIPLE_GLAZING` | Dreifachverglasung | 0.7 | 0.5 |

### Custom Konstruktion (nur wenn nicht im Katalog)

```json
{
  "elements": [
    {
      "id": "wall_special",
      "ifc_guid": "3Vk9Mr4Ws0RyQlYs5cO9GE",
      "type": "wall",
      "construction_custom": {
        "u_value": 0.15,
        "layers": [
          {"material_ref": "MAT_LIME_CEMENT_PLASTER", "thickness": 0.005},
          {"material_ref": "MAT_EPS_032", "thickness": 0.22},
          {"material_ref": "MAT_BRICK_PERFORATED", "thickness": 0.24},
          {"material_ref": "MAT_GYPSUM_PLASTER", "thickness": 0.015}
        ]
      },
      "area": 28.5
    }
  ]
}
```

---

## 3️⃣ Materialien

### Katalog-Referenz in Custom Konstruktionen

```json
{
  "construction_custom": {
    "layers": [
      {"material_ref": "MAT_EPS_032", "thickness": 0.16},
      {"material_ref": "MAT_BRICK_PERFORATED", "thickness": 0.24}
    ]
  }
}
```

### Verfügbare Materialien (Auswahl)

#### Dämmstoffe

| ID | Name | λ [W/(mK)] | WLG |
|----|------|------------|-----|
| `MAT_EPS_032` | EPS 032 | 0.032 | 032 |
| `MAT_EPS_035` | EPS 035 | 0.035 | 035 |
| `MAT_XPS_035` | XPS 035 | 0.035 | 035 |
| `MAT_MINERAL_WOOL_032` | Mineralwolle 032 | 0.032 | 032 |
| `MAT_MINERAL_WOOL_035` | Mineralwolle 035 | 0.035 | 035 |
| `MAT_PUR_024` | PUR/PIR 024 | 0.024 | 024 |
| `MAT_WOOD_FIBER_040` | Holzfaser 040 | 0.040 | 040 |
| `MAT_CELLULOSE_040` | Zellulose 040 | 0.040 | 040 |

#### Mauerwerk

| ID | Name | λ [W/(mK)] |
|----|------|------------|
| `MAT_BRICK_SOLID` | Vollziegel | 0.8 |
| `MAT_BRICK_PERFORATED` | Hochlochziegel | 0.45 |
| `MAT_BRICK_POROUS` | Poroton | 0.12 |
| `MAT_AAC_500` | Porenbeton 500 | 0.14 |
| `MAT_CALCIUM_SILICATE` | Kalksandstein | 0.99 |

Siehe `catalog/materials.json` für alle 52 Materialien.

---

## 🔄 Override-Mechanismus

Sie können Katalog-Werte überschreiben, wenn ein Bauteil vom Standard abweicht:

```json
{
  "elements": [
    {
      "id": "wall_ext_nord",
      "ifc_guid": "3Vk9Mr4Ws0RyQlYs5cO9GE",
      "type": "wall",
      "construction_ref": "WALL_EXT_BRICK_WDVS_160",
      "overrides": {
        "u_value": 0.19,
        "note": "U-Wert angepasst wegen Wärmebrücken"
      },
      "area": 28.5
    }
  ]
}
```

**Priorität:** `overrides` > `catalog` > `defaults`

---

## 📊 Varianten-Management mit Katalog

Sanierungsszenarien werden durch **Delta-Modell** abgebildet:

```json
{
  "scenarios": [
    {
      "id": "scenario_sanierung",
      "name": "Sanierung WDVS + Fenster",
      "delta": {
        "elements": [
          {
            "id": "wall_ext_sued",
            "construction_ref": "WALL_EXT_BRICK_WDVS_160"
          },
          {
            "id": "window_sued_01",
            "construction_ref": "WINDOW_TRIPLE_GLAZING"
          }
        ]
      }
    }
  ]
}
```

**Merge-Regel:** `base` + `delta` = `scenario`

---

## ✅ Best Practices

### 1. Katalog bevorzugen
✅ **Gut:** `"construction_ref": "WALL_EXT_BRICK_WDVS_160"`  
❌ **Schlecht:** Manuell alle Schichten definieren

### 2. Custom nur wenn nötig
Nutzen Sie Custom-Definitionen nur, wenn:
- Das Bauteil nicht im Katalog existiert
- Spezielle Anforderungen vorliegen
- Override nicht ausreicht

### 3. Konsistente Referenzen
Gleiche Bauteile sollten gleiche Katalog-Referenzen nutzen:

```json
// ✅ Gut - konsistent
{"id": "wall_ext_sued", "construction_ref": "WALL_EXT_BRICK_WDVS_160"},
{"id": "wall_ext_nord", "construction_ref": "WALL_EXT_BRICK_WDVS_160"}

// ❌ Schlecht - inkonsistent
{"id": "wall_ext_sued", "construction_ref": "WALL_EXT_BRICK_WDVS_160"},
{"id": "wall_ext_nord", "construction_custom": {...}}
```

### 4. Dokumentation
Nutzen Sie `note` oder `description` für Abweichungen:

```json
{
  "construction_ref": "WALL_EXT_BRICK_WDVS_160",
  "overrides": {
    "u_value": 0.19
  },
  "note": "U-Wert angepasst wegen Wärmebrücken an Fensteranschlüssen"
}
```

---

## 🔧 Katalog erweitern

Sie können eigene Katalog-Einträge hinzufügen:

### 1. Material hinzufügen

```json
{
  "materials": [
    {
      "id": "MAT_CUSTOM_INSULATION",
      "name_de": "Spezial-Dämmung",
      "category": "insulation",
      "lambda": 0.025,
      "rho": 25,
      "c": 1400,
      "mu": 30,
      "wlg": "025"
    }
  ]
}
```

### 2. Konstruktion hinzufügen

```json
{
  "constructions": [
    {
      "id": "WALL_CUSTOM_PASSIVE_HOUSE",
      "name_de": "Passivhaus-Wand 40cm",
      "category": "wall_external",
      "u_value_calculated": 0.10,
      "layers": [
        {"material_ref": "MAT_LIME_CEMENT_PLASTER", "thickness": 0.005},
        {"material_ref": "MAT_EPS_032", "thickness": 0.30},
        {"material_ref": "MAT_BRICK_PERFORATED", "thickness": 0.24},
        {"material_ref": "MAT_GYPSUM_PLASTER", "thickness": 0.015}
      ]
    }
  ]
}
```

---

## 📖 Beispiel-Projekt

Siehe `examples/demo-einfamilienhaus-katalog.din18599.json` für ein vollständiges Beispiel mit:

- ✅ Nutzungsprofil-Referenzen (`PROFILE_RES_EFH`)
- ✅ Konstruktions-Referenzen (Wände, Dach, Boden, Fenster)
- ✅ 2 Sanierungsszenarien mit Delta-Modell
- ✅ Energiebilanzen (Bestand vs. Sanierung)

---

## 🚀 Migration v2.0 → v2.1

### Breaking Changes

| Feld | v2.0 | v2.1 | Migration |
|------|------|------|-----------|
| `usage_profile` | `"17"` (String) | `"PROFILE_NWG_17"` (Enum) | Mapping-Tabelle |
| `elements[].ifc_guid` | Optional | **Required** | GUID hinzufügen |

### Migration-Script

```bash
# Automatische Migration (geplant)
node scripts/migrate-v2.0-to-v2.1.js input.json output.json
```

---

## 📚 Weitere Ressourcen

- **Schema:** `schema/v2.1-catalog-extensions.json`
- **Nutzungsprofile:** `catalog/din18599_usage_profiles.json`
- **Materialien:** `catalog/materials.json`
- **Konstruktionen:** `catalog/constructions.json`
- **Demo:** `examples/demo-einfamilienhaus-katalog.din18599.json`

---

**Letzte Aktualisierung:** 29. März 2026  
**Version:** 2.1.0  
**Feedback:** GitHub Issues oder opensource@dwe-beratung.de
