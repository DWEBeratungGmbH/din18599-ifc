# IFC vs. EVEBI Gap-Analyse

**Datum:** 1. April 2026  
**Ziel:** Identifiziere, was EVEBI besser macht und wie wir unser Datenmodell verbessern können

---

## 🎯 KERNFRAGE

**Warum funktioniert EVEBI perfekt in Energieberaterprogrammen?**

### Antwort: EVEBI ist **energieberater-zentrisch**, IFC ist **geometrie-zentrisch**

| Aspekt | IFC (Geometrie) | EVEBI (Energie) | Unser Sidecar |
|--------|-----------------|-----------------|---------------|
| **Primärer Fokus** | 3D-Geometrie, BIM | Energieberechnung | Energie (DIN 18599) |
| **Bauteil-ID** | GUID (geometrisch) | PosNo + Name | GUID (von IFC) |
| **Konstruktionen** | Material-Layers | U-Wert direkt | Beides |
| **Zonen** | IfcSpace (geometrisch) | Nutzungsprofil + Fläche | Beides |
| **Anlagentechnik** | IfcDistributionElement | Detailliert (Typ, Baujahr, COP) | Detailliert |

---

## 🔍 WAS MACHT EVEBI BESSER?

### 1. **Bauteil-Identifikation: PosNo**

**EVEBI:**
```xml
<tflListe>
  <item GUID="{...}" PosNo="001">
    <name>Außenwand Nord</name>
    <flaeche man="45.5">45.5</flaeche>
  </item>
</tflListe>
```

**IFC:**
```
IfcWall
  GlobalId: "2O2Fr$t4X7Zf8NOew3FNr2"
  Name: "Außenwand Nord"
  Tag: "001"  ← Oft leer oder inkonsistent!
```

**Problem:** IFC hat `Tag`, aber:
- Nicht standardisiert
- Oft leer
- Keine Konvention für Format

**Lösung für unser Modell:**
```json
{
  "elements": [
    {
      "ifc_guid": "2O2Fr$t4X7Zf8NOew3FNr2",
      "position_number": "001",  // ← NEU: Explizites Feld
      "name": "Außenwand Nord",
      "source": "ifc_tag"  // oder "ifc_name" oder "manual"
    }
  ]
}
```

---

### 2. **Konstruktions-Referenzierung**

**EVEBI:**
```xml
<tflListe>
  <item GUID="{...}">
    <konstruktion GUID="{7456141-...}"/>  ← Direkte Referenz
  </item>
</tflListe>

<konstruktionenListe>
  <item GUID="{7456141-...}">
    <name>WDVS Außenwand</name>
    <uWert man="0.2">0.2</uWert>
  </item>
</konstruktionenListe>
```

**IFC:**
```
IfcWall
  → IfcRelAssociatesMaterial
    → IfcMaterialLayerSetUsage
      → IfcMaterialLayerSet
        → IfcMaterialLayer[]  ← Komplex!
```

**Problem:** IFC-Material-Struktur ist:
- Sehr komplex (5 Ebenen)
- Nicht immer vollständig
- Schwer zu parsen

**Lösung für unser Modell:**
```json
{
  "elements": [
    {
      "ifc_guid": "...",
      "construction": {
        "id": "CONSTR-001",
        "name": "WDVS Außenwand",
        "u_value": 0.2,
        "source": "ifc_material_layers",  // oder "manual" oder "catalog"
        "ifc_material_set_guid": "..."  // Optional: Rückverfolgbarkeit
      }
    }
  ]
}
```

---

### 3. **Zonen-Nutzungsprofile**

**EVEBI:**
```xml
<geschosseListe>
  <item GUID="{...}">
    <name>Erdgeschoss</name>
    <nutzung>17</nutzung>  ← DIN 18599 Nutzungsprofil direkt!
    <flaeche>80.5</flaeche>
    <volumen>200.0</volumen>
  </item>
</geschosseListe>
```

**IFC:**
```
IfcSpace
  Name: "Erdgeschoss"
  LongName: "Wohnraum"
  ObjectType: ???  ← Kein Standard für Nutzungsprofile
```

**Problem:** IFC hat keine Standard-Nutzungsprofile für DIN 18599

**Lösung für unser Modell:**
```json
{
  "zones": [
    {
      "id": "ZONE-001",
      "name": "Erdgeschoss",
      "usage_profile": "17",  // DIN 18599 Code
      "usage_profile_name": "Wohnen",  // ← NEU: Lesbar
      "usage_profile_source": "ifc_object_type",  // oder "manual" oder "ai_detected"
      "ifc_space_guids": ["..."]
    }
  ]
}
```

---

