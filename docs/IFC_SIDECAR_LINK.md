# IFC ↔ DIN 18599 Sidecar Verknüpfung

**Ziel:** Klare Definition, wie IFC-Geometrie und DIN 18599 Energiedaten zusammenhängen.

---

## 1. Grundprinzip

```
┌─────────────────────────────────────────────────────────┐
│  IFC-Datei (Geometrie)                                  │
│  - IfcBuilding (GUID: 2Uj8Lq3Vr9QxPkXr4bN8FD)          │
│  - IfcSpace (GUID: 3Fk9Mp4Ws0RyQlYs5cO9GE)            │
│  - IfcWall (GUID: 1Ab2Cd3Ef4Gh5Ij6Kl7Mn8)             │
│  - IfcWindow (GUID: 2Bc3De4Fg5Hi6Jk7Lm8No9)           │
└─────────────────────────────────────────────────────────┘
                         ↓
                    Verknüpfung via GUID
                         ↓
┌─────────────────────────────────────────────────────────┐
│  DIN 18599 Sidecar JSON (Energiedaten)                 │
│  - meta.ifc_guid_building: "2Uj8Lq3Vr9QxPkXr4bN8FD"    │
│  - zones[].space_guids: ["3Fk9Mp4Ws0RyQlYs5cO9GE"]     │
│  - elements[].ifc_guid: "1Ab2Cd3Ef4Gh5Ij6Kl7Mn8"       │
│  - windows[].ifc_guid: "2Bc3De4Fg5Hi6Jk7Lm8No9"        │
└─────────────────────────────────────────────────────────┘
```

**Kern-Idee:**
- **IFC = Geometrie** (Wände, Räume, Fenster mit Koordinaten)
- **Sidecar = Physik** (U-Werte, Materialien, Systeme)
- **GUID = Verknüpfung** (eindeutige IFC-IDs referenzieren)

---

## 2. IFC-Kern: Welche Daten kommen aus IFC?

### 2.1 Geometrie (aus IFC)

| IFC-Klasse | Attribute | Verwendung in DIN 18599 |
|------------|-----------|-------------------------|
| **IfcBuilding** | GlobalId, Name | Projekt-Identifikation (`meta.ifc_guid_building`) |
| **IfcSpace** | GlobalId, Name, GrossFloorArea, NetFloorArea, Volume | Zonierung (`zones[].space_guids`, `area_an`, `volume_v`) |
| **IfcWall** | GlobalId, Name, Geometry | Opake Bauteile (`elements[].ifc_guid`) |
| **IfcSlab** | GlobalId, Name, PredefinedType (ROOF, FLOOR, BASESLAB) | Opake Bauteile (`elements[].ifc_guid`) |
| **IfcRoof** | GlobalId, Name | Opake Bauteile (`elements[].ifc_guid`) |
| **IfcWindow** | GlobalId, Name, OverallWidth, OverallHeight | Transparente Bauteile (`windows[].ifc_guid`) |
| **IfcDoor** | GlobalId, Name | Transparente Bauteile (wenn außenliegend) |
| **IfcRelSpaceBoundary** | RelatingSpace, RelatedBuildingElement | Zuordnung Raum ↔ Bauteil |

### 2.2 Was IFC NICHT liefert (kommt aus Sidecar)

- ❌ **U-Werte** (nicht in IFC-Standard)
- ❌ **Schichtaufbauten** (nur rudimentär in `IfcMaterialLayerSet`)
- ❌ **Wärmebrücken** (nicht standardisiert)
- ❌ **Anlagentechnik** (nur Platzhalter in IFC)
- ❌ **Nutzungsprofile** (nicht energetisch)
- ❌ **Energiebedarfe** (Ergebnis der Berechnung)

**→ Deshalb brauchen wir das Sidecar!**

---

## 3. Verknüpfungs-Matrix

### 3.1 Gebäude-Ebene

```json
{
  "meta": {
    "ifc_file_ref": "musterhaus.ifc",
    "ifc_guid_building": "2Uj8Lq3Vr9QxPkXr4bN8FD"
  }
}
```

**Bedeutung:**
- `ifc_file_ref`: Dateiname der IFC-Datei (relativ oder absolut)
- `ifc_guid_building`: GlobalId des `IfcBuilding`-Objekts

**Verwendung:**
- Eindeutige Zuordnung Sidecar ↔ IFC-Datei
- Validierung: "Gehört dieses Sidecar zu diesem IFC?"

---

### 3.2 Zonen-Ebene

```json
{
  "zones": [
    {
      "id": "ZONE-01",
      "name": "Wohnbereich EG",
      "space_guids": [
        "3Fk9Mp4Ws0RyQlYs5cO9GE",
        "4Gl0Nq5Xt2SzTmZt6dP1HF"
      ],
      "area_an": 85.5,
      "volume_v": 213.75
    }
  ]
}
```

**Bedeutung:**
- `space_guids`: Array von `IfcSpace.GlobalId`
- Eine thermische Zone kann **mehrere IFC-Räume** umfassen
- `area_an`, `volume_v` können aus IFC übernommen oder überschrieben werden

