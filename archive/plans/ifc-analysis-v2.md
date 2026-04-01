# IFC-Analyse v2: DIN18599TestIFCv2.ifc (Komplexes Modell)

**Datum:** 01.04.2026  
**Datei:** `/opt/din18599-ifc/sources/DIN18599TestIFCv2.ifc`  
**Format:** IFC2X3  
**Software:** CASCADOS_V12 12.1.1381.0

---

## 🏗️ IFC-Struktur (Multi-Story)

### Hierarchie
```
IFCPROJECT (DIN18599Test.cad)
└── IFCSITE (Gelände, 51°15'59"N, 8°52'59"E)
    └── IFCBUILDING (<Standard>)
        ├── IFCBUILDINGSTOREY (Erdgeschoss, -0.2m)
        │   ├── IFCSPACE (Räume)
        │   ├── IFCWALLSTANDARDCASE (Wand 001-006)
        │   └── IFCSLAB (Bodenplatte)
        │
        ├── IFCBUILDINGSTOREY (Obergeschoss, 2.7m)
        │   ├── IFCSPACE (Räume)
        │   └── IFCWALLSTANDARDCASE (Wand 007-010)
        │
        └── IFCBUILDINGSTOREY (Dachgeschoss, 5.5m)
            ├── IFCSPACE (Räume)
            ├── IFCWALLSTANDARDCASE (Wand 011-017)
            └── IFCROOF (3 Dächer)
                ├── Dach 2 (Hauptdach)
                ├── Gaube - 001
                └── Dach 3 (Komplex, 7 IFCSLAB)
```

### Geschosse

**Erdgeschoss (EG):**
- Höhe: -0.2m (unter Null)
- Wände: 6x (001-006)
- Höhen: 2.7m - 2.9m

**Obergeschoss (OG):**
- Höhe: 2.7m
- Wände: 4x (007-010)
- Höhen: 2.8m - 2.9m

**Dachgeschoss (DG):**
- Höhe: 5.5m
- Wände: 7x (011-017)
- Höhen: 2.8m - 2.9m
- Dächer: 3x (Hauptdach + Gaube + Komplex)

**Total: 17 Wände + 3 Dächer**

---

## 📐 Geometrie-Komplexität

### Problem: Nicht als Solids darstellbar!

**Warum?**

1. **Unterschiedliche Geschosshöhen:**
   - EG: 2.7m - 2.9m (variabel!)
   - OG: 2.8m - 2.9m
   - DG: 2.8m - 2.9m

2. **Komplexe Dachgeometrie:**
   - 3 separate Dächer
   - Gaube (Dachaufbau)
   - Dach 3 mit 7 IFCSLAB (sehr komplex)

3. **Nicht-rechteckige Grundrisse:**
   - Wände haben unterschiedliche Längen
   - Keine einfache Bounding Box

### Unser Solid-System:

**BOX:**
```json
{
  "type": "BOX",
  "dimensions": {
    "length": 10,  // Einheitlich!
    "width": 8,    // Einheitlich!
    "height": 2.5  // Einheitlich!
  }
}
```

**Problem:** IFC-Wände haben **individuelle** Höhen und Positionen!

---

## 🎯 FAZIT: Zwei Welten

### IFC-Welt (Detailliert, Komplex)
- Jede Wand ist individuell
- Unterschiedliche Höhen
- Komplexe Dächer mit Gauben
- Exakte Geometrie

### Solid-Welt (Vereinfacht, Parametrisch)
- Ein BOX pro Geschoss
- Einheitliche Höhe
- Ein TRIANGULAR_PRISM pro Dach
- Approximierte Geometrie

---

## ✅ EMPFEHLUNG: Hybrid-Ansatz bestätigt!

### Strategie

**1. Für NEUE Projekte: SOLID_GEOMETRY**
```json
{
  "meta": {"mode": "SOLID_GEOMETRY"},
  "geometry": {
    "solids": [
      {"id": "eg", "type": "BOX", "dimensions": {"length": 10, "width": 8, "height": 2.5}},
      {"id": "og", "type": "BOX", "dimensions": {"length": 10, "width": 8, "height": 2.8}},
      {"id": "roof", "type": "TRIANGULAR_PRISM", "dimensions": {...}}
    ]
  }
}
```

