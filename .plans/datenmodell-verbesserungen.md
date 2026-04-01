# Datenmodell-Verbesserungen - DIN 18599 JSON Schema v2.1

> **Datum:** 2026-03-31  
> **Status:** Analyse abgeschlossen  
> **Priorität:** HOCH (vor Szenario-Switcher)

---

## 🎯 Ziel

Datenmodell normkonform und vollständig machen, bevor UI/UX-Features implementiert werden.

---

## ⚠️ Kritische Fehlende Felder

### 1. Fenster → Wand Zuordnung (KRITISCH)

**Problem:**
- Fenster werden nur über `orientation` der Wand zugeordnet
- Bei mehreren Wänden gleicher Orientierung nicht eindeutig
- Türen, Nischen fehlen komplett

**Lösung:**
```json
{
  "windows": [
    {
      "id": "window_sued_1",
      "parent_element_id": "wall_sued",  // ← NEU: Eindeutige Zuordnung
      "parent_element_type": "wall",     // ← NEU: Typ (wall/roof/door)
      "orientation": 180.0,
      "area": 6.0,
      // ... rest
    }
  ]
}
```

**Vorteile:**
- ✅ Eindeutige Zuordnung
- ✅ Mehrere Wände gleicher Orientierung möglich
- ✅ Türen/Nischen können auch abgezogen werden
- ✅ Hierarchie klar definiert

---

### 2. Solargewinne (WICHTIG für Bilanz)

**Fehlend:**
- `solar_absorption` (α) für Wände/Dächer
- `shading_factor_fs` für Fenster

**Lösung:**
```json
{
  "walls_external": [
    {
      "id": "wall_sued",
      "solar_absorption": 0.6,  // ← NEU: Absorptionsgrad (dunkel=0.9, hell=0.3)
      // ... rest
    }
  ],
  "windows": [
    {
      "id": "window_sued_1",
      "shading_factor_fs": 0.9,  // ← NEU: Verschattung (1.0=keine, 0.5=50%)
      // ... rest
    }
  ]
}
```

**Wichtigkeit:**
- Solargewinne über Wände (opak): ~5-10% der Gesamtgewinne
- Solargewinne über Fenster (transparent): ~40-60% der Gesamtgewinne
- **Ohne diese Werte ist die Bilanz unvollständig!**

---

### 3. Wärmebrücken-Typ (für Genauigkeit)

**Fehlend:**
- `thermal_bridge_type` (DEFAULT/REDUCED/DETAILED)

**Lösung:**
```json
{
  "walls_external": [
    {
      "id": "wall_sued",
      "thermal_bridge_delta_u": 0.15,
      "thermal_bridge_type": "DEFAULT",  // ← NEU: 0.10 W/(m²K) pauschal
      // oder "REDUCED" (0.05) oder "DETAILED" (individuell)
    }
  ]
}
```

---

### 4. Bodenplatte (für Fx-Faktor)

**Fehlend:**
- `perimeter` (Umfang P)
- `characteristic_dimension_b` (B' = A/0.5P)

**Lösung:**
```json
{
  "floors": [
    {
      "id": "floor_keller",
      "area": 120.0,
      "perimeter": 44.0,                    // ← NEU: Umfang (m)
      "characteristic_dimension_b": 5.45,   // ← NEU: B' = 120 / (0.5 * 44)
      "boundary_condition": "GROUND"
    }
  ]
}
```

**Wichtigkeit:**
- B' bestimmt Fx-Faktor (Temperaturkorrekturfaktor)
- Ohne B' kann Transmissionsverlust zu Erdreich nicht korrekt berechnet werden

---

## 🔄 Szenarien (Delta-Merge)

**Aktuell:**
```json
{
  "scenarios": [
    {
      "id": "sanierung_stufe1",
      "delta": {
        "input": {
          "envelope": {
            "walls_external": [
              { "id": "wall_sued", "u_value_undisturbed": 0.21 }
            ]
          }
        }
      }
    }
  ]
}
```

**Problem:**
- ❌ Keine `output` Daten im Szenario
- ❌ Keine Kosten/Aufwand
- ❌ Keine Maßnahmen-Beschreibung

**Lösung:**
```json
{
  "scenarios": [
    {
      "id": "sanierung_stufe1",
      "name": "Sanierung Stufe 1: WDVS + Fenster",
      "description": "...",
      "measures": [                          // ← NEU: Maßnahmen-Liste
        {
          "id": "m1",
          "type": "INSULATION_FACADE",
          "description": "WDVS 160mm EPS 035",
          "cost_estimate": 18000,
          "affected_elements": ["wall_sued", "wall_nord", "wall_ost", "wall_west"]
        },
        {
          "id": "m2",
          "type": "WINDOW_REPLACEMENT",
          "description": "Dreifachverglasung Ug=1.0",
          "cost_estimate": 8000,
          "affected_elements": ["window_sued_1", "window_nord_1"]
        }
      ],
      "delta": {
        "input": { /* ... */ }
      },
      "output": {                            // ← NEU: Berechnete Ergebnisse
        "energy_balance": {
          "final_energy_kwh_a": 12500,      // Vorher: 28500
          "primary_energy_kwh_a": 14000,    // Vorher: 32000
          "co2_emissions_kg_a": 2800        // Vorher: 6800
        },
        "indicators": {
          "efficiency_class": "C",          // Vorher: F
          "specific_primary_energy_kwh_m2a": 93.3
        },
        "savings": {                         // ← NEU: Einsparungen
          "final_energy_percent": 56.1,
          "primary_energy_percent": 56.3,
          "co2_percent": 58.8,
          "cost_annual_eur": 1600
        }
      }
    }
  ]
}
```

---

## 📋 Implementierungs-Reihenfolge

### Phase 1: Kritische Felder (JETZT)
1. ✅ `parent_element_id` für Fenster
2. ✅ `solar_absorption` für Wände/Dächer
3. ✅ `shading_factor_fs` für Fenster
4. ✅ Demo-JSON aktualisieren

### Phase 2: Erweiterte Felder (vor Szenario-Switcher)
5. ✅ `thermal_bridge_type`
6. ✅ `perimeter` + `characteristic_dimension_b` für Böden
7. ✅ Szenario `output` + `measures`

### Phase 3: Optional (später)
8. ⏳ `horizon_angle`, `overhang_angle` (detaillierte Verschattung)
9. ⏳ `layer_structure_ref` (Schichtaufbau)
10. ⏳ Türen als separater Typ

---

## 🎯 Erfolgs-Kriterien

- [ ] Alle Pflichtfelder nach DIN V 18599 vorhanden
- [ ] Fenster-Zuordnung eindeutig (parent_element_id)
- [ ] Solargewinne berechenbar (solar_absorption, shading_factor)
- [ ] Szenarien mit Output-Daten
- [ ] Demo-JSON vollständig und normkonform

---

## 📚 Referenzen

- Leitfaden DIN V 18599 (2023), Kapitel 6 - Thermische Hüllfläche
- `/docs/PARAMETER_MATRIX.md` - Vollständige Feldliste
- `/sources/INDEX.md` - Quellen-Übersicht

---

**Nächster Schritt:** Demo-JSON aktualisieren mit kritischen Feldern
