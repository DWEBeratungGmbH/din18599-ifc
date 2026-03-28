# Registry Refactoring - Trennung von Norm-Semantik und Tabellenwerten

**Datum:** 28. März 2026  
**Anlass:** User-Feedback zur ersten Variablen-Registry  
**Problem:** Vermischung von statischer Symboldefinition und dynamischen Tabellenwerten

---

## 🎯 Kernproblem

Die ursprüngliche `din18599_variables.json` vermischte **zwei grundverschiedene Konzepte**:

| Konzept | Was es ist | Ändert sich? |
|---------|-----------|--------------|
| **Variable-Registry** | Symboldefinition: „θ bedeutet Temperatur, Einheit °C" | Nie (ist in der Norm definiert) |
| **Nutzungsprofil-Katalog** | Konkrete Tabellenwerte: „Büro → θ_h = 20°C, n_nutz = 0,5 1/h" | Bei jeder Normenrevision |

**Beispiel des Problems:**
```json
{
  "symbol": "theta_i_h_soll",
  "default_values": {"residential_efh": 20}  // ❌ Tabellenwert in Registry!
}
```

Wenn DIN 18599-10 einen Wert ändert, müsste die „Registry" angefasst werden, obwohl eine Registry eigentlich stabil sein sollte.

---

## ✅ Neue Architektur (3+1 Dateien)

### 1. `din18599_symbols.json` - Reines Glossar (STATISCH)

**Zweck:** Symboldefinitionen aus DIN 18599-10 Tabelle 1+2  
**Ändert sich:** Nur bei Normen-Revision  
**Inhalt:**
- Symbol (θ_i_h_soll)
- LaTeX (\theta_{i,h,soll})
- Namen (DE/EN)
- Einheit (°C)
- Datentyp (number)
- Kategorie (temperature)
- Scope (zone)
- DIN-Referenz (Teil, Tabelle)
- Verwendung (used_in)

**KEINE:**
- ❌ Tabellenwerte (default_values)
- ❌ Schema-Paths (schema_path)
- ❌ Implementierungsdetails

### 2. `din18599_nutzungsprofile.json` - Tabellenwerte (VERSIONIERT)

**Zweck:** Konkrete Werte aus DIN 18599-10 Tabelle 5-7  
**Ändert sich:** Bei jeder Normen-Revision  
**Struktur:**
```json
{
  "residential": {
    "EFH": {
      "parameters": {
        "theta_i_h_soll": {"value": 20, "unit": "°C"},
        "q_I": {"value": 45, "unit": "Wh/(m²·d)"}
      }
    }
  },
  "non_residential": {
    "01": {
      "name_de": "Einzelbüro",
      "parameters": {
        "theta_i_h_soll": {"value": 20, "unit": "°C"}
      }
    }
  }
}
```

### 3. `din18599_interface_map.json` - Datenflüsse (STATISCH)

**Zweck:** Tabelle 3+4 - Welche Symbole fließen zwischen welchen DIN-Teilen  
**Ändert sich:** Selten  
**Struktur:**
```json
{
  "outputs": [
    {
      "symbol": "theta_i_h_soll",
      "source_part": "DIN/TS 18599-10",
      "target_parts": ["DIN/TS 18599-2", "DIN/TS 18599-5"]
    }
  ]
}
```

### 4. `schema_mapping.json` - Implementierungsdetail (NICHT Teil der Norm)

**Zweck:** Mapping von Symbolen zu JSON Schema Paths  
**Ändert sich:** Bei Schema-Änderungen  
**Struktur:**
```json
{
  "mappings": {
    "zone_parameters": {
      "theta_i_h_soll": "zones[].usage_profile.parameters_din.theta_i_h_soll"
    }
  }
}
```

---

## 🔧 Weitere Verbesserungen

### 1. Indizes mit Typ-Klassifikation

**Vorher:**
```json
{"index_symbol": "h", "name_de": "Heizung"}
```

**Nachher:**
```json
{"index_symbol": "h", "name_de": "Heizung", "type": "system"}
```

**Typen:**
- `location` (i, e, I)
- `system` (h, c, V)
- `state` (soll, nutz, NA)
- `time` (a, d)
- `energy_type` (el)

**Vorteil:** Automatische Validierung ob `θ_i,h,soll` semantisch valide ist.

### 2. Interface-Variablen ohne Duplikation

**Vorher:** Symbol-Daten in `symbols` UND `interface_variables` wiederholt  
**Nachher:** `interface_map` referenziert nur Symbol-Namen, keine Duplikation

---

## 📊 Vergleich Alt vs. Neu

| Aspekt | Alt (1 Datei) | Neu (3+1 Dateien) |
|--------|---------------|-------------------|
| **Norm-Semantik** | ✅ Enthalten | ✅ `symbols.json` |
| **Tabellenwerte** | ❌ Vermischt | ✅ `nutzungsprofile.json` |
| **Datenflüsse** | ✅ Enthalten | ✅ `interface_map.json` |
| **Schema-Mapping** | ❌ Vermischt | ✅ `schema_mapping.json` (separat) |
| **Wartbarkeit** | ❌ Schwierig | ✅ Klar getrennt |
| **Versionierung** | ❌ Alles zusammen | ✅ Nur Nutzungsprofile versioniert |

---

## 🎯 Use Cases

### 1. Symboldefinition nachschlagen
```python
symbols = load_json("din18599_symbols.json")
theta = symbols["symbols"].find(s => s.symbol == "theta_i_h_soll")
print(f"{theta.symbol_latex} = {theta.name_de} [{theta.unit}]")
# Output: \theta_{i,h,soll} = Raum-Solltemperatur Heizung [°C]
```

### 2. Nutzungsprofil-Werte abrufen
```python
profiles = load_json("din18599_nutzungsprofile.json")
efh = profiles["residential"]["EFH"]
theta_value = efh["parameters"]["theta_i_h_soll"]["value"]
print(f"EFH: θ_i,h,soll = {theta_value}°C")
# Output: EFH: θ_i,h,soll = 20°C
```

### 3. Validierung (Required-Check)
```python
symbols = load_json("din18599_symbols.json")
required_zone_params = [s for s in symbols["symbols"] 
                        if s.scope == "zone" and s.required]
# Prüfe ob alle in zone_data vorhanden
```

### 4. Schema-Mapping (Implementierung)
```python
mapping = load_json("schema_mapping.json")
path = mapping["mappings"]["zone_parameters"]["theta_i_h_soll"]
# "zones[].usage_profile.parameters_din.theta_i_h_soll"
```

---

## ✅ Vorteile der neuen Architektur

1. **Klare Trennung:** Norm-Semantik ≠ Tabellenwerte ≠ Implementierung
2. **Wartbarkeit:** Normen-Revision betrifft nur `nutzungsprofile.json`
3. **Wiederverwendbarkeit:** `symbols.json` kann von jeder Software genutzt werden
4. **Versionierung:** Nur Tabellenwerte müssen versioniert werden
5. **Entkopplung:** Schema-Änderungen betreffen nur `schema_mapping.json`

---

## 📋 Nächste Schritte

1. ✅ Alte `din18599_variables.json` löschen
2. ✅ Neue 3+1 Dateien erstellen
3. ⏳ SQL-Seeds anpassen (3 separate INSERT-Statements)
4. ⏳ 43 NWG-Profile in `nutzungsprofile.json` ergänzen
5. ⏳ Validator-Logik implementieren (nutzt alle 4 Dateien)

---

**Status:** ✅ Refactoring abgeschlossen  
**Commit:** Folgt nach diesem Dokument
