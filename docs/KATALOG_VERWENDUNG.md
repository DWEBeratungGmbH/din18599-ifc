# Katalog-Verwendung

**Version:** 2.0  
**Stand:** März 2026

---

## 1. Überblick

**Kataloge** sind vordefinierte Sammlungen von Bauteilen, Materialien oder Systemen mit typischen Kennwerten. Sie ermöglichen:

- ✅ **Schnelle Dateneingabe** (Baujahr → U-Wert)
- ✅ **Konsistente Werte** (offizielle Quellen)
- ✅ **Rechtssicherheit** (BEG-konforme Defaults)
- ✅ **Vergleichbarkeit** (standardisierte Annahmen)

---

## 2. Bundesanzeiger-Katalog (de-bmwi2020-bauteile-v1.0)

### Quelle

**Bundesanzeiger AT 04.12.2020 B1**  
Bekanntmachung der Regeln für Energieverbrauchskennwerte und der Vergleichswerte im Nichtwohngebäudebestand

- **PDF:** https://bundesanzeiger.de/pub/publication/qzQUGd8A3unSCCbVMcf/content/qzQUGd8A3unSCCbVMcf/BAnz%20AT%2004.12.2020%20B1.pdf
- **Katalog:** `catalogs/constructions/de-bmwi2020-bauteile-v1.0.json`
- **Umfang:** 97 U-Wert-Referenzen
- **Status:** Offiziell, BEG-konform

### Struktur

```json
{
  "$schema": "https://din18599-ifc.de/schema/catalog/v1",
  "catalog_info": {
    "id": "DE_BMWI2020_BAUTEILE",
    "version": "1.0.0",
    "name": "Bundesanzeiger 2020 - Bauteile nach Baujahr",
    "source": "Bundesanzeiger AT 04.12.2020 B1",
    "valid_from": "2020-12-04"
  },
  "age_classes": [
    {
      "id": "BIS_1918",
      "name": "bis 1918",
      "year_from": 0,
      "year_to": 1918
    },
    ...
  ],
  "constructions": {
    "opaque": [...],
    "transparent": [...]
  }
}
```

### Baualtersklassen

| ID | Bezeichnung | Zeitraum |
|----|-------------|----------|
| `BIS_1918` | bis 1918 | 0-1918 |
| `1919_1948` | 1919-1948 | 1919-1948 |
| `1949_1957` | 1949-1957 | 1949-1957 |
| `1958_1968` | 1958-1968 | 1958-1968 |
| `1969_1978` | 1969-1978 | 1969-1978 |
| `1979_1983` | 1979-1983 | 1979-1983 |
| `1984_1994` | 1984-1994 | 1984-1994 |
| `1995_2001` | 1995-2001 | 1995-2001 |
| `2002_2009` | 2002-2009 | 2002-2009 |
| `AB_2010` | ab 2010 | 2010-9999 |

### Opake Bauteile

**Beispiel: Außenwand**

```json
{
  "id": "AW_VOLLZIEGEL_20_30_BMWI",
  "name": "Außenwand Vollziegel 20-30cm",
  "type": "WALL",
  "age_class": "1919_1948",
  "u_value": 1.8,
  "description": "Vollziegelmauerwerk 20-30cm, ungedämmt"
}
```

**Verfügbare Typen:**
- Außenwände (AW): Vollziegel, Hochlochziegel, Kalksandstein, Beton, etc.
- Dächer (DA): Massiv, Holz, Flachdach
- Kellerdecken (KD): Stahlbeton, Holzbalken
- Bodenplatten (BP): Stahlbeton

### Transparente Bauteile

**Beispiel: Fenster**

```json
{
  "id": "FENSTER_EINFACH_BMWI",
  "name": "Einfachverglasung",
  "type": "WINDOW",
  "age_class": "BIS_1918",
  "u_value_glass": 5.8,
  "u_value_frame": 3.5,
  "g_value": 0.85
}
```

---

## 3. Katalog-Verwendung im Sidecar

### Variante A: Katalog-Referenz (LOD 100-200)

```json
{
  "meta": {
    "catalog_references": ["DE_BMWI2020_BAUTEILE v1.0.0"]
  },
  "input": {
    "elements": [
      {
        "ifc_guid": "1Ab2Cd3Ef4Gh5Ij6Kl7Mn8",
        "boundary_condition": "EXTERIOR",
        "construction_catalog_ref": "AW_VOLLZIEGEL_20_30_BMWI",
        "u_value_undisturbed": 1.8
      }
    ]
  }
}
```