**Mapping:**
```
IfcSpace.GlobalId → zones[].space_guids[]
IfcSpace.GrossFloorArea → zones[].area_an (optional)
IfcSpace.Volume → zones[].volume_v (optional)
```

**Wichtig:**
- Wenn `area_an` im Sidecar gesetzt ist → **überschreibt** IFC-Wert
- Wenn nicht gesetzt → kann aus IFC berechnet werden (Summe aller Spaces)

---

### 3.3 Bauteil-Ebene (Opak)

```json
{
  "elements": [
    {
      "ifc_guid": "1Ab2Cd3Ef4Gh5Ij6Kl7Mn8",
      "boundary_condition": "EXTERIOR",
      "u_value_undisturbed": 0.24,
      "thermal_bridge_delta_u": 0.05,
      "orientation": 180,
      "inclination": 90
    }
  ]
}
```

**Bedeutung:**
- `ifc_guid`: GlobalId von `IfcWall`, `IfcSlab`, `IfcRoof`, etc.
- `orientation`, `inclination` können aus IFC-Geometrie berechnet werden

**Mapping:**
```
IfcWall.GlobalId → elements[].ifc_guid
IfcWall.Geometry → elements[].orientation (berechnet aus Normalenvektor)
IfcWall.Geometry → elements[].inclination (berechnet aus Normalenvektor)
```

**Wichtig:**
- Wenn `orientation` im Sidecar gesetzt → **überschreibt** IFC-Geometrie
- Wenn nicht gesetzt → muss aus IFC berechnet werden

---

### 3.4 Fenster-Ebene (Transparent)

```json
{
  "windows": [
    {
      "ifc_guid": "2Bc3De4Fg5Hi6Jk7Lm8No9",
      "u_value_glass": 0.7,
      "u_value_frame": 1.3,
      "g_value": 0.5,
      "frame_fraction": 0.25
    }
  ]
}
```

**Bedeutung:**
- `ifc_guid`: GlobalId von `IfcWindow` oder `IfcDoor`
- Fläche kann aus IFC berechnet werden (`OverallWidth × OverallHeight`)

**Mapping:**
```
IfcWindow.GlobalId → windows[].ifc_guid
IfcWindow.OverallWidth × OverallHeight → Fensterfläche (berechnet)
```

---

## 4. Datenfluss: IFC → Sidecar → Berechnung

```
┌─────────────────────┐
│  1. IFC-Import      │
│  - Geometrie laden  │
│  - GUIDs extrahieren│
│  - Flächen berechnen│
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  2. Sidecar-Erstellung│
│  - GUIDs referenzieren│
│  - U-Werte ergänzen  │
│  - Systeme definieren│
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  3. Merge (Runtime) │
│  - IFC + Sidecar    │
│  - Geometrie + Physik│
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  4. DIN 18599 Calc  │
│  - Energiebedarf    │
│  - Primärenergie    │
│  - Effizienzklasse  │
└──────────┬──────────┘
           ↓
┌─────────────────────┐
│  5. Output (Sidecar)│
│  - Ergebnisse       │
│  - Kennwerte        │
└─────────────────────┘
```

---

## 5. Vollständigkeits-Check

### ✅ Was ist vollständig definiert?

| Bereich | Status | Dokumentation |
|---------|--------|---------------|
| **IFC-Gebäude-Link** | ✅ | `meta.ifc_guid_building`, `meta.ifc_file_ref` |
| **IFC-Zonen-Link** | ✅ | `zones[].space_guids[]` |
| **IFC-Bauteil-Link** | ✅ | `elements[].ifc_guid`, `windows[].ifc_guid` |
| **U-Werte** | ✅ | `elements[].u_value_undisturbed`, `windows[].u_value_glass/frame` |
| **Wärmebrücken** | ✅ | `elements[].thermal_bridge_delta_u`, `thermal_bridge_type` |
| **Schichtaufbauten** | ✅ | `layer_structures[]` mit `layers[]` |
| **Materialien** | ✅ | `materials[]` inkl. `AIR_LAYER` |
| **Systeme** | ✅ | `systems[]`, `distribution[]`, `dhw[]`, `ventilation[]`, `lighting[]` |
| **LOD-Konzept** | ✅ | `meta.lod` (100-500) |
| **Varianten** | ✅ | `base` + `scenarios[]` (Delta-Modell) |
| **Kataloge** | ✅ | Bundesanzeiger 2020 (97 U-Werte) |

### ⚠️ Was fehlt noch?

| Bereich | Status | Nächster Schritt |
|---------|--------|------------------|
| **IFC-Geometrie-Berechnung** | ⚠️ | Dokumentieren: Wie werden Flächen/Orientierung aus IFC extrahiert? |
| **IfcRelSpaceBoundary** | ⚠️ | Wie werden Raum-Bauteil-Zuordnungen genutzt? |
| **Flächenberechnung** | ⚠️ | Netto vs. Brutto, AN vs. NGF |
| **IFC-Property Sets** | ⚠️ | Können U-Werte aus `Pset_WallCommon` kommen? |
| **IFC-Material-Mapping** | ⚠️ | Wie werden `IfcMaterialLayerSet` → `layer_structures` gemappt? |

