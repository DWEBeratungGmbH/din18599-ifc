# Level of Detail (LOD) Guide

**Version:** 2.0  
**Stand:** März 2026

---

## 1. Überblick

Das **Level of Detail (LOD)** Konzept definiert die **Detailtiefe** und **Genauigkeit** der energetischen Gebäudedaten. Es orientiert sich an BIM-Standards (LOD 100-500) und passt diese für die Energieberatung an.

**Kernidee:**
- **LOD 100:** Schnellschätzung (±30-50% Genauigkeit)
- **LOD 200:** iSFP-Beratung (±20-30% Genauigkeit)
- **LOD 300:** Variantenvergleich (±10-15% Genauigkeit)
- **LOD 400:** GEG-Nachweis (±5-10% Genauigkeit)
- **LOD 500:** As-Built / Monitoring (±2-5% Genauigkeit)

---

## 2. LOD-Definitionen

### LOD 100 - Konzept / Schnellschätzung

**Zweck:** Machbarkeitsstudie, erste Kostenschätzung

**Datenquellen:**
- Grobe Geometrie (Außenmaße, Geschosszahl)
- Baujahr → Katalog-U-Werte (Bundesanzeiger)
- Pauschale Systeme (Heizungstyp, Baujahr)

**Eingabedaten:**
- ✅ Zonen (1-3 Zonen, grobe Flächen)
- ✅ Bauteile (Katalog-Referenzen, keine Schichtaufbauten)
- ✅ Systeme (Typ, Baujahr, Energieträger)
- ❌ Keine detaillierten Schichtaufbauten
- ❌ Keine Wärmebrücken-Details
- ❌ Keine Lüftungskonzepte

**Genauigkeit:** ±30-50%

**Use Cases:**
- Erste Beratung (Telefonat, Vor-Ort-Termin)
- Machbarkeitsstudie
- Grobe Kostenschätzung

**Beispiel:** [lod100_schnellschaetzung.din18599.json](../examples/lod100_schnellschaetzung.din18599.json)

---

### LOD 200 - Vorentwurf / iSFP-Beratung

**Zweck:** iSFP (individueller Sanierungsfahrplan), Förderantrag KfW/BAFA

**Datenquellen:**
- Begehung vor Ort
- Baujahr → Katalog-U-Werte (Bundesanzeiger)
- Visuelle Systemerfassung
- Grobe Geometrie aus IFC (optional)

**Eingabedaten:**
- ✅ Zonen (detailliert, nach Nutzung)
- ✅ Bauteile (Katalog-Referenzen + ΔU_WB)
- ✅ Fenster (U_g, U_f, g-Wert)
- ✅ Systeme (Typ, Baujahr, Betriebsweise)
- ✅ Verteilung (Rohrdämmung, hydraulischer Abgleich)
- ✅ DHW (Speicher, Zirkulation)
- ✅ Lüftung (Typ, Wärmerückgewinnung)
- ❌ Keine detaillierten Schichtaufbauten
- ❌ Keine Blower-Door-Messung

**Genauigkeit:** ±20-30%

**Use Cases:**
- iSFP (individueller Sanierungsfahrplan)
- Förderantrag KfW/BAFA (Einzelmaßnahmen)
- Sanierungsberatung

**Beispiel:** [lod200_bestandsaufnahme.din18599.json](../examples/lod200_bestandsaufnahme.din18599.json)

---

### LOD 300 - Entwurf / Variantenvergleich

**Zweck:** Variantenvergleich, Wirtschaftlichkeitsberechnung, Fördergutachten

**Datenquellen:**
- Detaillierte Begehung
- Schichtaufbauten (aus Plänen oder Annahmen)
- Produktdatenblätter (Fenster, Dämmung)
- IFC-Geometrie (detailliert)

**Eingabedaten:**
- ✅ Zonen (detailliert, nach Nutzung)
- ✅ Bauteile (Schichtaufbauten mit Materialien)
- ✅ Materialien (λ-Werte, ρ, c, μ)
- ✅ Layer Structures (Schichtaufbauten von außen nach innen)
- ✅ Fenster (detailliert, Ψ-Werte)
- ✅ Systeme (detailliert, COP-Kennlinien)
- ✅ Varianten (Base + Scenarios, Delta-Modell)
- ❌ Keine Blower-Door-Messung
- ❌ Keine Thermografie

**Genauigkeit:** ±10-15%

