# Katalog-Format v4.0

> Umsetzung der sechs Katalog-Entscheidungen aus dem Review vom 21.07.2026.
> Vorgeschichte und Begründungen: [KATALOG_BESTANDSANALYSE.md](KATALOG_BESTANDSANALYSE.md) §6.

---

## Verzeichnisse

```
catalog/
├── core/                          # öffentlich, im Git — STRUKTUR
│   ├── adjacency_types.json              14 Einträge, inkl. Fx-Werte
│   ├── room_types.json                   57 Einträge (14 WG / 43 NWG)
│   ├── usage_profiles.2018-09.json       45 Profile, wertfrei
│   └── geg_reference_building.2024.json   7 Zeilen + Mapping-Regeln
└── values/                        # gitignored — ZAHLENWERTE
    ├── usage_profiles.2018-09.values.json
    └── geg_reference_building.2024.values.json

catalog-private/                   # gitignored — geschützte Norm-Daten
└── norm-derived/                         seit 21.07. hierher verschoben
```

Kein eigenes Repo (Entscheidung 6.3): Schema und Katalog entwickeln sich synchron,
ein zweites Repo verdoppelt die Release-Koordination ohne heutigen Gegenwert.

**Schutz:** `.gitignore` allein reicht nicht — sie greift nur für ungetrackte Dateien,
und `git add -f` umgeht sie lautlos. Zusätzlich erzwungen durch
[`scripts/check-catalog-values.sh`](../../scripts/check-catalog-values.sh) als
Pre-Commit-Hook und GitHub Action:

```bash
ln -sf ../../scripts/check-catalog-values.sh .git/hooks/pre-commit
bash scripts/check-catalog-values.sh --all   # CI-Modus
```

---

## Envelope (Entscheidung 6.2)

Ein generischer Rahmen für alle Kataloge, katalogspezifische Entry-Schemata darunter.
Schema: [`schema/v4.0/catalog-envelope.schema.json`](../../schema/v4.0/catalog-envelope.schema.json).

```json
{
  "$schema_ref": "https://din18599-ifc.de/schema/v4.0/catalog-envelope",
  "catalog_id": "adjacency_types",
  "catalog_version": "1.0.0",
  "catalog_source": "core",
  "dimension": { "type": "norm_edition", "value": "2018-09" },
  "values_overlay": { "required": false },
  "entry_schema_ref": "schema/v4.0/catalogs/adjacency_types.schema.json",
  "entries": [ … ]
}
```

Der Rahmen trägt genau das, was für jeden Katalog gleich sein muss: Identität,
Versionierung, Overlay-Steuerung, Herkunft. Die Einträge sind fachlich zu verschieden
für ein gemeinsames Schema — ein Fx-Wert und ein Materialschichtaufbau in ein
Entry-Schema zu zwingen erzeugt nur ein generisches `properties: {}`-Loch.

### Die drei Versionierungsklassen

Sie fallen in ein einziges `dimension.type`-Feld:

| `type` | Bedeutung | Katalog |
|---|---|---|
| `norm_edition` | Mehrere Norm-Ausgaben parallel vorhalten | `usage_profiles`, `adjacency_types` |
| `legal_edition` | Rechtlich datumsgebunden, mit `valid_from`/`valid_to` | `geg_reference_building` |
| `none` | Kuratiert, nur monoton steigendes `catalog_version` | `room_types`, `constructions`, `materials` |

`catalog_version` ist SemVer über den **Inhalt**, unabhängig von der Edition:
neue Einträge = Minor, korrigierte Werte = Patch, entfernte oder umbenannte Codes = Major.

---

## Werte-Overlay (Entscheidung 6.1)

Struktur liegt öffentlich, geschützte Zahlenwerte kommen zur Laufzeit dazu.
**Ein Overlay je Katalog UND je Edition** — die Lizenzlage kann pro Norm unterschiedlich
ausgehen, und wer eine Teil-Lizenz hat, soll genau das befüllen können, was er darf.
Eine Sammeldatei erzwänge Alles-oder-nichts.

### `norm_cell`-Zeiger statt `value: null`

Jeder Parameter-Slot trägt Einheit, Herkunftsart und Zellenzeiger — aber keinen Wert:

```json
"theta_i_h_soll": {
  "unit": "°C",
  "description": "Raum-Solltemperatur Heizung",
  "value_source": "norm_table",
  "norm_column": null
}
```

Zusammen mit dem `norm_cell` des Eintrags (`"T7-Z01"`) ergibt sich die vollständige
Zelle `T7-Z01-S19`. Das macht den Merge **prüfbar**: der Validator meldet, welche Zelle
fehlt, statt nur „irgendwo ist null".

