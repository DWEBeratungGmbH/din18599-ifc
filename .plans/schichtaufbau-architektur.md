# Schichtaufbau-Architektur für DIN 18599 Sidecar - Implementierungsplan

Erweiterung des Schemas um vollständige Schichtaufbau-Struktur mit Materialien, Layer-Architektur, Luftschichten (EN ISO 6946) und Varianten-Management (Delta-Modell).

---

## 🎯 Architektur-Entscheidungen (FINAL)

### ✅ U-Wert Berechnung: Hybrid (Option C)
- **`u_value_calculated`**: Aus Schichten berechnet (transparent, validierbar)
- **`u_value_override`**: Optionale manuelle Eingabe (für Messwerte, vereinfachte Eingabe)
- **Wärmebrücken**: Separat via `thermal_bridge_delta_u` (wie bisher)

### ✅ Varianten-Management: Delta-Modell (Option A)
```json
{
  "base": {
    "meta": {...},
    "input": {...}  // IST-Zustand
  },
  "scenarios": [
    {
      "id": "SCENARIO-01",
      "name": "Sanierung WDVS + Fenster",
      "delta": {
        "elements": [...],
        "layer_structures": [...],
        "windows": [...]
      }
    }
  ]
}
```
- **Basis:** Immer der IST-Zustand
- **Export:** Später Tool `tools/export_variant.py` (mergt delta in vollständige Datei)

### ✅ Luftschichten: Material mit Klassifizierung (EN ISO 6946)
```json
{
  "id": "MAT-AIR-01",
  "name": "Luftschicht 5cm ruhend",
  "type": "AIR_LAYER",
  "air_layer_type": "STILL",  // STILL, SLIGHTLY_VENTILATED, HIGHLY_VENTILATED
  "thickness_mm": 50,
  "r_value": 0.18,  // Manuell aus EN ISO 6946 Tabelle
  "orientation": "VERTICAL"  // HORIZONTAL_UP, HORIZONTAL_DOWN, VERTICAL
}
```

**Klassifizierung (EN ISO 6946):**
- **Ruhend (STILL)**: λ ≈ 0.0262 W/mK, volle R-Werte aus Norm-Tabelle
- **Schwach belüftet (SLIGHTLY_VENTILATED)**: R_Wert = 50% von ruhend
- **Stark belüftet (HIGHLY_VENTILATED)**: R_Wert = 0 (kein Dämmwert)

**Keine Berechnungslogik implementieren** - nur Datenstruktur für zukünftige Logik vorbereiten.

### ✅ Übergangswiderstände: Fest im Code (später konfigurierbar)
- R_se = 0.04 m²K/W (außen)
- R_si = 0.13 m²K/W (innen Wand), 0.10 m²K/W (Decke nach oben)

---

## 📐 Datenmodell-Erweiterungen

### 1. Materials (Erweitert)
```json
{
  "id": "string",
  "name": "string",
  "type": "STANDARD" | "AIR_LAYER",  // NEU
  
  // Standard-Material (type=STANDARD):
  "lambda": "number",
  "density": "number",
  "specific_heat": "number (optional)",
  "vapor_resistance_factor": "number (optional, μ-Wert)",
  "oekobau_uuid": "string (optional)",
  
  // Luftschicht (type=AIR_LAYER):
  "air_layer_type": "STILL" | "SLIGHTLY_VENTILATED" | "HIGHLY_VENTILATED",
  "thickness_mm": "number",
  "r_value": "number (manuell aus EN ISO 6946)",
  "orientation": "HORIZONTAL_UP" | "HORIZONTAL_DOWN" | "VERTICAL"
}
```

### 2. Layer Structures (NEU)
```json
{
  "id": "string",
  "name": "string",
  "type": "WALL" | "ROOF" | "FLOOR" | "CEILING",
  "description": "string (optional)",
  
  "layers": [
    {
      "position": "integer (1=außen)",
      "material_id": "string (ref zu materials[].id)",
      "thickness_mm": "number"
    }
  ],
  
  "calculated_values": {
    "r_total_m2k_w": "number",
    "u_value_w_m2k": "number",
    "sd_total_m": "number (Dampfdiffusion, optional)"
  },
  
  "surface_properties": {
    "exterior": {
      "solar_absorption": "number (0-1)",
      "emissivity": "number (0-1, optional)"
    }
  }
}
```

### 3. Scenarios (NEU, Top-Level)
```json
{
  "base": {
    "meta": {...},
    "input": {...}
  },
  "scenarios": [
    {
      "id": "string",
      "name": "string",
      "description": "string (optional)",
      "created_date": "ISO 8601",
      "delta": {
        "elements": [...],
        "windows": [...],
        "layer_structures": [...],
        "materials": [...],
        "systems": [...]
      }
    }
  ]
}
```

**Wichtig:** Alte Struktur (ohne scenarios) bleibt kompatibel!

---

## 🔄 Implementierungsschritte