**Use Cases:**
- Variantenvergleich (Sanierungsszenarien)
- Wirtschaftlichkeitsberechnung
- Fördergutachten (KfW Effizienzhaus)
- iSFP mit Variantenvergleich

**Beispiel:** [lod300_sanierung_varianten.din18599.json](../examples/lod300_sanierung_varianten.din18599.json)

---

### LOD 400 - Ausführung / GEG-Nachweis

**Zweck:** GEG-Nachweis, Bauantrag, Förderbescheid

**Datenquellen:**
- Ausführungsplanung (detaillierte Pläne)
- Produktdatenblätter (alle Bauteile)
- Blower-Door-Test (n50-Wert)
- Wärmebrücken-Katalog (Ψ-Werte)

**Eingabedaten:**
- ✅ Zonen (detailliert, nach DIN 18599-10)
- ✅ Bauteile (vollständige Schichtaufbauten)
- ✅ Materialien (λ, ρ, c, μ, sd-Wert)
- ✅ Layer Structures (detailliert, mit R-Wert-Berechnung)
- ✅ Fenster (detailliert, Ψ-Werte, Verschattung)
- ✅ Systeme (vollständig, COP-Kennlinien, Kältemittel)
- ✅ Wärmebrücken (detailliert, Ψ-Katalog)
- ✅ Blower-Door (gemessener n50-Wert)
- ✅ Lüftung (detailliert, Volumenstrom, SFP)
- ✅ Beleuchtung (installierte Leistung, Steuerung)
- ✅ Automation (Klasse A-D)
- ✅ PV (Nennleistung, Ausrichtung, Speicher)

**Genauigkeit:** ±5-10%

**Use Cases:**
- GEG-Nachweis (Bauantrag)
- Förderbescheid KfW/BAFA
- Energieausweis (Neubau)
- QNG-Zertifizierung

**Beispiel:** [lod400_geg_nachweis.din18599.json](../examples/lod400_geg_nachweis.din18599.json)

---

### LOD 500 - As-Built / Monitoring

**Zweck:** Monitoring, Verbrauchsabgleich, Optimierung

**Datenquellen:**
- As-Built-Dokumentation
- Bestandspläne (aktualisiert)
- Messdaten (Verbrauch, Temperaturen)
- Thermografie
- Blower-Door-Test

**Eingabedaten:**
- ✅ Alle LOD 400 Daten
- ✅ Gemessene Verbräuche (Heizung, Strom, Wasser)
- ✅ Thermografie-Ergebnisse
- ✅ Raumtemperaturen (gemessen)
- ✅ Lüftungsraten (gemessen)
- ✅ Anlagen-Betriebsdaten (COP real, Laufzeiten)

**Genauigkeit:** ±2-5%

**Use Cases:**
- Monitoring (Verbrauchsabgleich)
- Optimierung (Betriebsoptimierung)
- Performance-Gap-Analyse
- Energieausweis (Bestand, Verbrauch)

**Beispiel:** Noch nicht implementiert

---

## 3. LOD-Vergleich

| Kriterium | LOD 100 | LOD 200 | LOD 300 | LOD 400 | LOD 500 |
|-----------|---------|---------|---------|---------|---------|
| **Genauigkeit** | ±30-50% | ±20-30% | ±10-15% | ±5-10% | ±2-5% |
| **Zeitaufwand** | 1-2h | 4-8h | 16-24h | 40-60h | 80-120h |
| **Datenquellen** | Baujahr | Begehung | Pläne | Ausführung | Messung |
| **U-Werte** | Katalog | Katalog | Berechnet | Berechnet | Gemessen |
| **Schichtaufbauten** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Wärmebrücken** | Pauschal | Pauschal | Katalog | Detailliert | Thermografie |
| **Blower-Door** | Annahme | Annahme | Annahme | Gemessen | Gemessen |
| **Systeme** | Typ | Typ | Detailliert | Vollständig | + Messdaten |
| **Varianten** | ❌ | ❌ | ✅ | ✅ | ✅ |
| **Use Case** | Machbarkeit | iSFP | Varianten | GEG | Monitoring |

---

## 4. LOD-Auswahl (Entscheidungsbaum)

```
Welches LOD brauche ich?
│
├─ Nur grobe Schätzung?
│  └─ LOD 100 (Schnellschätzung)
│
├─ iSFP / Förderantrag Einzelmaßnahme?
│  └─ LOD 200 (iSFP-Beratung)
│
├─ Variantenvergleich / Wirtschaftlichkeit?
│  └─ LOD 300 (Variantenvergleich)
│
├─ GEG-Nachweis / Bauantrag?
│  └─ LOD 400 (GEG-Nachweis)
│
└─ Monitoring / Verbrauchsabgleich?
   └─ LOD 500 (As-Built / Monitoring)
```