### `null` ist reserviert

`value_source: "not_applicable"` heißt **existiert für dieses Profil nicht** — nicht
„noch nicht befüllt". Betrifft die Profile 16, 18, 19, 20 und 41: ihre Betriebszeiten
(`t_nutz_d`, `d_nutz_a`) kommen von der übergeordneten Zone über
`zone.parent_zone_ref`, nicht aus der Profiltabelle. Der Loader darf für diese Slots
**keinen** Overlay-Wert erwarten.

### Fehlt das Overlay

Kein `calc_ready`. Meldung aus `values_overlay.missing_value_message`, z.B.
„Werte-Katalog fehlt — DWEapp verbinden oder Overlay aus eigener Normlizenz befüllen."

---

## Was öffentlich ist und warum

| Katalog | Werte public? | Begründung |
|---|---|---|
| `adjacency_types` | **ja, vollständig** | Zwölf Einzelfakten aus jedem GEG-Kommentar, kein Datenbankwerk. Und die Boundary-Validierung als Grundfunktion darf nicht an einem Overlay hängen (Entscheidung 6.6) |
| `geg_reference_building` | **rechtlich ja**, faktisch noch nicht | GEG ist amtliches Werk nach § 5 UrhG, also gemeinfrei. Werte fehlen nur, weil sie belegt aus dem Gesetzestext zu übernehmen sind, nicht aus zweiter Hand |
| `usage_profiles` | **nein** | DIN-Tabellenwerte, DIN/Beuth-Urheberrecht |
| `room_types` | ja (Struktur) | DWE-eigene Definitionen und abgeleitete Profilbezüge |

---

## Sidecar-Anbindung

Zwei Ebenen, bewusst beide (Entscheidung 6.4):

- **Referenz** — `meta.catalogs[]` mit `catalog_id`, `catalog_version`, `catalog_source`,
  `dimension`. Macht eine Berechnung reproduzierbar.
- **Kopie** — `zone.used_profile_values` als Snapshot der tatsächlich verwendeten Werte,
  inklusive `norm_cell` je Wert. Bleibt nachvollziehbar, auch wenn der Katalogstand
  nicht mehr beschaffbar ist. Bitemporales Muster analog `offerSnapshot`.

---

## Generatoren

Kataloge mit vielen gleichförmigen Einträgen werden erzeugt, nicht handgepflegt:

```bash
python3 scripts/build-usage-profiles-catalog.py --edition 2018-09
python3 scripts/build-room-types-catalog.py
```

Der Profil-Generator ist auf die Ausgabe 2025-10 wiederverwendbar, sobald deren
Profilliste vorliegt.

---

## Offene Punkte

1. **`room_types` ist ein belegter Seed, keine abgenommene Liste** (`catalog_version: 0.1.0`).
   Die 43 NWG-Typen sind 1:1 aus den Nutzungsprofilen abgeleitet, die 14 WG-Typen sind
   DWE-eigene Definitionen aus der Baupraxis. Für die im Handoff genannten „~55 Typen mit
   3-Normen-Mapping" gibt es im Repo **keine Quelle** — der referenzierte Handoff-Abschnitt
   enthält die Revit-Testbefunde, keine Raumtypen. Zwei Spalten sind deshalb durchgehend
   `null`: `din_277_category` (DIN 277-1 Nutzungsarten) und `theta_heizlast_standard_c`
   (DIN EN 12831). Beides Normgrößen, die nicht geraten werden.

2. **Profilanzahl weicht ab.** Der Altbestand liefert 45 Profile (2 WG + 43 NWG),
   der Handoff nennt 42 für 2018-09 und 43 für 2025-10. Vor dem Befüllen des Overlays
   zu klären, welche Zählung stimmt.

3. **`norm_column` ist durchgehend `null`.** Zeile und Tabelle stehen fest, die
   Spaltennummern werden beim Befüllen aus der lizenzierten Quelle ergänzt.

4. **GEG Anlage 2 (Nichtwohngebäude) fehlt vollständig.** Dort ist das Referenzgebäude
   zonenweise definiert, die Zeilenstruktur ist eine andere.

5. **`constructions.json` und `materials.json`** liegen noch im alten Format unter
   `catalog/` und sind nicht auf den Envelope migriert. Sie sind DWE-eigen und
   unkritisch — Migration bei Gelegenheit.

6. **LCA/ÖKOBAUDAT** ist noch nicht angefangen. Vorlage sind die 17 produktiv
   geschriebenen QNG-Pfade, siehe [QNG_SIDECAR_PFADE.md](QNG_SIDECAR_PFADE.md).
