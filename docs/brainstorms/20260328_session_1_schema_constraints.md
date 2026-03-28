# Brainstorm Session #1: Schema-Constraints Review

**Datum:** 28. März 2026  
**Teilnehmer:** User + Cascade AI  
**Dauer:** ~90 Minuten  
**Ziel:** Entscheidungen für Schema v2.1 - Required-Felder, Enums, Fx-Werte, Varianten-Modell, Nutzungsprofile

---

## 📋 Zusammenfassung - Alle Entscheidungen

### ✅ 1. Required-Felder & ID-Strategie

**Entscheidung: Option B - ID-First**
- `id` ist **IMMER Pflicht** (für Delta-Merge, Referenzen)
- `ifc_guid` ist **optional** (nur für IFC-Linked Modus)
- **Vorteil:** Standalone-Modus (ohne IFC) funktioniert

**Required-Felder für Elements:**
- `id` (String)
- `type` (Enum)
- `boundary_condition` (Enum)

**Required-Felder für Windows:**
- `id` (String)

**Required-Felder für Zones:**
- `id` (String)
- `usage_profile` (Object)

---

### ✅ 2. Element-Typ mit UNDEFINED

**Entscheidung: Required mit UNDEFINED Enum-Wert**

```json
{
  "type": {
    "enum": ["WALL", "ROOF", "FLOOR", "CEILING", "DOOR", "UNDEFINED"],
    "description": "UNDEFINED = Typ unbekannt, Element wird nicht in Berechnung berücksichtigt"
  }
}
```

**Begründung:**
- Explizit: "Ich weiß nicht, was das ist"
- Validator kann warnen
- Berechnung kann Element überspringen

---

### ✅ 3. Element-Status (NEU)

**Entscheidung: Neues Feld `status` als Enum**

```json
{
  "status": {
    "enum": ["ACTIVE", "PASSIVE", "PLANNED", "DEMOLISHED"],
    "default": "ACTIVE",
    "description": "ACTIVE: In Berechnung berücksichtigt, PASSIVE: Nicht berücksichtigt, PLANNED: Geplante Sanierung, DEMOLISHED: Rückbau"
  }
}
```

**Use Cases:**
- ACTIVE: Normaler Betrieb, in Berechnung
- PASSIVE: Dokumentiert, aber nicht aktiv (z.B. temporär deaktiviert)
- PLANNED: Geplante Sanierung (iSFP)
- DEMOLISHED: Rückbau dokumentieren

---

### ✅ 4. boundary_condition Enum (erweitert)

**Entscheidung: 9 Werte basierend auf DIN 18599-2 Tabelle 5**

```json
{
  "boundary_condition": {
    "enum": [
      "EXTERIOR",                    // Fx = 1.0 (Außenluft)
      "GROUND",                      // Fx = 0.8 (Erdreich, vereinfacht)
      "INTERIOR",                    // Fx = 0.0 (gleiche Temperatur)
      "HEATED",                      // Fx = 0.0 (zu beheiztem Raum)
      "UNHEATED",                    // Fx = 0.5 (zu unbeheiztem Raum)
      "UNHEATED_ROOF_UNINSULATED",   // Fx = 0.8 (DIN Tabelle 5, Zeile 2)
      "UNHEATED_ROOF_INSULATED",     // Fx = 0.5 (DIN Tabelle 5, Zeile 3)
      "LOW_HEATED",                  // Fx = 0.35 (12-19°C, Treppenhaus)
      "ADIABATIC"                    // Fx = 0.0 (keine Wärmeübertragung)
    ]
  }
}
```

**Mapping zu DIN 18599-2 Tabelle 5:**
- Zeile 1: EXTERIOR (Fe = 1.0)
- Zeile 2: UNHEATED_ROOF_UNINSULATED (FD = 0.8)
- Zeile 3: UNHEATED, UNHEATED_ROOF_INSULATED (Fu = 0.5)
- Zeile 4: LOW_HEATED (Fnb = 0.35)

---

### ✅ 5. Fx-Wert (Temperaturfaktor)

