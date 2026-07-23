# Migration Guide: Schema v2.2 → v2.3

## Überblick

**Kernänderung:** Flache Struktur mit **dwelling_units, zones, rooms** statt hierarchischer Verschachtelung.

**Begründung:** Räume können sowohl einer Zone als auch einer Wohneinheit zugeordnet sein. Wohneinheiten können mehrere Zonen haben. Hierarchie ist zu starr.

---

## Hauptänderung: Flache Struktur

### v2.2 (ALT) - Hierarchisch
```json
"building": {
  "zones": [
    {
      "id": "space_guid_1",
      "name": "Wohnzimmer",  // IfcSpace direkt als Zone
      "area": 22.5,
      "volume": 56.25,
      "height": 2.5,
      "usage_profile_ref": "wohnen"
    }
  ]
}
```

**Problem:** IfcSpace ≠ Thermische Zone
- 33 Räume → 33 "Zonen" (fachlich falsch)
- Keine Wohneinheiten
- Keine Aggregation möglich

### v2.3 (NEU) - Flach mit Referenzen
```json
"building": {
  "dwelling_units": [
    {
      "id": "dwelling_1",
      "name": "Wohnung EG links",
      "type": "residential",
      "area": 65.5
    }
  ],
  "zones": [
    {
      "id": "zone_1",
      "name": "Wohnen EG",
      "usage_profile_ref": "wohnen_din18599-10",
      "area": 45.5,      // Aggregiert aus rooms
      "volume": 125.0,
      "height": 2.75
    }
  ],
  "rooms": [
    {
      "id": "space_guid_1",
      "ifc_guid": "space_guid_1",
      "name": "Wohnzimmer",
      "area": 22.5,
      "volume": 56.25,
      "height": 2.5,
      "zone_ref": "zone_1",           // Referenz zu Zone
      "dwelling_unit_ref": "dwelling_1", // Optional
      "storey_ref": "storey_eg"
    },
    {
      "id": "space_guid_2",
      "name": "Küche",
      "area": 12.0,
      "zone_ref": "zone_1",           // Gleiche Zone
      "dwelling_unit_ref": "dwelling_1"
    },
    {
      "id": "space_guid_3",
      "name": "Bad",
      "area": 6.0,
      "zone_ref": "zone_2",           // Andere Zone (24°C)
      "dwelling_unit_ref": "dwelling_1"  // Gleiche Wohneinheit
    }
  ]
}
```

**Vorteile:**
- ✅ Räume (IfcSpace) korrekt abgebildet
- ✅ Zonen (thermisch) separat definiert
- ✅ Wohneinheiten unabhängig
- ✅ Flexible Zuordnung via Referenzen
- ✅ Mehrere Räume → 1 Zone
- ✅ 1 Wohneinheit → mehrere Zonen

---

## Neue Definitionen

### dwelling_unit (NEU)
```json
{
  "id": "dwelling_1",
  "ifc_guid": "...",  // Optional (IfcBuilding oder custom)
  "name": "Wohnung EG links",
  "type": "residential",  // residential, commercial, common_area
  "area": 65.5,           // Aggregiert aus rooms
  "volume": 180.0
}
```

**Verwendung:**
- Wohngebäude: Mehrere Wohneinheiten pro Gebäude
- Nichtwohngebäude: Kann leer sein
- Gemeinschaftsflächen: type="common_area"

### zone (GEÄNDERT)
```json
{
  "id": "zone_1",
  "ifc_guid": "...",  // IfcZone falls vorhanden
  "name": "Wohnen EG",
  "usage_profile_ref": "wohnen_din18599-10",  // REQUIRED
  "area": 45.5,       // Aggregiert aus rooms
  "volume": 125.0,    // REQUIRED
  "height": 2.75,     // REQUIRED
  "setpoint_heating_c": 20,
  "conditioned": true
}
```

**Änderungen:**
- `volume`, `height` jetzt REQUIRED (waren optional in v2.2)
- Werte werden aus `rooms` aggregiert
- `ifc_guid` optional (IfcZone selten vorhanden)

### room (NEU)
```json
{
  "id": "space_guid_1",
  "ifc_guid": "space_guid_1",  // IfcSpace GUID
  "name": "Wohnzimmer",
  "area": 22.5,
  "volume": 56.25,
  "height": 2.5,
  "zone_ref": "zone_1",           // Referenz zu Zone
  "dwelling_unit_ref": "dwelling_1", // Optional
  "storey_ref": "storey_eg"
}
```

**Mapping:**
- `IfcSpace` → `room`
- `room.zone_ref` → Thermische Zone
- `room.dwelling_unit_ref` → Wohneinheit (optional)

---

## Änderungen an envelope

### opaque_element + transparent_element

**NEU:**
```json
{
  "zone_ref": "zone_1",     // Statt direkt zone_ref
  "room_ref": "space_guid_1"  // NEU: Optional, für detaillierte Zuordnung
}
```

**Entfernt:**
- Keine Änderungen an bestehenden Feldern

---

## Migration-Schritte

### 1. Parser-Anpassung

