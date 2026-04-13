# Migration v3.0 → v3.1

> **Keine Breaking Changes.** Jedes valide v3.0-Sidecar ist auch ein valides
> v3.1-Sidecar. Die neuen Felder sind rein additiv und optional.

## Motivation

Im Workshop 13.04.2026 wurde zwischen DWEapp und din18599-ifc festgelegt:

1. **Energieausweis-Werte** sollen im Sidecar liegen, nicht in einer
   DWEapp-spezifischen Nebentabelle. Quelle ist in den meisten Fällen ein
   PDF, das der Energieberater manuell abtippt, oder später ein Nextcloud-Link.
2. **Zielwerte** müssen separat definierbar sein für den Fall, dass nur
   eine IFC-Datei vorliegt und noch kein Verbrauchsausweis oder Messwerte —
   typisch bei Neubau-Beratung und bei Bestandsprojekten ohne Historie.

Beide gehören konzeptionell in `input`, weil sie Eingangsgrößen der
DIN-Berechnung sind (Soll-Ist-Vergleich), nicht Output und nicht Szenario.

## Änderungen

### 1. `schema_info`

| Feld | v3.0 | v3.1 |
|------|------|------|
| `url` const | `https://din18599-ifc.de/schema/v3.0/complete` | `https://din18599-ifc.de/schema/v3.1/complete` |
| `version` pattern | `^3\.0\.\d+$` | `^3\.1\.\d+$` |

### 2. Neu: `input.energy_certificate`

Neues optionales Objekt unter `input`. Alle Felder sind optional, weil
Teil-Ausweise explizit erlaubt sind (z.B. nur Verbrauch ohne Bedarf).

```json
{
  "input": {
    "energy_certificate": {
      "certificate_type": "VERBRAUCH",
      "issued_on": "2024-03-01",
      "valid_until": "2034-02-28",
      "issuer_name": "DWE Beratung GmbH",
      "final_energy_kwh_m2a": 145.2,
      "primary_energy_kwh_m2a": 178.4,
      "co2_kg_m2a": 36.1,
      "energy_class": "E",
      "heating_source": "Gasbrennwertkessel",
      "hotwater_source": "Gas",
      "source": "PDF_UPLOAD",
      "source_ref": "documents/ausweis-2024-03.pdf",
      "note": "Aus dem Ausweis manuell abgetippt, Original in Nextcloud"
    }
  }
}
```

**Felder (alle optional):**

- `certificate_type`: `"VERBRAUCH" | "BEDARF"`
- `issued_on` / `valid_until`: ISO-8601 Date
- `issuer_name`: Name des Energieberaters
- `final_energy_kwh_m2a`: Endenergie (kWh/(m²·a))
- `primary_energy_kwh_m2a`: Primärenergie
- `co2_kg_m2a`: CO₂-Emissionen
- `energy_class`: `A+ | A | B | C | D | E | F | G | H`
- `heating_source` / `hotwater_source`: Freier Text
- `source`: `"MANUAL_ENTRY" | "PDF_UPLOAD" | "NEXTCLOUD_LINK"` — wichtig für Audit
- `source_ref`: Verweis auf das Quelldokument (storage_ref oder Nextcloud-Pfad)
- `note`: Freitext

### 3. Neu: `input.targets`

Neues optionales Objekt mit einer Liste von Zielwerten. Im Gegensatz zum
Energieausweis (harte Messwerte) sind Zielwerte weicher: vom Energieberater
oder Kunden definiert, für Soll-Ist-Vergleiche.

```json
{
  "input": {
    "targets": {
      "defined_by": "DWE Beratung GmbH",
      "defined_on": "2026-04-14",
      "entries": [
        {
          "id": "t-endenergie-2030",
          "kind": "FINAL_ENERGY_KWH_M2A",
          "label": "Zielwert Endenergie 2030",
          "value": 55,
          "year": 2030,
          "source": "EXPERT_ESTIMATE",
          "note": "Orientiert am GEG-Neubaustandard"
        },
        {
          "id": "t-co2-2045",
          "kind": "CO2_KG_M2A",
          "label": "Klimaneutralität",
          "value": 0,
          "year": 2045,
          "source": "LEGAL_MINIMUM"
        }
      ]
    }
  }
}
```

**Pflichtfelder pro Eintrag:** `id`, `kind`, `value`.

**`kind`-Werte:**
- `FINAL_ENERGY_KWH_M2A`
- `PRIMARY_ENERGY_KWH_M2A`
- `CO2_KG_M2A`
- `HEATING_ENERGY_KWH_M2A`
- `OTHER`

**`source`-Werte:**
- `EXPERT_ESTIMATE` — Fachliche Schätzung
- `BENCHMARK` — Aus Vergleichswerten abgeleitet
- `LEGAL_MINIMUM` — Aus GEG/EnEV/anderen Vorschriften
- `CUSTOM` — Frei definiert

## Upgrade-Pfad für bestehende Sidecars

1. `schema_info.url` auf `https://din18599-ifc.de/schema/v3.1/complete` setzen
2. `schema_info.version` auf `3.1.0` hochziehen
3. Fertig — keine weiteren Aktionen nötig, solange keine v3.1-Features genutzt werden

Sobald ein neues v3.1-Feld geschrieben wird (z.B. `input.energy_certificate`),
muss der Konsument natürlich gegen das v3.1-Schema validieren.

## Kompatibilität DWEapp ↔ din18599-ifc

| Komponente | v3.0 | v3.1 |
|------------|------|------|
| DWEapp `src/types/din18599.ts` | aktuell | bei v3.1-Nutzung `schema:generate` neu ausführen |
| DWEapp `scripts/schema-check.mjs` | prüft gegen v3.0 | **Umstellung nötig, wenn v3.1 produktiv** |
| din18599-ifc Python Validator | v3.0-URL | v3.1-URL-Eintrag ergänzen |
| IFC→Sidecar Parser | v3.0 | keine Änderung, bleibt rückwärtskompatibel |
