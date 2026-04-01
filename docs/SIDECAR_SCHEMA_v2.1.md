# Sidecar JSON Schema v2.1

**Version:** 2.1.0  
**Datum:** 1. April 2026  
**Änderung:** Katalog-Referenzen optional + vollständige Layer-Auflösung

---

## 🎯 KERNPRINZIP

**Daten vollständig aufgelöst + optionale Katalog-Referenz**

```json
{
  "layer_structures": [
    {
      "id": "LS-001",
      "name": "Außenwand WDVS 16cm",
      "layers": [
        // ← Vollständig aufgelöst (IMMER vorhanden)
        {"position": 1, "material_name": "Putz", "thickness": 0.005, "lambda": 0.87},
        {"position": 2, "material_name": "EPS 032", "thickness": 0.16, "lambda": 0.032},
        {"position": 3, "material_name": "Ziegel", "thickness": 0.24, "lambda": 0.45}
      ],
      "u_value_calculated": 0.21,
      "source": "catalog_template",
      "catalog_ref": "WALL_EXT_BRICK_WDVS_160"  // ← Optional: Referenz zum Katalog
    }
  ]
}
```

**Vorteile:**
- ✅ Daten sind **vollständig** (funktioniert ohne Katalog)
- ✅ Katalog-Referenz ist **optional** (für Transparenz/Tracking)
- ✅ User kann sehen: "Das kam aus dem Katalog"
- ✅ Aber: Daten sind **nicht abhängig** vom Katalog

---

## 📊 VOLLSTÄNDIGES SCHEMA

```json
{
  "schema_info": {
    "url": "https://din18599-ifc.de/schema/v2.1",
    "version": "2.1.0"
  },
  "meta": {
    "project_id": "PRJ-2026-04-01-123456",
    "project_name": "Musterprojekt",
    "ifc_file_ref": "building.ifc",
    "ifc_guid_building": "2O2Fr$t4X7Zf8NOew3FNr2",
    "lod": "300",
    "software_name": "DIN18599-IFC Converter",
    "software_version": "2.1.0",
    "calculation_date": "2026-04-01T12:00:00Z",
    "norm_version": "DIN V 18599:2018-09"
  },
  "input": {
    "climate_location": {
      "postcode": "10115",
      "city": "Berlin",
      "try_region_code": 4
    },
    
    "materials": [
      {
        "id": "MAT-001",
        "name": "EPS 032 Dämmung",
        "lambda": 0.032,
        "density": 15.0,
        "specific_heat": 1500,
        "mu": 50,
        "source": "ifc_material",
        "ifc_material_guid": "3kF8s$t4X7Zf8NOew3FNr2",
        "catalog_ref": null  // ← Optional: Referenz zu catalog/materials.json
      },
      {
        "id": "MAT-002",
        "name": "Hochlochziegel",
        "lambda": 0.45,
        "density": 800.0,
        "specific_heat": 1000,
        "mu": 10,
        "source": "catalog",
        "ifc_material_guid": null,
        "catalog_ref": "MAT_BRICK_PERFORATED"  // ← Aus Katalog
      }
    ],
    
    "layer_structures": [
      {
        "id": "LS-001",
        "name": "Außenwand WDVS 16cm (KfW 55)",
        "type": "WALL",
        "layers": [
          {
            "position": 1,
            "material_name": "Kalkzementputz",
            "thickness": 0.005,
            "lambda": 0.87,
            "density": 1800,
            "specific_heat": 1000,
            "mu": 35,
            "material_ref": "MAT-003",
            "function": "exterior_finish"
          },
          {
            "position": 2,
            "material_name": "EPS 032 Dämmung",
            "thickness": 0.16,
            "lambda": 0.032,
            "density": 15,
            "specific_heat": 1500,
            "mu": 50,
            "material_ref": "MAT-001",
            "function": "insulation"
          },
          {
            "position": 3,
            "material_name": "Hochlochziegel",
            "thickness": 0.24,
            "lambda": 0.45,
            "density": 800,
            "specific_heat": 1000,
            "mu": 10,
            "material_ref": "MAT-002",
            "function": "structure"
          },
          {
            "position": 4,
            "material_name": "Gipsputz",
            "thickness": 0.015,
            "lambda": 0.35,
            "density": 1200,
            "specific_heat": 1000,
            "mu": 10,
            "material_ref": "MAT-004",
            "function": "interior_finish"
          }
        ],
        "total_thickness": 0.42,
        "u_value_calculated": 0.21,
        "source": "catalog_template",
        "ifc_material_layer_set_guid": null,
        "catalog_ref": "WALL_EXT_BRICK_WDVS_160",  // ← Optional: Aus Katalog
        "metadata": {
          "created_at": "2026-04-01T12:00:00Z",
          "modified_at": "2026-04-01T14:30:00Z",
          "created_by": "user@example.com",
          "is_modified": false  // true wenn User Katalog-Template angepasst hat
        }
      },
      {
        "id": "LS-002",
        "name": "Außenwand Bestand ungedämmt",
        "type": "WALL",
        "layers": [
          {
            "position": 1,
            "material_name": "Vollziegel",
            "thickness": 0.365,
            "lambda": 0.8,
            "density": 1800,
            "material_ref": "MAT-005",
            "function": "structure"
          }
        ],
        "total_thickness": 0.365,
        "u_value_calculated": 1.4,
        "source": "ifc_material_layer_set",
        "ifc_material_layer_set_guid": "5mH9t$t4X7Zf8NOew3FNr2",
        "catalog_ref": null  // ← Kein Katalog (aus IFC)
      }
    ],
    
    "elements": [
      {
        "ifc_guid": "2O2Fr$t4X7Zf8NOew3FNr2",
        "position_number": "001",
        "layer_structure_ref": "LS-001",
        "boundary_condition": "EXTERIOR",
        "u_value_undisturbed": 0.21,
        "thermal_bridge_delta_u": 0.02,
        "thermal_bridge_type": "SIMPLIFIED",
        "orientation": 180,
        "inclination": 90,
        "solar_absorption": 0.5
      }
    ],
    
    "zones": [
      {
        "id": "ZONE-001",
        "name": "Erdgeschoss",
        "usage_profile": "17",
        "usage_profile_name": "Wohnen",
        "area_an": 80.5,
        "volume_v": 200.0,
        "height_h": 2.5,
        "air_change_n50": 0.6,
        "design_temp_heating": 20,
        "design_temp_cooling": 26,
        "lighting_control": "MANUAL",
        "ifc_space_guids": ["4nJ0u$t4X7Zf8NOew3FNr2"]
      }
    ]
  }
}
```