### 4. **Orientierung & Neigung (Geometrie)**

**EVEBI:**
```xml
<tflListe>
  <item>
    <orientierung>180</orientierung>  ← Azimut (0-360°)
    <neigung>90</neigung>             ← Neigung (0-90°)
  </item>
</tflListe>
```

**IFC:**
```
IfcWall
  → Geometry (IfcProductDefinitionShape)
    → IfcShapeRepresentation
      → IfcExtrudedAreaSolid
        → Position (Matrix 4x4)  ← Muss berechnet werden!
```

**Problem:** IFC speichert Geometrie als 3D-Mesh, nicht als Orientierung

**Lösung für unser Modell:**
```json
{
  "elements": [
    {
      "ifc_guid": "...",
      "geometry": {
        "orientation": 180,  // Azimut (berechnet aus IFC)
        "inclination": 90,   // Neigung (berechnet aus IFC)
        "area": 45.5,        // Fläche (berechnet aus IFC)
        "calculation_method": "ifc_normal_vector"  // ← NEU: Transparenz
      }
    }
  ]
}
```

---

### 5. **Anlagentechnik-Metadaten**

**EVEBI:**
```xml
<hzErzListe>
  <item GUID="{...}">
    <name>Gas-Brennwertkessel</name>
    <art>Kessel</art>
    <baujahr>2015</baujahr>
    <energietraeger>Gas</energietraeger>
    <nennleistung>24.0</nennleistung>
  </item>
</hzErzListe>
```

**IFC:**
```
IfcBoiler
  Name: "Gas-Brennwertkessel"
  ObjectType: "Boiler"
  Tag: ???
  → IfcPropertySet "Pset_BoilerTypeCommon"
    → NominalEfficiency: 0.95
    → ??? (kein Standard für Baujahr, Energieträger)
```

**Problem:** IFC hat keine Standard-Properties für Energieberatung

**Lösung für unser Modell:**
```json
{
  "systems": [
    {
      "id": "SYS-001",
      "type": "BOILER",
      "name": "Gas-Brennwertkessel",
      "energy_source": "GAS",
      "year_built": 2015,
      "nominal_power_kw": 24.0,
      "efficiency": 0.95,
      "ifc_element_guid": "...",  // Optional: Verknüpfung zu IFC
      "metadata": {
        "manufacturer": "Viessmann",
        "model": "Vitodens 200-W",
        "serial_number": "..."
      }
    }
  ]
}
```

---

## 💡 ERKENNTNISSE

### Was EVEBI besser macht:

1. **Explizite Energieberatungs-Felder**
   - Nutzungsprofile (DIN 18599 Codes)
   - Orientierung/Neigung (direkt, nicht berechnet)
   - Energieträger (standardisiert)

2. **Einfache Referenzierung**
   - GUID-basiert (wie IFC)
   - Aber: Flache Hierarchie
   - Direkte Konstruktions-Referenzen

3. **Metadaten-Reichtum**
   - Baujahr, Hersteller, Modell
   - Berechnungsmethoden (man/calc)
   - Versionierung (XSDVersion)

4. **Daten-Provenienz**
   - `man` (manuell) vs. `calc` (berechnet)
   - Transparenz über Datenherkunft

---

## 🚀 EMPFEHLUNGEN FÜR UNSER DATENMODELL

### 1. **Sidecar JSON Schema erweitern**

```json
{
  "schema_info": {
    "url": "https://din18599-ifc.de/schema/v2",
    "version": "2.1.0"  // ← Neue Version
  },
  "meta": {
    "project_id": "...",
    "ifc_file_ref": "...",
    "ifc_guid_building": "...",
    "data_quality": {  // ← NEU
      "ifc_completeness": 0.85,
      "manual_overrides": 12,
      "ai_inferred_fields": 5
    }
  },
  "input": {
    "elements": [
      {
        "ifc_guid": "...",
        "position_number": "001",  // ← NEU
        "construction_ref": "CONSTR-001",  // ← Vereinfacht
        "geometry": {
          "orientation": 180,
          "inclination": 90,
          "area": 45.5,
          "calculation_method": "ifc_normal_vector"  // ← NEU
        },
        "thermal": {
          "u_value": 0.2,
          "u_value_source": "construction",  // ← NEU
          "thermal_bridge_delta_u": 0.02,
          "thermal_bridge_type": "SIMPLIFIED"
        },
        "metadata": {  // ← NEU
          "created_at": "2026-04-01T12:00:00Z",
          "modified_at": "2026-04-01T14:30:00Z",
          "data_source": "ifc_import",
          "quality_score": 0.95
        }
      }
    ],
    "constructions": [  // ← NEU: Separate Konstruktions-Bibliothek
      {
        "id": "CONSTR-001",
        "name": "WDVS Außenwand",
        "type": "WALL",
        "u_value": 0.2,
        "layers": [  // Optional: Wenn verfügbar
          {
            "material_id": "MAT-001",
            "thickness": 0.14,
            "position": 1
          }
        ],
        "source": "ifc_material_layers"
      }
    ],
    "zones": [
      {
        "id": "ZONE-001",
        "name": "Erdgeschoss",
        "usage_profile": "17",
        "usage_profile_name": "Wohnen",  // ← NEU
        "usage_profile_source": "manual",  // ← NEU
        "area_an": 80.5,
        "volume_v": 200.0,
        "height_h": 2.5,
        "ifc_space_guids": ["..."],
        "metadata": {  // ← NEU
          "confidence": 0.9,
          "inference_method": "ifc_object_type"
        }
      }
    ]
  }
}
```