### Phase 0: Plan-Migration 📁

**Ziel:** Projektspezifischen Plan-Ordner erstellen

1. **Ordner erstellen:**
   ```bash
   mkdir -p /opt/din18599-ifc/.plans
   ```

2. **Bestehende Pläne migrieren:**
   - `schichtaufbau-implementierung-cc49bf.md` → `.plans/schichtaufbau-implementierung.md`
   - `layer-architecture-schema-cc49bf.md` → `.plans/architektur-entscheidungen.md`

3. **.gitignore prüfen:**
   - `.plans/` NICHT ignorieren (soll committet werden)

**Deliverable:** Projektspezifischer Plan-Ordner eingerichtet

---

### Phase 1: Schema-Erweiterung ✏️

**Datei:** `gebaeude.din18599.schema.json`

1. **Materials erweitern:**
   - `type` Enum hinzufügen: `["STANDARD", "AIR_LAYER"]`
   - Conditional Schema: AIR_LAYER vs. STANDARD Properties
   - Neue Felder: `air_layer_type`, `orientation`, `r_value`, `vapor_resistance_factor`, `specific_heat`

2. **Layer Structures hinzufügen:**
   - Neues Top-Level Property `input.layer_structures[]`
   - Schema wie oben definiert
   - Validierung: `material_id` muss existieren

3. **Scenarios hinzufügen:**
   - Neue Root-Struktur mit `base` + `scenarios`
   - Alt-Format (direkt meta/input) bleibt gültig
   - `oneOf` Schema für Kompatibilität

4. **Elements anpassen:**
   - Validierung: `layer_structure_ref` muss existieren (wenn angegeben)
   - `u_value_override` hinzufügen (optional)

**Deliverable:** Erweitertes Schema mit allen neuen Strukturen

---

### Phase 2: Beispiel-Daten ✏️

**Datei:** `examples/musterhaus_vollstaendig.din18599.json`

**Neue vollständige Beispieldatei mit:**

1. **3 Material-Typen:**
   - Standard: Mauerwerk, Dämmung (bereits vorhanden)
   - Luftschicht ruhend (STILL, 5cm, vertikal)
   - Luftschicht schwach belüftet (SLIGHTLY_VENTILATED, hinterlüftete Fassade)

2. **3 Schichtaufbauten:**
   - **Außenwand:** Putz + Mauerwerk + Dämmung + Putz
   - **Dachaufbau:** Ziegel + Lattung + Luftschicht + Dämmung + OSB
   - **Kellerdecke:** Beton + Dämmung

3. **Elements mit layer_structure_ref:**
   - Verknüpfung zu den neuen Layer Structures

4. **Berechnung dokumentieren:**
   - Kommentar mit Rechenweg für U-Werte

**Deliverable:** Validierbare Beispiel-JSON mit allen Features

---

### Phase 3: Varianten-Beispiel ✏️

**Datei:** `examples/sanierung_delta_modell.din18599.json`

**Zeigt Varianten-Management:**

```json
{
  "base": {
    "meta": {
      "project_name": "Sanierung Musterstraße 1",
      "ifc_file_ref": "musterhaus.ifc",
      ...
    },
    "input": {
      // IST-Zustand (Bestand)
    }
  },
  "scenarios": [
    {
      "id": "SCENARIO-FASSADE",
      "name": "Dämmung WDVS 16cm",
      "description": "Außenwanddämmung mit WDVS EPS 160mm",
      "delta": {
        "layer_structures": [
          {
            "id": "LAYER-AW-01-SANIERT",
            "name": "Außenwand WDVS 16cm",
            "layers": [...]
          }
        ],
        "elements": [
          {
            "ifc_guid": "3xS3BCk291NvV5o6281",
            "layer_structure_ref": "LAYER-AW-01-SANIERT"  // Überschreibt Bestand
          }
        ]
      }
    },
    {
      "id": "SCENARIO-KOMPLETT",
      "name": "Vollsanierung (WDVS + Fenster + Dach)",
      "delta": {
        "layer_structures": [...],
        "elements": [...],
        "windows": [...]
      }
    }
  ]
}
```

**Deliverable:** Praxis-nahes Varianten-Beispiel

---

### Phase 4: Dokumentation 📝

#### 4.1 Parameter-Matrix erweitern

**Datei:** `docs/PARAMETER_MATRIX.md`

**Neue Sektionen:**

1. **1.2.1 Materialien (erweitert):**
   - Tabelle mit allen Material-Properties
   - Trennung: Standard vs. Luftschicht
   - EN ISO 6946 Referenzen

2. **1.2.2 Schichtaufbauten (NEU):**
   - `layer_structures[]` komplett dokumentieren
   - Berechnungsbeispiel U-Wert
   - DIN EN ISO 6946 Verweise

3. **Varianten-Management (NEU):**
   - Delta-Modell erklären
   - Merge-Logik beschreiben
   - Export-Workflow

#### 4.2 README erweitern