**Vorteile:**
- ✅ Einfach zu erstellen
- ✅ Editierbar
- ✅ Schnelle Berechnung
- ✅ Viewer-freundlich

**Nachteile:**
- ❌ Approximation (keine Gauben, keine Details)

---

**2. Für IFC-IMPORT: IFC_LINKED**
```json
{
  "meta": {
    "mode": "IFC_LINKED",
    "ifc_file": "DIN18599TestIFCv2.ifc"
  },
  "envelope": {
    "walls_external": [
      {
        "id": "wall_001",
        "ifc_guid": "1ybs9cI0P0uhJtYtcGuM9Q",
        "area": 20.5,
        "orientation": 180,
        "inclination": 90,
        "u_value_undisturbed": 1.2
      }
    ]
  }
}
```

**Vorteile:**
- ✅ Volle IFC-Details erhalten
- ✅ Exakte Geometrie
- ✅ Keine Konvertierung nötig

**Nachteile:**
- ❌ IFC-Datei muss verfügbar sein
- ❌ Nicht editierbar
- ❌ Viewer muss IFC parsen (komplex)

---

**3. Für IFC-IMPORT mit Vereinfachung: IFC_SIMPLIFIED**
```json
{
  "meta": {
    "mode": "IFC_SIMPLIFIED",
    "ifc_source": "DIN18599TestIFCv2.ifc"
  },
  "geometry": {
    "solids": [
      // Aus IFC generiert (Bounding Boxes)
      {"id": "eg", "type": "BOX", "dimensions": {...}, "ifc_source": "Erdgeschoss"},
      {"id": "og", "type": "BOX", "dimensions": {...}, "ifc_source": "Obergeschoss"}
    ]
  },
  "envelope": {
    "walls_external": [
      // IFC-GUIDs erhalten für Rückverfolgbarkeit
      {"solid_ref": "eg", "face_index": 0, "ifc_guid": "1ybs9cI0P0uhJtYtcGuM9Q"}
    ]
  }
}
```

**Vorteile:**
- ✅ Vereinfachte Geometrie (editierbar)
- ✅ IFC-Rückverfolgbarkeit (GUIDs)
- ✅ Viewer-freundlich

**Nachteile:**
- ❌ Verlust von Details (Gauben, exakte Geometrie)

---

## 📊 Vergleich: v1 vs. v2

| Eigenschaft | v1 (Einfach) | v2 (Komplex) |
|-------------|--------------|--------------|
| **Geschosse** | 1 (EG) | 3 (EG + OG + DG) |
| **Wände** | 6 | 17 |
| **Dächer** | 1 (Satteldach) | 3 (Hauptdach + Gaube + Komplex) |
| **Höhen** | Einheitlich | Variabel (2.7-2.9m) |
| **Grundriss** | Rechteckig | Komplex |
| **Solid-Mapping** | ✅ Möglich | ⚠️ Approximation nötig |

---

## 🚀 Implementierungs-Strategie

### Phase 1: SOLID_GEOMETRY Modus (MVP)
1. ✅ Schema mit `mode` Feld
2. ✅ Geometry Generators (BOX + TRIANGULAR_PRISM)
3. ✅ SolidRenderer Component
4. ✅ Demo-JSON (einfaches Haus)

### Phase 2: IFC_LINKED Modus
1. Schema erweitern (area, orientation, inclination optional)
2. Viewer: Schematische Darstellung aus area/orientation
3. Demo-JSON: v1 als IFC_LINKED

### Phase 3: IFC_SIMPLIFIED Modus (Optional)
1. IFC-Import Tool
2. Bounding Box Berechnung
3. Solid-Generierung
4. GUID-Mapping

---

## ✅ NÄCHSTER SCHRITT

**Jetzt implementieren:**
1. Schema: `meta.mode` Feld hinzufügen
2. Viewer: SOLID_GEOMETRY Modus (Priorität!)
3. Testing mit Demo-JSON

**Später:**
- IFC_LINKED Modus
- IFC-Import Tool

---

**Status:** ✅ Komplexes IFC analysiert, Strategie bestätigt  
**Erkenntnis:** Solid-System ist für **neue/einfache** Projekte ideal, IFC-Linked für **komplexe/importierte** Projekte