### 2. **IFC-Parser erweitern**

```python
# Neue Funktionen:

def extract_position_number(ifc_element) -> Optional[str]:
    """
    Extrahiert PosNo aus:
    1. Tag Property
    2. Name (Regex: "Pos XXX")
    3. Custom PropertySet
    """
    pass

def extract_usage_profile(ifc_space) -> Optional[str]:
    """
    Mappt IFC ObjectType zu DIN 18599 Nutzungsprofil
    
    Mapping:
    - "Wohnraum" → "17"
    - "Büro" → "18"
    - "Klassenzimmer" → "19"
    - etc.
    """
    pass

def calculate_geometry_metadata(ifc_element) -> dict:
    """
    Berechnet Geometrie + Metadaten:
    - Orientierung (Azimut)
    - Neigung
    - Fläche
    - Berechnungsmethode
    - Konfidenz-Score
    """
    pass
```

### 3. **Konstruktions-Bibliothek**

Erstelle eine **zentrale Konstruktions-Bibliothek** (wie EVEBI):

```json
{
  "construction_library": {
    "version": "1.0",
    "constructions": [
      {
        "id": "CONSTR-WALL-WDVS-001",
        "name": "WDVS Außenwand 14cm",
        "type": "WALL",
        "u_value": 0.2,
        "layers": [...],
        "tags": ["außenwand", "wdvs", "standard"],
        "din_4108_compliant": true
      }
    ]
  }
}
```

### 4. **Daten-Provenienz tracken**

Jedes Feld sollte wissen, woher es kommt:

```json
{
  "u_value": 0.2,
  "u_value_source": "ifc_material_layers",  // oder "manual" oder "catalog"
  "u_value_confidence": 0.95,
  "u_value_calculated_at": "2026-04-01T12:00:00Z"
}
```

---

## 🎯 NÄCHSTE SCHRITTE

### Phase 1: Schema-Erweiterung (1-2 Tage)
1. Sidecar JSON Schema v2.1 erstellen
2. Neue Felder dokumentieren
3. Migrations-Guide schreiben

### Phase 2: Parser-Erweiterung (2-3 Tage)
1. PosNo-Extraktion verbessern
2. Nutzungsprofil-Mapping implementieren
3. Geometrie-Metadaten hinzufügen

### Phase 3: Konstruktions-Bibliothek (3-5 Tage)
1. Standard-Konstruktionen definieren
2. Matching-Algorithmus erweitern
3. Katalog-Import implementieren

### Phase 4: Testing & Validierung (2-3 Tage)
1. Mit Real-World Projekten testen
2. Datenqualität messen
3. Dokumentation finalisieren

---

## 📊 ERWARTETE VERBESSERUNGEN

| Metrik | Vorher | Nachher (geschätzt) |
|--------|--------|---------------------|
| **Match-Rate** | 81.2% | **95%+** |
| **Datenqualität** | 75% | **90%+** |
| **Nutzbarkeit** | Mittel | **Hoch** |
| **Wartbarkeit** | Mittel | **Hoch** |

---

## 💡 FAZIT

**EVEBI zeigt uns:**
1. **Einfachheit schlägt Komplexität** (flache Hierarchie vs. IFC-Tiefe)
2. **Domain-spezifische Felder** (Energieberatung > Geometrie)
3. **Daten-Provenienz** (woher kommt der Wert?)
4. **Metadaten-Reichtum** (Baujahr, Hersteller, etc.)

**Unser Weg:**
- Nicht IFC ersetzen, sondern **ergänzen**
- EVEBI-Konzepte in Sidecar JSON **integrieren**
- **Hybrides Modell**: IFC (Geometrie) + EVEBI (Energie) = Perfekt! 🎯