**Entscheidung: Optional mit Automatik + Bodenplatten-Parameter**

```json
{
  "f_x": {
    "type": "number",
    "minimum": 0,
    "maximum": 1,
    "description": "Temperaturfaktor DIN V 18599-2. Optional - wird aus boundary_condition berechnet wenn nicht angegeben. Für Bodenplatten: Manuell nach Tabelle 6 setzen."
  },
  "ground_properties": {
    "type": "object",
    "description": "Für Bodenplatten: Parameter für Fx-Berechnung nach DIN 18599-2 Tabelle 6",
    "properties": {
      "characteristic_dimension_b": {
        "type": "number",
        "description": "Charakteristisches Bodenplattenmaß B = Ag / (0.5 * P) in m"
      },
      "thermal_resistance_rf": {
        "type": "number",
        "description": "Wärmedurchlasswiderstand Rf in m²K/W"
      },
      "edge_insulation": {
        "type": "object",
        "properties": {
          "type": { "enum": ["NONE", "HORIZONTAL", "VERTICAL"] },
          "depth_d": { "type": "number", "description": "Tiefe/Breite in m" },
          "thermal_resistance": { "type": "number", "description": "R_WD,RD in m²K/W" }
        }
      }
    }
  }
}
```

**Workflow:**
1. **Einfacher Fall:** Nur `boundary_condition` → Fx automatisch
2. **Komplexer Fall (Bodenplatte):** `boundary_condition: "GROUND"` + `f_x: 0.25` (manuell berechnet)
3. **Berechnung:** Im Berechnungsprogramm, nicht im Format
4. **Später:** Viewer/Editor kann Fx-Logik einbauen (v2.2+)

---

### ✅ 6. Varianten-Modell (ZENTRAL in Meta)

**Entscheidung: meta.variants[] mit dependency_type**

```json
{
  "meta": {
    "variants": [
      {
        "id": "VAR-IST",
        "name": "IST-Zustand",
        "type": "BASE",
        "dependency_type": null,
        "depends_on": null,
        "description": "Bestand vor Sanierung"
      },
      {
        "id": "VAR-STUFE1",
        "name": "Stufe 1: WDVS + Fenster",
        "type": "SCENARIO",
        "dependency_type": "ADDITIVE",
        "depends_on": "VAR-IST",
        "priority": 1,
        "timeline": 2026,
        "funding": "BEG_EM",
        "description": "Außenwände dämmen + Fenster tauschen"
      },
      {
        "id": "VAR-STUFE2",
        "name": "Stufe 2: Dach + Heizung",
        "type": "SCENARIO",
        "dependency_type": "ADDITIVE",
        "depends_on": "VAR-STUFE1",
        "priority": 2,
        "timeline": 2028,
        "funding": "BEG_EM"
      }
    ]
  }
}
```

**dependency_type Enum:**
- **ADDITIVE:** Baut auf vorheriger Variante auf (iSFP-Stufen)
- **ALTERNATIVE:** Alternative zur vorherigen (Planungsvarianten)

**Element-Zuordnung:**
```json
{
  "id": "AW-01",
  "variant_id": "VAR-IST",
  "type": "WALL",
  "u_value": 1.2
}
```

**Vorteile:**
- ✅ Zentrale Varianten-Definition (iSFP-Roadmap)
- ✅ Zeitliche Abfolge (timeline)
- ✅ Förderung (funding) pro Variante
- ✅ Prioritäten (priority)
- ✅ Delta-Modell bleibt sauber

---

### ✅ 7. Nutzungsprofile (Wohnen vs. NWG)

**Entscheidung: Zwei Profile-Typen + Norm vs. Individuelle Werte**

```json
{
  "usage_profile": {
    "type": "RESIDENTIAL",
    "building_type": "MFH",
    "source": "DIN_18599_10",
    "parameters_din": {
      "theta_i_h_soll": 20,
      "theta_i_c_soll": 25,
      "q_i": 90,
      "n_nutz": 0.5
      // ... alle Werte aus DIN 18599-10 Tabelle 5
    },
    "parameters_individuell": {
      "theta_i_h_soll": 22,
      "theta_i_c_soll": 23
      // ... nur Abweichungen zur Norm
    }
  }
}
```