**ALT (v2.2):**
```python
"zones": [
    {
        "id": s['id'],
        "ifc_guid": s['ifc_guid'],
        "name": s['name'],
        "area": s.get('area'),
        "volume": s.get('volume'),
        "height": s.get('height'),
        "storey_ref": s.get('storey_ref'),
        "usage_profile_ref": None,
    }
    for s in geometry.spaces
]
```

**NEU (v2.3):**
```python
"dwelling_units": [],  # Wird manuell oder aus IFC ergänzt
"zones": [],           # Wird manuell oder aus IfcZone ergänzt
"rooms": [
    {
        "id": s['id'],
        "ifc_guid": s['ifc_guid'],
        "name": s['name'],
        "area": s.get('area'),
        "volume": s.get('volume'),
        "height": s.get('height'),
        "zone_ref": None,           # Wird manuell ergänzt
        "dwelling_unit_ref": None,  # Optional
        "storey_ref": s.get('storey_ref')
    }
    for s in geometry.spaces
]
```

### 2. Zone-Aggregation (manuell oder automatisch)

**Manuell:**
```json
{
  "zones": [
    {
      "id": "zone_wohnen_eg",
      "name": "Wohnen EG",
      "usage_profile_ref": "wohnen_din18599-10",
      "area": 45.5,  // Summe: 22.5 + 12.0 + 11.0
      "volume": 125.0,
      "height": 2.75
    }
  ],
  "rooms": [
    {"id": "r1", "name": "Wohnzimmer", "area": 22.5, "zone_ref": "zone_wohnen_eg"},
    {"id": "r2", "name": "Küche", "area": 12.0, "zone_ref": "zone_wohnen_eg"},
    {"id": "r3", "name": "Flur", "area": 11.0, "zone_ref": "zone_wohnen_eg"}
  ]
}
```

**Automatisch (falls IfcZone vorhanden):**
```python
# Parser extrahiert IfcZone
for ifc_zone in ifc_file.by_type('IfcZone'):
    zone = {
        'id': ifc_zone.GlobalId,
        'name': ifc_zone.Name,
        'area': 0,
        'volume': 0
    }
    # Aggregiere aus zugeordneten Spaces
    for rel in ifc_zone.IsGroupedBy:
        for space in rel.RelatedObjects:
            if space.is_a('IfcSpace'):
                zone['area'] += get_area(space)
                zone['volume'] += get_volume(space)
```

---

## Abwärtskompatibilität

**Keine Abwärtskompatibilität** - v2.3 ist ein Breaking Change.

**Grund:** Fundamentale Strukturänderung (zones → rooms + zones).

**Migration:**
```python
# v2.2 → v2.3
def migrate_v22_to_v23(old_data):
    return {
        "dwelling_units": [],  # Manuell ergänzen
        "zones": [],           # Manuell ergänzen
        "rooms": old_data['building']['zones']  # Alte "zones" sind jetzt "rooms"
    }
```

---

## Validierung

**Test mit DIN18599TestIFCv4.ifc:**

```json
{
  "building": {
    "dwelling_units": [
      {
        "id": "dwelling_eg",
        "name": "Wohnung EG",
        "type": "residential",
        "area": 85.5
      }
    ],
    "zones": [
      {
        "id": "zone_wohnen",
        "name": "Wohnen",
        "usage_profile_ref": "wohnen_din18599-10",
        "area": 65.5,
        "volume": 180.0,
        "height": 2.75
      },
      {
        "id": "zone_bad",
        "name": "Bad",
        "usage_profile_ref": "bad_din18599-10",
        "area": 6.0,
        "volume": 15.0,
        "height": 2.5
      }
    ],
    "rooms": [
      {"id": "r1", "name": "Galarie", "area": 9.57, "zone_ref": "zone_wohnen", "dwelling_unit_ref": "dwelling_eg"},
      {"id": "r2", "name": "Bad", "area": 6.62, "zone_ref": "zone_bad", "dwelling_unit_ref": "dwelling_eg"},
      {"id": "r3", "name": "Garage", "area": 11.96, "zone_ref": "zone_wohnen", "dwelling_unit_ref": "dwelling_eg"}
    ]
  }
}
```

---

## Zusammenfassung

| Änderung | v2.2 | v2.3 | Begründung |
|----------|------|------|------------|
| **Struktur** | Hierarchisch (zones) | Flach (dwelling_units, zones, rooms) | Flexible Zuordnung |
| **IfcSpace** | → zone | → room | Fachlich korrekt |
| **Thermische Zone** | = IfcSpace | Separat definiert | DIN 18599-konform |
| **Wohneinheiten** | Fehlt | dwelling_units[] | Mehrfamilienhäuser |
| **Referenzen** | Implizit | Explizit (zone_ref, dwelling_unit_ref) | Flexibel |
| **Aggregation** | Nicht möglich | Möglich (rooms → zone) | Mehrere Räume → 1 Zone |

**Ergebnis:** Schema v2.3 ist **fachlich korrekt** für DIN 18599 und **flexibel** für verschiedene Gebäudetypen.