**Bedeutung:**
- `catalog_references`: Liste der verwendeten Kataloge
- `construction_catalog_ref`: Referenz auf Katalog-Eintrag
- `u_value_undisturbed`: Wird aus Katalog übernommen (kann überschrieben werden)

### Variante B: Eigene Schichtaufbauten (LOD 300-400)

```json
{
  "input": {
    "materials": [
      {
        "id": "MAT-BRICK",
        "name": "Vollziegel",
        "type": "STANDARD",
        "lambda": 0.81
      }
    ],
    "layer_structures": [
      {
        "id": "LS-AW-BESTAND",
        "name": "Außenwand Bestand",
        "type": "WALL",
        "layers": [
          {"position": 1, "material_id": "MAT-BRICK", "thickness_mm": 250}
        ],
        "calculated_values": {
          "u_value_w_m2k": 1.8
        }
      }
    ],
    "elements": [
      {
        "ifc_guid": "1Ab2Cd3Ef4Gh5Ij6Kl7Mn8",
        "layer_structure_ref": "LS-AW-BESTAND",
        "u_value_undisturbed": 1.8
      }
    ]
  }
}
```

---

## 4. Katalog-Auswahl nach Baujahr

### Automatisches Mapping

```python
def get_catalog_entry(building_year, construction_type):
    """
    Ermittelt Katalog-Eintrag basierend auf Baujahr
    """
    age_class = get_age_class(building_year)
    catalog_id = f"{construction_type}_{age_class}_BMWI"
    return catalog.get(catalog_id)

# Beispiel
building_year = 1975
construction_type = "AW_VOLLZIEGEL_20_30"
entry = get_catalog_entry(1975, "AW_VOLLZIEGEL_20_30")
# → AW_VOLLZIEGEL_20_30_1969_1978_BMWI (U=1.4 W/m²K)
```

### Mapping-Tabelle

| Baujahr | Baualtersklasse | Außenwand Vollziegel | U-Wert |
|---------|-----------------|----------------------|--------|
| 1900 | BIS_1918 | AW_VOLLZIEGEL_20_30_BIS_1918_BMWI | 2.0 |
| 1930 | 1919_1948 | AW_VOLLZIEGEL_20_30_1919_1948_BMWI | 1.8 |
| 1960 | 1958_1968 | AW_VOLLZIEGEL_20_30_1958_1968_BMWI | 1.4 |
| 1975 | 1969_1978 | AW_VOLLZIEGEL_20_30_1969_1978_BMWI | 1.4 |
| 2000 | 1995_2001 | AW_VOLLZIEGEL_20_30_1995_2001_BMWI | 0.5 |
| 2015 | AB_2010 | AW_VOLLZIEGEL_20_30_AB_2010_BMWI | 0.24 |

---

## 5. Custom Catalogs

### Eigene Kataloge erstellen

```json
{
  "$schema": "https://din18599-ifc.de/schema/catalog/v1",
  "catalog_info": {
    "id": "CUSTOM_MATERIALS_2026",
    "version": "1.0.0",
    "name": "Firmen-Katalog Materialien",
    "source": "Interne Datenbank",
    "valid_from": "2026-01-01"
  },
  "materials": [
    {
      "id": "MAT-CUSTOM-001",
      "name": "Hochleistungsdämmung XYZ",
      "type": "STANDARD",
      "lambda": 0.018,
      "density": 35,
      "manufacturer": "Firma XYZ",
      "product_code": "XYZ-HLD-180"
    }
  ]
}
```

### Katalog-Speicherorte

```
catalogs/
├── constructions/
│   ├── de-bmwi2020-bauteile-v1.0.json       # Bundesanzeiger
│   └── custom-constructions-v1.0.json       # Eigene Bauteile
├── materials/
│   ├── oekobaudat-2023-v1.0.json           # Ökobaudat
│   └── custom-materials-v1.0.json          # Eigene Materialien
└── systems/
    └── custom-systems-v1.0.json            # Eigene Systeme
```

---

## 6. Katalog-Versionierung

### Versionsschema

```
{catalog_id}-v{major}.{minor}.{patch}.json
```

**Beispiel:**
- `de-bmwi2020-bauteile-v1.0.0.json` (Initial Release)
- `de-bmwi2020-bauteile-v1.1.0.json` (Neue Einträge)
- `de-bmwi2020-bauteile-v2.0.0.json` (Breaking Changes)