**Für Nichtwohngebäude:**
```json
{
  "usage_profile": {
    "type": "NON_RESIDENTIAL",
    "profile_id": "01",
    "source": "DIN_18599_10",
    "parameters_din": {
      // ... alle Werte aus DIN 18599-10 Tabelle 6+7
    },
    "parameters_individuell": {
      // ... nur Abweichungen
    }
  }
}
```

**Wichtig:**
- Wohnen bekommt **eigene Behandlung** (EFH/MFH)
- 43 Nutzungsprofile für Nichtwohngebäude (01-43)
- Norm-Werte in `parameters_din`
- Individuelle Werte in `parameters_individuell`
- Katalog: `catalog/usage_profiles.json`

---

### ✅ 8. uniqueItems

**Entscheidung: Custom Validator (Phase 1, Woche 2)**

JSON Schema Draft-07 kann nur ganze Objekte prüfen, nicht einzelne Felder.

**Lösung:**
- Python Validator erweitern
- JavaScript Validator (für Viewer)
- Prüfung auf doppelte IDs in Arrays

---

### ✅ 9. additionalProperties

**Entscheidung: Option C - Hybrid mit x-Präfix**

```json
{
  "additionalProperties": false,
  "patternProperties": {
    "^x-": { }
  }
}
```

**Vorteil:**
- ✅ Strikt für Standard-Felder
- ✅ Erweiterbar für Software-spezifische Felder (`x-mysoft-custom-field`)

---

## 📊 DIN 18599 Referenzen

### Tabelle 5 - Fx-Werte (Bauteile außer Bodenplatte)

| Zeile | Boundary Condition | Fx | Beschreibung |
|-------|-------------------|-----|--------------|
| 1 | EXTERIOR | 1.0 | Außenwand, Fenster, Dach |
| 2 | UNHEATED_ROOF_UNINSULATED | 0.8 | Zu unbeheiztem, nicht gedämmtem Dachraum |
| 3 | UNHEATED, UNHEATED_ROOF_INSULATED | 0.5 | Zu unbeheiztem Raum |
| 4 | LOW_HEATED | 0.35 | Zu niedrig beheiztem Raum (12-19°C) |

### Tabelle 6 - Fx-Werte (Bodenplatte)

**Vereinfachung (Fußnote a):**
> "Vereinfacht darf für die Bauteile des unteren Gebäudeabschlusses der Temperaturkorrekturfaktor mit **Fx = 0.8** angenommen werden."

**Detailliert:** Fx hängt ab von:
- Bodenplattenmaß B (0-32m)
- Wärmedurchlasswiderstand Rf (0.5-2.5 m²K/W)
- Randdämmung (horizontal/vertikal, Tiefe D)
- Keller (beheizt/unbeheizt)
- **Fx-Bereich:** 0.05 - 0.80

---

## 🎯 Nächste Schritte

1. ✅ Schema v2.1 implementieren (sichere Punkte)
2. ⏳ Session #2: Delta-Merge-Algorithmus
3. ⏳ Session #3: Katalog-Architektur
4. ⏳ DIN 18599-10 Profile in JSON konvertieren (43 NWG + Wohnen)
5. ⏳ docs/SCHEMA_V2.1_CONCEPT.md erstellen

---

## 📝 Offene Fragen (für Session #2+3)

1. **Delta-Merge:** Wie werden Arrays gemerged? (append, replace, merge by id?)
2. **Katalog-Referenzen:** Wie funktioniert `construction_ref` vs. `layer_structure_ref`?
3. **Material-Override:** Können Katalog-Materialien überschrieben werden?
4. **Nutzungsprofile-Katalog:** Struktur für 43 Profile + Wohnen?

---

**Status:** ✅ Session #1 abgeschlossen  
**Nächste Session:** #2 Delta-Merge-Algorithmus
