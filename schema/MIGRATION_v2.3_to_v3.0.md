# Migration v2.3 → v3.0

> **Datum:** 09.04.2026
> **Abwaertskompatibel:** Ja — v2.3 Dokumente sind gueltige v3.0 Dokumente (neue Felder optional)

## Neue Top-Level Sections

| Section | Pflicht | Beschreibung |
|---------|:-------:|-------------|
| `documents[]` | Nein | Dokumente, Nachweise, Plaene, Fotos, Rechnungen als Cloud-Links |
| `funding[]` | Nein | Foerderungen (BEG, KfW, BAFA) mit Snapshot + ERPNext-Referenz |
| `roadmap` | Nein | Sanierungsfahrplan mit priorisierten Schritten |
| `sla_context` | Nein | Sandbox-Bruecke: abgeleitete Parameter fuer SLA-Kalkulation |

## Neue Definitions

| Definition | Verwendet in |
|-----------|-------------|
| `document` | `documents[]` |
| `funding_entry` | `funding[]` |
| `roadmap_step` | `roadmap.steps[]` |

## Schema-Info Aenderungen

```diff
- "$id": "https://din18599-ifc.de/schema/v2.3/complete"
+ "$id": "https://din18599-ifc.de/schema/v3.0/complete"

- "version": "2.3.0"
+ "version": "3.0.0"

- "pattern": "^2\\.3\\.\\d+$"
+ "pattern": "^3\\.0\\.\\d+$"
```

## Konzepte

### Storage Resolver (documents.storage_ref)

Dokumente werden als logischer Pfad gespeichert, nicht als volle URL:

```
buildings/{building_id}/documents/energieausweis.pdf
buildings/{building_id}/ifc/gebaeude.ifc
buildings/{building_id}/fotos/fassade_sued.jpg
```

Ein Storage-Resolver-Service loest den Pfad zur vollen URL auf (Nextcloud, S3, etc.).
Bei Provider-Wechsel aendert sich nur die Resolver-Konfiguration, kein Sidecar.

### Hybrid Funding (funding.snapshot + erpnext_ref)

- `program`, `scenario_ref` = technische Zuordnung (Sidecar-owned)
- `erpnext_ref` = Link zum ERPNext-Datensatz (Source of Truth fuer Finanzen)
- `snapshot` = letzter Stand, wird per n8n-Workflow synchronisiert

### SLA Context (sla_context)

Abgeleitete Parameter fuer die SLA-Sandbox-Kalkulation:
- `bgf`, `we`, `bt` = Grunddaten (alternativ aus input.building abgeleitet)
- `gebaeudeart` = WG/NWG/MISCH
- `scenarios[]` = Mapping Sidecar-Szenarien → SLA-Szenarien + Massnahmen

## Migration bestehender Dateien

Keine Aenderungen noetig — alle neuen Felder sind optional.
Bestehende v2.3 Dateien koennen als v3.0 gelesen werden, nur `schema_info` muss aktualisiert werden.
