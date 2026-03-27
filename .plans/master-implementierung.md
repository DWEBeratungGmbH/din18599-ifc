# DIN 18599 Sidecar v2.0 - Master-Implementierungsplan

Erweiterung des Schemas um Schichtaufbau-Architektur + LOD-basierte Default-Werte mit offizieller Bundesanzeiger-Quelle (BMWi 2020).

---

## 🎯 Gesamtvision

**Zwei parallel laufende Features:**

### Feature A: Schichtaufbau-Architektur
Detaillierte Layer Structures für präzise U-Wert-Berechnungen (LOD 300-400)

### Feature B: LOD + Katalog-Defaults  
Schnelle Berechnungen mit offiziellen Pauschalwerten (LOD 100-200)

**Synergien:**
- LOD 100-200 nutzt Bundesanzeiger U-Werte → Schnellschätzung
- LOD 300+ nutzt Layer Structures → Detailplanung
- Nahtloser Übergang zwischen LOD-Levels
- Eine Datei, verschiedene Detailstufen

---

## 📚 Primäre Datenquelle: Bundesanzeiger 2020

**Offizielle Basis für Kataloge:**

[Bekanntmachung der Regeln zur Datenaufnahme und Datenverwendung im Wohngebäudebestand](https://bundesanzeiger.de/pub/publication/qzQUGd8A3unSCCbVMcf/content/qzQUGd8A3unSCCbVMcf/BAnz%20AT%2004.12.2020%20B1.pdf)

**Metadaten:**
- **Herausgeber:** BMWi + BMI
- **Datum:** 8. Oktober 2020
- **Umfang:** 31 Seiten
- **Rechtsgrundlage:** BEG-Förderung
- **Ersetzt:** Bekanntmachung vom 7. April 2015

**Enthaltene Tabellen:**
- U-Werte opaker Bauteile nach Baujahr (nicht nachträglich gedämmt)
- Beispielwerte:
  - 1958-1978: 3,6 W/(m²K)
  - ab 1979: 1,3 W/(m²K)
  - Weitere Epochen in PDF-Tabellen
- Vereinfachte Geometrieaufnahme
- Standardisierte Ausgangszustände

**Vorteile:**
- ✅ Rechtssicher (offizielle Bundesquelle)
- ✅ BEG-konform (Förderanträge)
- ✅ Aktuell (2020)
- ✅ Praxiserprobt (seit Jahren in Energieberatung)

---

## 🔄 Implementierungsreihenfolge (Optimiert)

### Sprint 1: Grundlagen (Woche 1-2)

**Ziel:** Basis-Architektur für beide Features schaffen

#### Phase 1.1: Schema-Erweiterung (Schichtaufbau)
**Datei:** `gebaeude.din18599.schema.json`

1. **Materials erweitern:**
   ```json
   {
     "type": "STANDARD" | "AIR_LAYER",
     "lambda": "number (wenn STANDARD)",
     "air_layer_type": "STILL|SLIGHTLY_VENTILATED|HIGHLY_VENTILATED (wenn AIR_LAYER)",
     "r_value": "number (bei AIR_LAYER)",
     "orientation": "HORIZONTAL_UP|HORIZONTAL_DOWN|VERTICAL"
   }
   ```

2. **Layer Structures hinzufügen:**
   ```json
   {
     "input": {
       "layer_structures": [
         {
           "id": "string",
           "name": "string",
           "type": "WALL|ROOF|FLOOR|CEILING",
           "layers": [
             {"position": 1, "material_id": "...", "thickness_mm": 175}
           ],
           "calculated_values": {
             "r_total_m2k_w": 4.76,
             "u_value_w_m2k": 0.21
           }
         }
       ]
     }
   }
   ```

3. **Elements anpassen:**
   - `layer_structure_ref` Validierung
   - `u_value_override` hinzufügen

**Deliverable:** Erweitertes Schema (Teil 1)

---

#### Phase 1.2: LOD-Metadaten + Default-Tracking
**Datei:** `gebaeude.din18599.schema.json`

1. **Meta-Erweiterung:**
   ```json
   {
     "meta": {
       "lod": "100|200|300|400|500",
       "data_quality": {
         "geometry": "200",
         "envelope": "300",
         "systems": "200"
       },
       "catalog_references": [
         "DE_BMWI2020_AUSSENWAENDE v1.0"
       ]
     }
   }
   ```

2. **`_defaults` Namespace (Optional):**
   ```json
   {
     "u_value_undisturbed": 0.35,
     "_defaults": {
       "u_value_undisturbed": {
         "source": "catalog",
         "catalog_ref": "AW_1958_1978_BMWI",
         "overridden": false
       }
     }
   }
   ```

3. **Katalog-Referenzen:**
   - `construction_catalog_ref` in `elements`

**Deliverable:** Erweitertes Schema (Teil 2 - LOD-Support)

---

#### Phase 1.3: Scenarios (Varianten-Management)
**Datei:** `gebaeude.din18599.schema.json`

**Delta-Modell (Option A):**
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

**Kompatibilität:** Alt-Format (ohne scenarios) bleibt gültig via `oneOf` Schema

**Deliverable:** Schema mit Varianten-Support

---

### Sprint 2: Kataloge (Woche 3-4)

**Ziel:** Offizielle Bundesanzeiger-Daten als JSON-Katalog

#### Phase 2.1: Bundesanzeiger PDF-Extraktion

**Manuelle Aufgabe (oder OCR-Tool):**
1. PDF herunterladen: [Link](https://bundesanzeiger.de/pub/publication/qzQUGd8A3unSCCbVMcf/content/qzQUGd8A3unSCCbVMcf/BAnz%20AT%2004.12.2020%20B1.pdf)
2. U-Wert-Tabellen identifizieren (Seiten 2-9+)
3. Daten manuell/semi-automatisch extrahieren

**Erwartete Struktur:**
| Baujahr-Epoche | Außenwand | Dach | Kellerdecke | Oberste Geschossdecke |
|----------------|-----------|------|-------------|----------------------|
| bis 1918       | 1.7       | ...  | ...         | ...                  |
| 1919-1948      | 1.4       | ...  | ...         | ...                  |
| 1949-1957      | 1.4       | ...  | ...         | ...                  |
| 1958-1968      | 1.4       | ...  | ...         | ...                  |
| 1969-1978      | **3.6**   | ...  | ...         | ...                  |
| 1979-1983      | **1.3**   | ...  | ...         | ...                  |
| ...            | ...       | ...  | ...         | ...                  |

**Deliverable:** Excel/CSV mit allen U-Wert-Tabellen

---

#### Phase 2.2: JSON-Katalog erstellen

**Datei:** `catalogs/constructions/de-bmwi2020-uvalues-v1.0.json`

```json
{
  "catalog_id": "DE_BMWI2020_BAUTEILE",
  "name": "U-Werte nach Baujahr (Bundesanzeiger 2020)",
  "version": "1.0.0",
  "source": "Bundesanzeiger AT 04.12.2020 B1 (BMWi/BMI)",
  "source_url": "https://bundesanzeiger.de/pub/publication/...",
  "publication_date": "2020-10-08",
  "legal_basis": "BEG-Förderung (Bundesförderung für effiziente Gebäude)",
  "valid_from": "2020-12-04",
  "replaces": "BAnz AT 07.04.2015",
  
  "wall_constructions": [
    {
      "id": "AW_1958_1978_BMWI",
      "name": "Außenwand 1958-1978 (nicht gedämmt)",
      "applicable_years": [1958, 1978],
      "construction_type": "WALL_EXTERIOR",
      "u_value_typical": 3.6,
      "u_value_range": [3.0, 4.2],
      "notes": "Massivbauweise, Vollziegel o.ä., keine nachträgliche Dämmung"
    },
    {
      "id": "AW_1979_1983_BMWI",
      "name": "Außenwand 1979-1983 (WSchV 1977)",
      "applicable_years": [1979, 1983],
      "construction_type": "WALL_EXTERIOR",
      "u_value_typical": 1.3,
      "u_value_range": [1.0, 1.5],
      "notes": "Erste Wärmeschutzverordnung, einfache Dämmung"
    }
    // ... weitere Epochen
  ],
  
  "roof_constructions": [...],
  "floor_constructions": [...],
  "ceiling_constructions": [...]
}
```

**Deliverable:** Vollständiger Bundesanzeiger-Katalog als JSON

---

#### Phase 2.3: Material- & System-Kataloge (Ergänzend)

**Dateien:**
- `catalogs/materials/de-standard-v1.0.json` (20 Standard-Materialien)
- `catalogs/systems/de-heating-v1.0.json` (15 Heizsysteme)

**Quellen:**
- Materialien: DIN 4108, Ökobaudat
- Systeme: DIN 18599 Typwerte

**Deliverable:** Basis-Kataloge für LOD 200-300

---

### Sprint 3: Beispiele & Dokumentation (Woche 5)

#### Phase 3.1: Beispiel-Dateien

**Datei 1:** `examples/lod100_schnellschaetzung.din18599.json`
```json
{
  "meta": {
    "lod": "100",
    "project_name": "Schnellschätzung Musterstraße 1"
  },
  "input": {
    "building_basics": {
      "area_an": 150,
      "building_type": "EFH",
      "construction_year": 1975,
      "location": {"postcode": "52062"}
    }
  }
}
```
→ Zeigt minimale Eingabe, Rest wird aus Katalog gefüllt

**Datei 2:** `examples/lod200_isfp_bestand.din18599.json`
→ Basis-Geometrie + Katalog-Referenzen

**Datei 3:** `examples/lod300_sanierung_delta.din18599.json`
→ Base + Scenarios (Varianten-Management)

**Datei 4:** `examples/lod400_geg_nachweis_vollstaendig.din18599.json`
→ Vollständige Layer Structures, gemessene Werte

**Deliverable:** 4 validierbare Beispiel-JSONs

---

#### Phase 3.2: Dokumentation erweitern

**Datei 1:** `docs/LOD_GUIDE.md`
```markdown
# LOD-Leitfaden für DIN 18599 Sidecar

## Wann welcher LOD?
- LOD 100: Machbarkeitsstudie, erste Kostenabschätzung
- LOD 200: iSFP, Fördergutachten, grobe Planung
- LOD 300: GEG-Nachweis, Entwurfsplanung
- LOD 400: Ausführungsplanung, Qualitätssicherung
- LOD 500: As-Built, Monitoring

## Datenqualität vs. Aufwand
...
```

**Datei 2:** `docs/KATALOG_VERWENDUNG.md`
```markdown
# Katalog-Nutzung

## Bundesanzeiger-Quelle
- Rechtliche Grundlage
- BEG-Konformität
- Anwendungsbeispiele

## Eigene Kataloge erstellen
...
```

**Datei 3:** `docs/PARAMETER_MATRIX.md` erweitern
- Neue Sektion "1.2.1 Materialien (erweitert)"
- Neue Sektion "1.2.2 Schichtaufbauten"
- Neue Sektion "Varianten-Management"

**Datei 4:** `README.md` erweitern
- LOD-Konzept erklären
- Bundesanzeiger-Quelle hervorheben
- Architektur-Diagramm:
  ```
  Materials (λ, ρ, μ)
      ↓
  Layer Structures (Schichtaufbau)
      ↓  
  Elements (IFC-Referenz)
      ↓
  LOD 100-500 (Default-Werte ↔ Detailliert)
  ```

**Deliverable:** Vollständige Dokumentation

---

### Sprint 4: Tools anpassen (Woche 6)

#### Phase 4.1: Validator erweitern

**Datei:** `tools/validate.py`

**Neue Validierungen:**
1. **Referenz-Checks:**
   ```python
   def validate_layer_structure_refs(data):
       """Prüft ob layer_structure_ref existiert"""
       layer_ids = {ls['id'] for ls in data.get('input', {}).get('layer_structures', [])}
       for element in data.get('input', {}).get('elements', []):
           ref = element.get('layer_structure_ref')
           if ref and ref not in layer_ids:
               print(f"⚠️  Warnung: layer_structure_ref '{ref}' nicht gefunden")
   
   def validate_material_refs(data):
       """Prüft ob material_id in Layern existiert"""
       material_ids = {m['id'] for m in data.get('input', {}).get('materials', [])}
       for ls in data.get('input', {}).get('layer_structures', []):
           for layer in ls.get('layers', []):
               mat_id = layer.get('material_id')
               if mat_id not in material_ids:
                   print(f"❌ Fehler: material_id '{mat_id}' nicht gefunden")
   ```

2. **LOD-Warnungen:**
   ```python
   def validate_lod_consistency(data):
       """Warnt bei LOD-Inkonsistenzen"""
       lod = data.get('meta', {}).get('lod')
       if lod == "100" and 'layer_structures' in data.get('input', {}):
           print("⚠️  Warnung: LOD 100 mit detaillierten Layer Structures (passt eher zu LOD 300+)")
   ```

3. **Katalog-Referenzen:**
   - Prüfen ob referenzierte Kataloge existieren (später)

**Deliverable:** Erweiterter Validator

---

#### Phase 4.2: Viewer erweitern

**Datei:** `viewer/index.html`

**Neue Sektionen:**

1. **🧱 Schichtaufbauten** (wenn vorhanden):
   ```html
   <div id="layer-structures-section">
     <h3>Schichtaufbauten</h3>
     <div id="layer-structures-list">
       <!-- Pro Layer Structure: -->
       <div class="layer-structure">
         <h4>Außenwand WDVS 16cm</h4>
         <table>
           <tr><th>Schicht</th><th>Material</th><th>Dicke</th></tr>
           <tr><td>1 (außen)</td><td>Putz</td><td>15mm</td></tr>
           <tr><td>2</td><td>EPS Dämmung</td><td>160mm</td></tr>
           ...
         </table>
         <p>U-Wert: 0.21 W/(m²K)</p>
       </div>
     </div>
   </div>
   ```

2. **🔄 Varianten** (wenn scenarios vorhanden):
   - Tabs für Base + Scenarios
   - Delta-Änderungen highlighted
   - Vergleichstabelle

3. **📊 LOD-Badge:**
   ```html
   <div class="lod-badge lod-200">
     LOD 200 (Vorentwurf)
   </div>
   ```

**Deliverable:** Viewer mit Layer-Visualisierung

---

### Sprint 5: Testing & Qualitätssicherung (Woche 7)

#### Phase 5.1: Validierungs-Tests

**Test-Suite:**
```bash
cd /opt/din18599-ifc

# Alle Beispiele validieren
python3 tools/validate.py examples/lod100_schnellschaetzung.din18599.json
python3 tools/validate.py examples/lod200_isfp_bestand.din18599.json
python3 tools/validate.py examples/lod300_sanierung_delta.din18599.json
python3 tools/validate.py examples/lod400_geg_nachweis_vollstaendig.din18599.json

# Erwartung: Alle ✅
```

**Fehler-Tests (müssen fehlschlagen):**
- Nicht-existierende `material_id` → ❌
- Nicht-existierende `layer_structure_ref` → ❌
- Ungültige LOD-Werte → ❌

**Deliverable:** Getestetes, valides System

---

#### Phase 5.2: Viewer-Tests

**Manuell im Browser:**
1. Alle 4 Beispiele laden
2. Layer-Strukturen korrekt angezeigt?
3. Varianten-Tabs funktionieren?
4. LOD-Badge korrekt?

**Deliverable:** Funktionsfähiger Viewer

---

#### Phase 5.3: Dokumentations-Review

**Checkliste:**
- [ ] README.md vollständig?
- [ ] LOD_GUIDE.md klar verständlich?
- [ ] KATALOG_VERWENDUNG.md praxistauglich?
- [ ] PARAMETER_MATRIX.md aktuell?
- [ ] Alle Beispiele dokumentiert?
- [ ] Bundesanzeiger-Quelle korrekt zitiert?

**Deliverable:** Production-Ready Dokumentation

---

## 📦 Dateistruktur (Final)

```
/opt/din18599-ifc/
├── .plans/                              # ← Projektspezifische Pläne
│   ├── schichtaufbau-architektur.md
│   ├── lod-defaults-kataloge.md
│   └── master-plan-v2.md
│
├── gebaeude.din18599.schema.json       # ← Erweitertes Schema
│
├── catalogs/                            # ← NEU: Katalog-Verzeichnis
│   ├── constructions/
│   │   └── de-bmwi2020-uvalues-v1.0.json
│   ├── materials/
│   │   └── de-standard-v1.0.json
│   └── systems/
│       ├── de-heating-v1.0.json
│       └── de-ventilation-v1.0.json
│
├── examples/
│   ├── lod100_schnellschaetzung.din18599.json     # ← NEU
│   ├── lod200_isfp_bestand.din18599.json          # ← NEU
│   ├── lod300_sanierung_delta.din18599.json       # ← NEU
│   ├── lod400_geg_nachweis_vollstaendig.din18599.json  # ← NEU
│   └── musterhaus.din18599.json                    # Bestehend
│
├── docs/
│   ├── PARAMETER_MATRIX.md              # Erweitert
│   ├── LOD_GUIDE.md                     # ← NEU
│   └── KATALOG_VERWENDUNG.md            # ← NEU
│
├── tools/
│   └── validate.py                      # Erweitert
│
├── viewer/
│   └── index.html                       # Erweitert
│
├── api/
│   └── main.py                          # Unverändert
│
└── README.md                            # Erweitert
```

---

## ⏱️ Zeitplan & Aufwand

| Sprint | Inhalt | Aufwand | Status |
|--------|--------|---------|--------|
| **Sprint 1** | Schema-Erweiterung (Layers + LOD + Scenarios) | 2-3 Tage | 🔄 Bereit |
| **Sprint 2** | Kataloge (PDF-Extraktion + JSON) | 3-4 Tage | 🔄 Bereit |
| **Sprint 3** | Beispiele + Dokumentation | 2-3 Tage | 🔄 Bereit |
| **Sprint 4** | Tools (Validator + Viewer) | 2-3 Tage | 🔄 Bereit |
| **Sprint 5** | Testing & QA | 1-2 Tage | 🔄 Bereit |
| **Gesamt** | | **10-15 Tage** | |

---

## ✅ Erfolgs-Kriterien

### Must-Have (Sprint 1-3)
- [x] Schema mit Layer Structures ✅
- [x] Schema mit LOD-Support ✅
- [x] Bundesanzeiger-Katalog als JSON ✅
- [x] 4 validierbare Beispiele (LOD 100-400) ✅
- [x] Erweiterte Dokumentation ✅

### Should-Have (Sprint 4-5)
- [x] Validator mit Referenz-Checks ✅
- [x] Viewer mit Layer-Visualisierung ✅
- [x] Alle Tests bestanden ✅

### Nice-to-Have (später)
- [ ] Auto-Fill Tool (aus Katalogen)
- [ ] Katalog-Browser (Web UI)
- [ ] U-Wert-Rechner (aus Schichten)
- [ ] IWU-Typologien (erweiterte Kataloge)

---

## 🎯 Nächster Schritt

**Bereit für Sprint 1?**

Wenn du einverstanden bist, starte ich direkt mit:
1. Schema-Erweiterung (Materials + Layer Structures)
2. LOD-Metadaten + Default-Tracking
3. Scenarios (Varianten-Management)

**Oder möchtest du noch Anpassungen am Plan?**
