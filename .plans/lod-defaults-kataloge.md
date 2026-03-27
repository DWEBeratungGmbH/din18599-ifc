# LOD-Konzept & Default-Werte für DIN 18599 Sidecar

Einführung eines BIM-inspirierten Level of Detail (LOD) Systems mit Katalog-Defaults und Formeln für schnelle Berechnungen in frühen Planungsphasen.

---

## 🎯 Zielbild

**Problem heute:**
- Schema erfordert viele detaillierte Eingaben
- Ohne vollständige Daten keine Berechnung möglich
- Frühe Planungsphasen (Vorentwurf) vs. Detail-Planung haben unterschiedliche Datenanforderungen

**Lösung: LOD-basiertes Datenmodell**
```
LOD 100 (Konzept)      → Minimale Eingaben, viele Defaults
    ↓
LOD 200 (Vorentwurf)   → Grobe Geometrie, Katalogwerte
    ↓
LOD 300 (Entwurf)      → Detaillierte Geometrie, pauschale U-Werte
    ↓
LOD 400 (Ausführung)   → Vollständige Schichten, gemessene Werte
    ↓
LOD 500 (As-Built)     → Reale Messwerte, Monitoring-Daten
```

**Use Cases:**
- ✅ Schnellschätzung mit 5 Eingaben (Fläche, Baujahr, Gebäudetyp)
- ✅ iSFP-Beratung mit vereinfachten Daten
- ✅ Detailplanung mit vollständigen Schichtaufbauten
- ✅ Monitoring mit Verbrauchsdaten

---

## 📐 LOD-Definitionen für DIN 18599

### LOD 100 - Konzept (Volumenstudie)
**Eingaben:** Minimal (5-10 Felder)
- Gebäudefläche (AN)
- Gebäudevolumen
- Baujahr oder Sanierungsstand
- Gebäudetyp (EFH, MFH, Büro, etc.)
- Standort (PLZ für Klimadaten)

**Defaults/Formeln:**
- U-Werte aus **Tabellenwerten** (DIN 4108 Beiblatt 2 nach Baujahr)
  - Vor 1977: U_Wand = 1.4 W/m²K
  - 1977-1995: U_Wand = 0.6 W/m²K
  - etc.
- Anlagentechnik: **Statistische Typwerte** nach Baujahr
  - Vor 1995: Gaskessel Standard (η = 0.85)
  - 2000-2010: Brennwertkessel (η = 0.95)
- Fensterfläche: **30% der Außenwandfläche** (Formel)
- Lüftung: Fensterlüftung (Default)

**Genauigkeit:** ±30-50%

---

### LOD 200 - Vorentwurf
**Eingaben:** Basis-Geometrie
- Zonierung (grob, 2-5 Zonen)
- Hüllflächen mit Ausrichtung
- U-Werte pauschal oder nach Katalog

**Defaults/Formeln:**
- **Katalog-Konstruktionen** (vordefinierte Layer Structures)
  - "Außenwand unsaniert 1960er" → Layer Structure mit typischen Materialien
  - "Außenwand WDVS 14cm" → Standard-Aufbau
- Fensterflächen pro Orientierung (Verteilungsregel)
- g-Wert nach Baujahr-Tabelle
- Anlagentechnik aus Katalog (Typwerte)

**Genauigkeit:** ±20-30%

---

### LOD 300 - Entwurf
**Eingaben:** Detaillierte Geometrie
- Zonierung mit Nutzungsprofilen
- Bauteile mit IFC-Referenzen
- U-Werte gemessen oder berechnet
- Systeme mit Hersteller-Daten

**Defaults/Formeln:**
- **Übergangswiderstände** (R_si, R_se nach DIN EN ISO 6946)
- **Luftwechselrate n50** nach Gebäudeklasse
  - Neubau ohne Zertifikat: 3.0 1/h
  - Neubau mit Blower Door: 1.5 1/h
- COP-Werte Wärmepumpe nach Produktdatenblätter (wenn keine eigenen Werte)

**Genauigkeit:** ±10-15%

---

### LOD 400 - Ausführungsplanung
**Eingaben:** Vollständige Spezifikation
- Alle Schichtaufbauten mit Materialien
- Gemessene U-Werte (falls vorhanden)
- Anlagen mit exakten Kennlinien
- Regelungsstrategien

**Defaults:**
- Minimal (nur technische Konstanten)
- Physikalische Randbedingungen (DIN-Normen)

**Genauigkeit:** ±5-10%

---

### LOD 500 - As-Built / Monitoring
**Eingaben:** Reale Messdaten
- Verbrauchsdaten
- Blower Door Messung
- U-Wert Messungen
- Monitoring-Integration

**Keine Defaults** - nur reale Daten