---

## 🔄 DATENQUELLEN & catalog_ref

### 1. **Aus IFC extrahiert**
```json
{
  "source": "ifc_material_layer_set",
  "ifc_material_layer_set_guid": "...",
  "catalog_ref": null  // ← Kein Katalog
}
```

### 2. **Aus EVEBI extrahiert**
```json
{
  "source": "evebi_construction",
  "ifc_material_layer_set_guid": null,
  "catalog_ref": null  // ← Kein Katalog
}
```

### 3. **Aus Katalog gewählt (unverändert)**
```json
{
  "source": "catalog_template",
  "catalog_ref": "WALL_EXT_BRICK_WDVS_160",  // ← Referenz
  "metadata": {
    "is_modified": false  // ← Nicht angepasst
  }
}
```

### 4. **Aus Katalog gewählt + angepasst**
```json
{
  "source": "catalog_template_modified",
  "catalog_ref": "WALL_EXT_BRICK_WDVS_160",  // ← Original-Referenz
  "metadata": {
    "is_modified": true,  // ← User hat angepasst
    "original_u_value": 0.21,  // ← Original aus Katalog
    "modified_fields": ["layers[1].thickness"]  // ← Was geändert wurde
  }
}
```

### 5. **Manuell erstellt**
```json
{
  "source": "manual",
  "catalog_ref": null  // ← Kein Katalog
}
```

---

## 💡 USE CASES

### **UC1: IFC-Import**
```
1. IFC-Parser extrahiert Material-Layers
2. Layers vollständig im JSON
3. source: "ifc_material_layer_set"
4. catalog_ref: null
```

### **UC2: Katalog-Template nutzen**
```
1. User wählt "Außenwand WDVS 16cm" aus Katalog
2. System kopiert Layers ins JSON
3. source: "catalog_template"
4. catalog_ref: "WALL_EXT_BRICK_WDVS_160"
5. is_modified: false
```

### **UC3: Katalog-Template anpassen**
```
1. User wählt "Außenwand WDVS 16cm" aus Katalog
2. User ändert Dämmdicke: 16cm → 18cm
3. Layers im JSON aktualisiert
4. source: "catalog_template_modified"
5. catalog_ref: "WALL_EXT_BRICK_WDVS_160" (Original)
6. is_modified: true
7. modified_fields: ["layers[1].thickness"]
```

### **UC4: Katalog-Update**
```
Wenn Katalog aktualisiert wird:
- Elemente mit catalog_ref + is_modified=false → können aktualisiert werden
- Elemente mit catalog_ref + is_modified=true → NICHT aktualisieren (User-Änderungen)
- Elemente ohne catalog_ref → ignorieren
```

---

## 🎯 VORTEILE

| Aspekt | Vorteil |
|--------|---------|
| **Vollständigkeit** | Daten funktionieren ohne Katalog ✅ |
| **Transparenz** | User sieht Herkunft (IFC/EVEBI/Katalog) ✅ |
| **Tracking** | Änderungen nachvollziehbar ✅ |
| **Updates** | Katalog-Updates möglich (wenn nicht modified) ✅ |
| **Flexibilität** | User kann Templates anpassen ✅ |

---

## 📝 BEISPIEL: Vollständiger Workflow

```json
// 1. User importiert IFC
{
  "id": "LS-001",
  "name": "Außenwand aus IFC",
  "layers": [...],  // Vollständig
  "source": "ifc_material_layer_set",
  "catalog_ref": null
}

// 2. User wählt Katalog-Template
{
  "id": "LS-002",
  "name": "Außenwand WDVS 16cm",
  "layers": [...],  // Vollständig (aus Katalog kopiert)
  "source": "catalog_template",
  "catalog_ref": "WALL_EXT_BRICK_WDVS_160",
  "metadata": {"is_modified": false}
}

// 3. User passt Template an
{
  "id": "LS-002",
  "name": "Außenwand WDVS 18cm (angepasst)",
  "layers": [
    {...},
    {"thickness": 0.18, ...},  // ← Geändert von 0.16
    {...}
  ],
  "source": "catalog_template_modified",
  "catalog_ref": "WALL_EXT_BRICK_WDVS_160",  // Original
  "metadata": {
    "is_modified": true,
    "modified_fields": ["layers[1].thickness", "name"]
  }
}
```

---

## 🚀 IMPLEMENTIERUNG

Siehe:
- `api/parsers/ifc_material_extractor.py` (Layer-Extraktion)
- `api/generators/sidecar_generator.py` (Sidecar-Generierung)
- `catalog/constructions.json` (Katalog-Daten)
