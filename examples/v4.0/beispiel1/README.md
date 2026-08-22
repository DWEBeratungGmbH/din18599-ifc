# Beispiel1 — Referenz-Container (v4.0)

> Deterministisch erzeugt von [`scripts/build-example-beispiel1.py`](../../scripts/build-example-beispiel1.py).
> Stand: 22.08.2026 · Schema v4.0 · Validierungsstufe `balanced`

## Aufbau

```
beispiel1/
├── energy.din18599.json   Sidecar v4.0 (SOURCE OF TRUTH)
└── manifest.json          Container-Manifest (Inhaltsverzeichnis, Checksumme)
```

`model.ifc` ist im Repo nicht enthalten — der Container ist trotzdem gültig
(ein `.dwe` ohne IFC ist der Normalfall für reine Bestandsaufnahme). Die
Schema-Konstanz wird im CI gegen `schema/v4.0/*.schema.json` geprüft.

## Validierungsstand

| Stufe | Status | Begründung |
|---|---|---|
| `draft` | ✅ | schema-gültig |
| `enriched` | ✅ | Raumtypen, Zonen, Konstruktionen aufgelöst |
| `geometry_ok` | ✅ | synthetische `boundaries[]` + `meta.ve_method` vorhanden |
| `balanced` | ✅ | `envelope_area_m2`, `ve_m3`, `ngf_m2` deklariert & within Toleranz |
| `calc_ready` | ⚠️ blockiert | gitignored Normwerte-Overlays fehlen (Fx, Rsi/Rse, δ₀, …) |

`calc_ready` lässt sich im öffentlichen Repo **bewusst nicht** erreichen: die
Normwerte (DIN V 18599-2 Tab. 5/6, DIN EN ISO 6946 Tab. 7/8, DIN 4108-3)
stehen unter Urheberrechtsschutz und liegen nur in
`catalog/values/*.values.json` (gitignored). Sie sind aus eigener Normlizenz
oder über die DWEapp bereitzustellen — siehe
[`docs/v4/KATALOG_FORMAT.md`](../../docs/v4/KATALOG_FORMAT.md).

## Was an `boundaries[]` synthetisch ist

Bis die Revit/Dynamo-Pipeline (Stufe 2d) die echte Angrenzungsmatrix liefert,
stehen hier **deterministische Platzhalter**:

| Aspekt | Wert |
|---|---|
| AW-* (Außenwände) | `exterior`, `space_b=null`, Fläche = `LAENGEN × RAUMHOEHE` |
| IW-WE1-WE2-* (Trennwand WE1↔WE2) | `other_zone`, beide beheizt → `relevant_18599=false` |
| IW-* innerhalb einer WE | `same_zone`, `relevant_18599=false` |
| `openings[]` | 2 Testfenster (AW-NO-01, AW-SO-01), `opening_type: "window"` |
| `openings_index` | aus `boundaries[].openings[]` berechnet (read-only) |

Die Flächen sind **illustrativ**, nicht aus echter Geometrie abgeleitet. Sie
reichen aus, um die Validator-Pfade `geometry_ok` und `balanced` real
durchlaufen zu lassen. Die echte Matrix aus Dynamo wird sie später ersetzen —
das ist ein Merge, kein Konflikt, weil der Sidecar die Wahrheit ist.

## Neuaufbau

```bash
python3 scripts/build-example-beispiel1.py
python3 tools/dwe_validate.py examples/v4.0/beispiel1/energy.din18599.json \
    --manifest examples/v4.0/beispiel1/manifest.json
python3 tools/test_dwe_validate.py    # Negativtests + saubere Referenz
```