**Genauigkeit:** Real (für Vergleich Bedarf vs. Verbrauch)

---

## 🗂️ Katalog-Struktur

### 📚 Primäre Quelle: Bundesanzeiger 2020

**Offizielle Basis:** [Bekanntmachung der Regeln zur Datenaufnahme und Datenverwendung im Wohngebäudebestand](https://bundesanzeiger.de/pub/publication/qzQUGd8A3unSCCbVMcf/content/qzQUGd8A3unSCCbVMcf/BAnz%20AT%2004.12.2020%20B1.pdf)

- **Herausgeber:** BMWi + BMI (8. Oktober 2020)
- **Umfang:** 31 Seiten mit tabellarischen Pauschalwerten
- **Rechtsgrundlage:** BEG-Förderung, offizielle Standards
- **Ersetzt:** Bekanntmachung vom 7. April 2015

**Enthaltene Daten:**
- U-Werte opaker Bauteile nach Baujahr (nicht nachträglich gedämmt)
- Vereinfachte Geometrieaufnahme
- Standardisierte Ausgangszustände für Energieberatung

**Nutzung im Projekt:**
- Als **Fallback-Quelle** für LOD 100-200 (wenn keine detaillierten Daten vorliegen)
- Rechtssichere Basis für Förderanträge
- Erweitert durch IWU-Gebäudetypologie für Details

---

### 1. Konstruktions-Katalog (`catalogs/constructions/`)

**Beispiel: Außenwände nach Baujahr (Basis: Bundesanzeiger 2020)**
```json
{
  "catalog_id": "DE_AUSSENWAENDE_BAUJAHR_BMWI2020",
  "name": "Außenwände Deutschland nach Baujahr (Bundesanzeiger)",
  "version": "1.0",
  "source": "Bundesanzeiger AT 04.12.2020 B1 (BMWi/BMI)",
  "source_url": "https://bundesanzeiger.de/pub/publication/qzQUGd8A3unSCCbVMcf/...",
  
  "entries": [
    {
      "id": "AW_1860_1918",
      "name": "Außenwand vor 1918 (Ziegelmauerwerk)",
      "applicable_years": [1860, 1918],
      "layer_structure": {
        "type": "WALL",
        "layers": [
          {"material_id": "CAT_PLASTER_LIME", "thickness_mm": 20},
          {"material_id": "CAT_BRICK_SOLID", "thickness_mm": 365},
          {"material_id": "CAT_PLASTER_LIME", "thickness_mm": 20}
        ]
      },
      "u_value_typical": 1.4,
      "u_value_range": [1.2, 1.7]
    },
    {
      "id": "AW_2002_2009_ENEV",
      "name": "Außenwand EnEV 2002-2009 (WDVS)",
      "applicable_years": [2002, 2009],
      "layer_structure": {...},
      "u_value_typical": 0.35,
      "u_value_range": [0.28, 0.45]
    }
  ]
}
```

### 2. Material-Katalog (`catalogs/materials/`)

**Standard-Materialien mit typischen Werten:**
```json
{
  "catalog_id": "DE_MATERIALS_STANDARD",
  "entries": [
    {
      "id": "CAT_BRICK_SOLID",
      "name": "Vollziegel",
      "lambda": 0.84,
      "density": 1800,
      "specific_heat": 1000,
      "vapor_resistance_factor": 10,
      "oekobau_uuid": "..."
    },
    {
      "id": "CAT_EPS_040",
      "name": "EPS-Dämmung λ=0.040",
      "lambda": 0.040,
      "density": 20,
      "specific_heat": 1500,
      "vapor_resistance_factor": 50
    }
  ]
}
```

### 3. System-Katalog (`catalogs/systems/`)

**Anlagentechnik-Typwerte:**
```json
{
  "catalog_id": "DE_HEATING_SYSTEMS",
  "entries": [
    {
      "id": "SYS_BOILER_GAS_OLD",
      "name": "Gaskessel Standard (vor 1995)",
      "type": "BOILER_GAS",
      "efficiency_annual": 0.72,
      "applicable_years": [1960, 1995],
      "typical_age": 25
    },
    {
      "id": "SYS_HP_AIR_MODERN",
      "name": "Luft-Wasser-WP modern (COP A2/W35 = 3.8)",
      "type": "HEAT_PUMP_AIR",
      "cop_a2_w35": 3.8,
      "cop_a7_w35": 4.5,
      "applicable_years": [2020, 2030]
    }
  ]
}
```

---

## 🔧 Schema-Erweiterungen

### 1. LOD-Metadaten

**In `meta` Objekt:**
```json
{
  "meta": {
    "lod": "200",  // 100, 200, 300, 400, 500
    "data_quality": {
      "geometry": "200",
      "envelope": "300",
      "systems": "200"
    },
    "default_source": "catalog",  // "catalog", "formula", "measured", "mixed"
    "catalog_references": [
      "DE_AUSSENWAENDE_BAUJAHR v1.0",
      "DE_MATERIALS_STANDARD v1.2"
    ]
  }
}
```

### 2. Default-Tracking in Feldern

**Option A: Separate Felder (explizit)**
```json
{
  "u_value_undisturbed": 0.35,
  "u_value_source": "catalog",  // "catalog", "calculated", "measured", "estimated"
  "u_value_catalog_ref": "AW_2002_2009_ENEV"
}
```

**Option B: Namespace (kompakt, empfohlen)**
```json
{
  "u_value_undisturbed": 0.35,
  "_defaults": {
    "u_value_undisturbed": {
      "source": "catalog",
      "catalog_ref": "AW_2002_2009_ENEV",
      "overridden": false
    }
  }
}
```

**Option C: Embedded Metadata (JSON-LD Style)**
```json
{
  "u_value_undisturbed": {
    "@value": 0.35,
    "@source": "catalog:AW_2002_2009_ENEV",
    "@confidence": 0.8
  }
}
```

**Empfehlung: Option B** (sauber, erweiterbar, optional)

### 3. Formeln speichern (optional)

```json
{
  "window_area_m2": 45.5,
  "_defaults": {
    "window_area_m2": {
      "source": "formula",
      "formula": "wall_area * 0.30",
      "formula_params": {"wall_area": 150},
      "overridden": false
    }
  }
}
```

---

## 🔄 Workflow-Integration

### Use Case 1: Schnellschätzung (LOD 100)

**Input:**
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

**Software füllt automatisch:**
- Hüllflächen aus Faustregel (A/V-Verhältnis)
- U-Werte aus Baujahr-Tabelle
- Fensterflächen 30% der Außenwand
- Gaskessel Standard (η=0.72)
- Fensterlüftung

**Output:** Grobe Energiebilanz in 30 Sekunden

---

### Use Case 2: iSFP-Beratung (LOD 200)

**Input:** Basis-Geometrie + Katalog-Auswahl
```json
{
  "meta": {"lod": "200"},
  "input": {
    "elements": [
      {
        "ifc_guid": "...",
        "construction_catalog_ref": "AW_1960_1977",
        "_defaults": {
          "u_value_undisturbed": {
            "source": "catalog",
            "catalog_ref": "AW_1960_1977"
          }
        }
      }
    ]
  }
}
```

**Varianten:** Delta-Modell mit Katalog-Sanierungsmaßnahmen

---

### Use Case 3: GEG-Nachweis (LOD 400)

**Input:** Vollständige Schichten, gemessene Werte
```json
{
  "meta": {"lod": "400"},
  "input": {
    "elements": [
      {
        "layer_structure_ref": "LAYER-AW-01",
        "u_value_override": 0.24,  // Gemessen
        "_defaults": {
          "u_value_override": {
            "source": "measured",
            "measurement_date": "2026-02-15",
            "measurement_method": "U-Wert-Messung nach ISO 9869"
          }
        }
      }
    ]
  }
}
```

---

## 📋 Implementierungsschritte

### Phase 1: Konzept & Katalog-Struktur definieren

1. **LOD-Levels finalisieren:**
   - Welche Felder sind pro LOD Pflicht/Optional/Default?
   - Mapping-Tabelle erstellen

2. **Katalog-Format definieren:**
   - JSON-Schema für Kataloge
   - Ordnerstruktur `catalogs/`
   - Versionierung (Breaking/Non-Breaking Changes)

3. **Default-Tracking entscheiden:**
   - Option A, B oder C?
   - Konflikte mit bestehendem Schema?

---

### Phase 2: Schema erweitern

1. **Meta-Erweiterung:**
   - `lod` Feld hinzufügen
   - `data_quality` Objekt
   - `catalog_references` Array

2. **`_defaults` Namespace:**
   - Optional für jedes Objekt
   - Schema für Default-Tracking

3. **Katalog-Referenzen:**
   - `construction_catalog_ref` in `elements`
   - `system_catalog_ref` in `systems`

---

### Phase 3: Kataloge erstellen (Basis: Bundesanzeiger 2020)

**Datenbeschaffung:**
1. PDF parsen: Bundesanzeiger AT 04.12.2020 B1 (31 Seiten)
2. U-Wert-Tabellen extrahieren (nach Baujahr)
3. Als JSON-Katalog strukturieren

**Katalog-Inhalte:**

1. **Konstruktions-Katalog (Primär: Bundesanzeiger):**
   - **Außenwände:** U-Werte nach Baujahr aus BMWi-Tabellen
     - Beispiel: 1958-1978 → 3,6 W/(m²K)
     - Beispiel: ab 1979 → 1,3 W/(m²K)
   - **Dächer, Decken, Böden:** Weitere Tabellenwerte
   - **Ergänzung:** IWU-Typologien für detaillierte Schichtaufbauten (LOD 300+)

2. **Material-Katalog (Sekundär):**
   - 20 Standard-Materialien (Mauerwerk, Dämmungen, Beton, Holz)
   - Quelle: DIN 4108, Ökobaudat
   
3. **System-Katalog (Ergänzend):**
   - 15 typische Heizsysteme
   - 5 Lüftungssysteme
   - Quelle: DIN 18599 Typwerte

**Rechtliche Absicherung:**
- Offizielle BMWi/BMI-Quelle zitieren
- Hinweis auf BEG-Konformität

**Dateiformat:**
```
catalogs/
├── materials/
│   └── de-standard-v1.0.json
├── constructions/
│   ├── de-walls-byyear-v1.0.json
│   ├── de-roofs-standard-v1.0.json
│   └── de-floors-standard-v1.0.json
└── systems/
    ├── de-heating-v1.0.json
    └── de-ventilation-v1.0.json
```

---

### Phase 4: Beispiele & Dokumentation

1. **3 LOD-Beispiele:**
   - `examples/lod100_schnellschaetzung.din18599.json`
   - `examples/lod200_isfp.din18599.json`
   - `examples/lod400_geg_nachweis.din18599.json`

2. **LOD-Guide:**
   - `docs/LOD_GUIDE.md`
   - Wann welcher LOD?
   - Workflow-Beispiele
   - Datenqualität vs. Aufwand

3. **Katalog-Dokumentation:**
   - `docs/CATALOG_FORMAT.md`
   - Wie eigene Kataloge erstellen?
   - Versionierung & Updates

---

### Phase 5: Validator erweitern

1. **LOD-Validierung:**
   - Pflichtfelder pro LOD prüfen
   - Warnungen bei LOD-Inkonsistenzen

2. **Katalog-Referenzen prüfen:**
   - Existiert `catalog_ref`?
   - Version kompatibel?

3. **Default-Tracking validieren:**
   - `_defaults` korrekt strukturiert?

---

### Phase 6: Tools (optional)

1. **Katalog-Browser (Web):**
   - HTML-Viewer für Kataloge
   - Suche, Filter nach Baujahr/Typ
   - Copy-Paste Referenzen

2. **Auto-Fill Tool:**
   ```bash
   python tools/autofill.py --input minimal.json --lod 200 --catalogs DE
   ```
   - Füllt Defaults aus Katalogen
   - Generiert vollständiges JSON

---

## ❓ Offene Fragen (ENTSCHEIDUNG ERFORDERLICH)

### 1. Default-Tracking: Welche Option?
- **A:** Separate `_source` Felder (explizit, redundant)
- **B:** `_defaults` Namespace (sauber, empfohlen)
- **C:** JSON-LD Style (komplex, zukunftssicher)

**Meine Empfehlung:** Option B

---

### 2. Katalog-Scope: Wie umfangreich?
- **Minimal (Phase 1):** Bundesanzeiger U-Wert-Tabellen (~20 Baujahr-Epochen) ✅
- **Standard (Phase 2):** + IWU-Typologien (~100 Konstruktionen)
- **Vollständig (später):** + Regionale Varianten, Hersteller-Daten

**Meine Empfehlung:** Start mit Minimal (Bundesanzeiger), dann Standard

---

### 3. LOD-Pflichtfelder: Wie streng?
- **Streng:** LOD 100 erfordert nur 5 Felder, Rest defaults
- **Flexibel:** LOD ist Hinweis, keine harte Validierung
- **Hybrid:** Pflichtfelder + Warnungen

**Meine Empfehlung:** Hybrid

---

### 4. Formel-Engine: Implementieren?
- **Ja:** Dynamische Berechnungen (z.B. Fensterfläche aus Wandfläche)
- **Nein:** Nur statische Katalogwerte
- **Später:** Feature für v2.0

**Meine Empfehlung:** Später (erstmal Kataloge etablieren)

---

## 🎯 Nächster Schritt

**Bitte entscheide:**
1. Default-Tracking Methode (A/B/C)?
2. Katalog-Scope (Minimal/Standard/Vollständig)?
3. Formel-Engine jetzt oder später?

**Dann kann ich:**
- LOD-Konzept finalisieren
- Mit Schichtaufbau-Plan harmonisieren
- Gemeinsamen Implementierungsplan erstellen

**Soll ich direkt mit Option B + Standard-Katalog + "Formeln später" starten?**