**Datei:** `README.md`

**Anpassungen:**

1. **Architektur-Diagramm:**
```
Materials (λ, ρ, μ)
    ↓
Layer Structures (Schichtaufbau)
    ↓  
Elements (IFC-Referenz)
```

2. **Varianten-Workflow:**
   - IST-Zustand als Base
   - Szenarien als Delta
   - Export-Funktion (geplant)

3. **Luftschichten-Hinweis:**
   - EN ISO 6946 Klassifizierung
   - Verwendung in Praxis

**Deliverable:** Vollständige Dokumentation

---

### Phase 5: Validator erweitern 🔧

**Datei:** `tools/validate.py`

**Neue Validierungen:**

1. **Referenz-Checks:**
   ```python
   def validate_references(data):
       # Check: layer_structure_ref exists
       # Check: material_id exists
       # Check: delta scenarios only modify existing items
   ```

2. **Warnungen (nicht Fehler):**
   - U-Wert weicht von Berechnung ab (>10%)
   - Luftschicht > 30cm (unüblich)
   - Stark belüftete Luftschicht mit R-Wert > 0

3. **Scenarios-Support:**
   - Base + Scenarios Format validieren
   - Delta-Struktur prüfen

**Deliverable:** Erweiterter Validator mit Referenz-Checks

---

### Phase 6: Viewer erweitern 🖥️

**Datei:** `viewer/index.html`

**Neue Sektionen:**

1. **🧱 Schichtaufbauten:**
   - Liste aller Layer Structures
   - Pro Aufbau: Material-Stack mit Dicken visualisieren
   - U-Wert calculated + override anzeigen

2. **🔄 Varianten (falls vorhanden):**
   - Tabs für Base + Scenarios
   - Delta-Änderungen highlighted
   - Vergleichstabelle (Base vs. Scenario)

3. **📊 Material-Übersicht:**
   - Gruppierung: Standard vs. Luftschichten
   - Properties anzeigen

**Deliverable:** Viewer mit Layer-Visualisierung

---

### Phase 7: Testing 🧪

1. **Validierungs-Tests:**
   ```bash
   python3 tools/validate.py examples/musterhaus_vollstaendig.din18599.json
   python3 tools/validate.py examples/sanierung_delta_modell.din18599.json
   ```

2. **Referenz-Fehler provozieren:**
   - Nicht-existierende `material_id` → Muss fehlschlagen
   - Nicht-existierende `layer_structure_ref` → Muss fehlschlagen

3. **Viewer-Test:**
   - Beide Beispiele im Viewer laden
   - Layer-Strukturen korrekt angezeigt?
   - Varianten-Tabs funktionieren?

**Deliverable:** Getestete, valide Implementierung

---

## 📋 Dateien-Übersicht (was wird geändert/erstellt)

### Ändern:
- ✏️ `gebaeude.din18599.schema.json` (Materials, Layer Structures, Scenarios)
- ✏️ `docs/PARAMETER_MATRIX.md` (3 neue Sektionen)
- ✏️ `README.md` (Architektur-Diagramm, Varianten-Workflow)
- ✏️ `tools/validate.py` (Referenz-Checks, Scenarios-Support)
- ✏️ `viewer/index.html` (Layers + Varianten Sektionen)

### Neu erstellen:
- ✨ `examples/musterhaus_vollstaendig.din18599.json`
- ✨ `examples/sanierung_delta_modell.din18599.json`

### Später (nicht jetzt):
- 🔮 `tools/export_variant.py` (Delta → Vollständige Datei)
- 🔮 `tools/calculate_uvalue.py` (U-Wert aus Schichten berechnen)

---

## ⏱️ Zeitschätzung

- **Phase 1 (Schema):** 30 Min
- **Phase 2 (Beispiel vollständig):** 20 Min
- **Phase 3 (Varianten-Beispiel):** 15 Min
- **Phase 4 (Doku):** 25 Min
- **Phase 5 (Validator):** 20 Min
- **Phase 6 (Viewer):** 30 Min
- **Phase 7 (Testing):** 15 Min

**Gesamt:** ~2.5 Stunden

---

## ✅ Erfolgs-Kriterien

1. **Schema valide:** Alle Beispiele laufen durch Validator
2. **Referenzen funktionieren:** material_id, layer_structure_ref werden geprüft
3. **Varianten funktionieren:** Delta-Modell ist implementiert
4. **Luftschichten vollständig:** Alle 3 Typen (EN ISO 6946) im Schema
5. **Dokumentation vollständig:** Matrix + README erweitert
6. **Tools funktionieren:** Validator + Viewer zeigen neue Features

---

## 🚀 Nächster Schritt

**Bereit für Implementierung?**

Wenn du mit diesem Plan einverstanden bist, starte ich direkt mit **Phase 1 (Schema-Erweiterung)** und arbeite dann sequenziell durch alle Phasen.

**Änderungswünsche?** Sag Bescheid, dann passe ich den Plan an.