### Kompatibilität

- **Major:** Breaking Changes (IDs geändert, Struktur geändert)
- **Minor:** Neue Einträge (abwärtskompatibel)
- **Patch:** Bugfixes (U-Wert korrigiert)

### Katalog-Referenz im Sidecar

```json
{
  "meta": {
    "catalog_references": [
      "DE_BMWI2020_BAUTEILE v1.0.0",
      "CUSTOM_MATERIALS_2026 v1.2.0"
    ]
  }
}
```

---

## 7. Katalog-Validierung

### Pflichtfelder

```json
{
  "catalog_info": {
    "id": "REQUIRED",
    "version": "REQUIRED (semver)",
    "name": "REQUIRED",
    "source": "REQUIRED",
    "valid_from": "REQUIRED (ISO 8601)"
  }
}
```

### Validierungs-Regeln

- ✅ `id` muss eindeutig sein
- ✅ `version` muss Semantic Versioning folgen
- ✅ Alle Einträge müssen `id`, `name`, `type` haben
- ✅ U-Werte müssen > 0 sein
- ✅ λ-Werte müssen > 0 sein

---

## 8. Best Practices

### Katalog-Auswahl

**LOD 100-200:**
- ✅ Nutze Bundesanzeiger-Katalog
- ✅ Wähle Baualtersklasse nach Baujahr
- ✅ Nutze `construction_catalog_ref`

**LOD 300-400:**
- ✅ Erstelle eigene Schichtaufbauten
- ✅ Nutze Produktdatenblätter
- ✅ Katalog nur als Fallback

### Katalog-Pflege

- 📅 **Jährlich aktualisieren** (neue Normen, neue Produkte)
- 📝 **Dokumentieren** (Quelle, Datum, Annahmen)
- 🔍 **Validieren** (Plausibilitätschecks)
- 🔄 **Versionieren** (Semantic Versioning)

### Katalog-Sharing

- 🌐 **Open Source** (GitHub, GitLab)
- 📦 **Paketmanager** (npm, PyPI)
- 🔗 **URL-Referenzen** (https://catalogs.din18599-ifc.de/...)

---

## 9. Katalog-API (Future)

### REST-Endpunkte

```
GET /catalogs                           # Liste aller Kataloge
GET /catalogs/{id}                      # Katalog-Details
GET /catalogs/{id}/entries              # Alle Einträge
GET /catalogs/{id}/entries/{entry_id}   # Einzelner Eintrag
GET /catalogs/search?q=vollziegel       # Suche
```

### Beispiel-Request

```bash
curl https://api.din18599-ifc.de/catalogs/DE_BMWI2020_BAUTEILE/entries/AW_VOLLZIEGEL_20_30_1969_1978_BMWI
```

**Response:**
```json
{
  "id": "AW_VOLLZIEGEL_20_30_1969_1978_BMWI",
  "name": "Außenwand Vollziegel 20-30cm",
  "type": "WALL",
  "age_class": "1969_1978",
  "u_value": 1.4,
  "description": "Vollziegelmauerwerk 20-30cm, ungedämmt"
}
```

---

## 10. Beispiele

### Beispiel 1: LOD 100 mit Bundesanzeiger

```json
{
  "meta": {
    "lod": "100",
    "catalog_references": ["DE_BMWI2020_BAUTEILE v1.0.0"]
  },
  "input": {
    "elements": [
      {
        "ifc_guid": "1Ab2Cd3Ef4Gh5Ij6Kl7Mn8",
        "construction_catalog_ref": "AW_VOLLZIEGEL_20_30_1969_1978_BMWI",
        "u_value_undisturbed": 1.4
      }
    ]
  }
}
```

### Beispiel 2: LOD 300 mit Custom Catalog

```json
{
  "meta": {
    "lod": "300",
    "catalog_references": ["CUSTOM_MATERIALS_2026 v1.0.0"]
  },
  "input": {
    "materials": [
      {
        "id": "MAT-CUSTOM-001",
        "name": "Hochleistungsdämmung XYZ",
        "type": "STANDARD",
        "lambda": 0.018
      }
    ],
    "layer_structures": [
      {
        "id": "LS-AW-SANIERT",
        "layers": [
          {"position": 1, "material_id": "MAT-CUSTOM-001", "thickness_mm": 200}
        ]
      }
    ]
  }
}
```

---

**Status:** ✅ Katalog-System ist vollständig definiert und implementiert.