---

## 6. Best Practices

### 6.1 GUID-Konsistenz

**Problem:** IFC-GUIDs ändern sich bei Re-Export  
**Lösung:** 
- IFC-Software sollte GUIDs **stabil** halten
- Alternativ: Mapping-Tabelle pflegen (alt → neu)

### 6.2 Fehlende IFC-Elemente

**Problem:** Sidecar referenziert GUID, die nicht in IFC existiert  
**Lösung:**
- Validator prüft GUID-Existenz
- Warnung ausgeben, aber nicht abbrechen

### 6.3 Mehrfach-Referenzierung

**Problem:** Ein `IfcWall` wird in mehreren Zonen verwendet  
**Lösung:**
- `IfcRelSpaceBoundary` definiert Zuordnung
- Bauteil kann mehrere `boundary_condition` haben (z.B. EXTERIOR + HEATED)

### 6.4 IFC-Geometrie vs. Sidecar-Werte

**Regel:**
- **Sidecar überschreibt IFC** (explizit > implizit)
- Wenn `orientation` im Sidecar → nutze Sidecar-Wert
- Wenn nicht → berechne aus IFC-Geometrie

---

## 7. Beispiel: Vollständige Verknüpfung

### IFC-Datei (vereinfacht)

```ifc
#1 = IFCBUILDING('2Uj8Lq3Vr9QxPkXr4bN8FD', 'Musterhaus', ...);
#2 = IFCSPACE('3Fk9Mp4Ws0RyQlYs5cO9GE', 'Wohnzimmer', ...);
#3 = IFCWALL('1Ab2Cd3Ef4Gh5Ij6Kl7Mn8', 'Außenwand Süd', ...);
#4 = IFCWINDOW('2Bc3De4Fg5Hi6Jk7Lm8No9', 'Fenster Süd', ...);
```

### Sidecar JSON

```json
{
  "schema_info": {
    "url": "https://din18599-ifc.de/schema/v1",
    "version": "2.0.0"
  },
  "meta": {
    "ifc_file_ref": "musterhaus.ifc",
    "ifc_guid_building": "2Uj8Lq3Vr9QxPkXr4bN8FD",
    "lod": "300"
  },
  "input": {
    "zones": [
      {
        "id": "ZONE-01",
        "name": "Wohnbereich",
        "space_guids": ["3Fk9Mp4Ws0RyQlYs5cO9GE"],
        "area_an": 35.5,
        "volume_v": 88.75
      }
    ],
    "elements": [
      {
        "ifc_guid": "1Ab2Cd3Ef4Gh5Ij6Kl7Mn8",
        "boundary_condition": "EXTERIOR",
        "u_value_undisturbed": 0.24,
        "thermal_bridge_delta_u": 0.05,
        "orientation": 180,
        "inclination": 90
      }
    ],
    "windows": [
      {
        "ifc_guid": "2Bc3De4Fg5Hi6Jk7Lm8No9",
        "u_value_glass": 0.7,
        "u_value_frame": 1.3,
        "g_value": 0.5,
        "frame_fraction": 0.25
      }
    ]
  }
}
```

### Verknüpfung

```
IFC Building (2Uj8Lq3Vr...) ←→ meta.ifc_guid_building
IFC Space (3Fk9Mp4Ws...) ←→ zones[0].space_guids[0]
IFC Wall (1Ab2Cd3Ef...) ←→ elements[0].ifc_guid
IFC Window (2Bc3De4Fg...) ←→ windows[0].ifc_guid
```

---

## 8. Offene Fragen für Implementierung

1. **IFC-Parser:** Welche Library? (xbim, web-ifc, ifc.js?)
2. **Geometrie-Berechnung:** Wie werden Normalenvektoren → Orientierung berechnet?
3. **Flächenberechnung:** Netto vs. Brutto? AN vs. NGF?
4. **Property Sets:** Sollen `Pset_*` ausgelesen werden?
5. **Material-Mapping:** `IfcMaterialLayerSet` → `layer_structures`?
6. **Validierung:** GUID-Existenz-Check im Validator?

---

## 9. Nächste Schritte

- [ ] **IFC-Geometrie-Extraktion** dokumentieren (Normalenvektor → Orientierung)
- [ ] **Flächenberechnung** spezifizieren (AN-Berechnung aus IFC)
- [ ] **Validator erweitern:** GUID-Existenz-Check
- [ ] **Beispiel-IFC** erstellen (mit GUIDs aus Beispiel-JSONs)
- [ ] **IFC-Parser-Evaluation** (web-ifc vs. xbim vs. ifc.js)

---

**Status:** ✅ IFC-Kern und Sidecar-Link sind **konzeptionell vollständig definiert**.  
**Fehlende Details:** Implementierungs-Spezifikation für Geometrie-Extraktion.