---

## 5. LOD-Upgrade-Pfad

**Von LOD 100 → LOD 200:**
- Begehung vor Ort
- Detaillierte Zonierung
- Systeme erfassen (Typ, Baujahr)
- Wärmebrücken-Zuschläge ergänzen

**Von LOD 200 → LOD 300:**
- Schichtaufbauten definieren
- Materialien ergänzen (λ-Werte)
- Layer Structures erstellen
- Varianten definieren (Delta-Modell)

**Von LOD 300 → LOD 400:**
- Blower-Door-Test durchführen
- Wärmebrücken detailliert (Ψ-Katalog)
- Produktdatenblätter einholen
- Lüftung, Beleuchtung, Automation ergänzen

**Von LOD 400 → LOD 500:**
- Messdaten erfassen (Verbrauch, Temperaturen)
- Thermografie durchführen
- Anlagen-Betriebsdaten loggen
- Verbrauchsabgleich

---

## 6. LOD im Schema

### meta.lod

```json
{
  "meta": {
    "lod": "300",
    "data_quality": {
      "geometry": "300",
      "envelope": "300",
      "systems": "200"
    }
  }
}
```

**Bedeutung:**
- `lod`: Gesamt-LOD des Projekts
- `data_quality.geometry`: LOD der Geometrie (IFC)
- `data_quality.envelope`: LOD der Hülle (U-Werte, Schichtaufbauten)
- `data_quality.systems`: LOD der Anlagentechnik

**Regel:** `lod` = min(geometry, envelope, systems)

---

## 7. Katalog-Verwendung nach LOD

| LOD | Katalog-Verwendung |
|-----|-------------------|
| **100** | Bundesanzeiger (Baujahr → U-Wert) |
| **200** | Bundesanzeiger (Baujahr → U-Wert) + ΔU_WB |
| **300** | Bundesanzeiger (optional) + eigene Schichtaufbauten |
| **400** | Produktdatenblätter + Wärmebrücken-Katalog |
| **500** | Gemessene Werte + Thermografie |

Siehe [KATALOG_VERWENDUNG.md](KATALOG_VERWENDUNG.md) für Details.

---

## 8. Best Practices

### LOD 100-200: Katalog-basiert
- Nutze Bundesanzeiger-Katalog für U-Werte
- `construction_catalog_ref` statt `layer_structure_ref`
- Pauschale Wärmebrücken (DEFAULT: 0.10 W/m²K)

### LOD 300-400: Schichtaufbau-basiert
- Definiere `layer_structures` mit `materials`
- Berechne U-Werte aus Schichtaufbauten
- Nutze `u_value_override` nur bei Bedarf

### LOD 400-500: Messdaten-basiert
- Blower-Door-Test → `air_change_n50`
- Thermografie → `thermal_bridge_delta_u`
- Verbrauchsdaten → `output.energy_balance`

---

## 9. Validierung nach LOD

Der Validator prüft LOD-spezifische Pflichtfelder:

**LOD 100-200:**
- ✅ `zones[].area_an` (Fläche)
- ✅ `elements[].u_value_undisturbed` ODER `construction_catalog_ref`
- ❌ Keine `layer_structures` erforderlich

**LOD 300-400:**
- ✅ `layer_structures[]` (Schichtaufbauten)
- ✅ `materials[]` (Materialien)
- ✅ `elements[].layer_structure_ref`
- ✅ `air_change_n50` (LOD 400: gemessen)

**LOD 500:**
- ✅ Alle LOD 400 Felder
- ✅ `output.energy_balance` (gemessene Verbräuche)

---

## 10. Beispiele

Alle Beispiele befinden sich in `examples/`:

- **LOD 100:** [lod100_schnellschaetzung.din18599.json](../examples/lod100_schnellschaetzung.din18599.json)
- **LOD 200:** [lod200_bestandsaufnahme.din18599.json](../examples/lod200_bestandsaufnahme.din18599.json)
- **LOD 300:** [lod300_sanierung_varianten.din18599.json](../examples/lod300_sanierung_varianten.din18599.json)
- **LOD 400:** [lod400_geg_nachweis.din18599.json](../examples/lod400_geg_nachweis.din18599.json)

---

**Status:** ✅ LOD-Konzept ist vollständig definiert und implementiert.
