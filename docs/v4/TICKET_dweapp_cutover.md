# TICKET: DWEapp-Cutover auf Schema v4.0

> **Status:** offen, nicht terminiert. Auszuführen beim v4.0-Umstieg, gemeinsam mit Timo.
> **Betrifft:** `/opt/weclapp-manager` (DWEapp) — nicht dieses Repo.
> **Angelegt:** 2026-07-21, Review-Auflage B.

---

## Kurzfassung

DWEapp ist der einzige echte Konsument des v3.x-Sidecar-Schemas. Er hängt an **drei
verschiedenen Schema-Versionen gleichzeitig** und hat sich in einem Punkt vom Standard
abgekoppelt. Alle drei Fundstellen müssen beim v4.0-Cutover **synchron** umgestellt
werden — einzeln umgestellt erzeugt jede von ihnen einen inkonsistenten Zwischenstand.

**Bis dahin gilt: `schema/v3.0-complete.json` ist unantastbar.** Es ist die Quelle der
TypeScript-Typen von DWEapp; ein Entfernen bricht dort sofort `npm run preflight`.

---

## Fundstelle 1 — erfundene Schema-URL

**Datei:** `src/server/api/routers/__tests__/qng-evebi-parser.test.ts:56`

```ts
schema_info: { version: '3.2.0', url: 'https://dweapp.de/schema/v3.2' }
```

Die kanonische URL lautet `https://din18599-ifc.de/schema/...`. `dweapp.de` existiert im
Standard nicht und ist frei erfunden. Weil das Schema die URL als `const` prüft, würde
ein so gebautes Sidecar gegen das echte Schema **durchfallen** — der Test zementiert
also einen ungültigen Zustand.

Verschärfend: v3.2 wurde inzwischen verworfen (siehe CHANGELOG). Die Version, auf die
sich dieser Test bezieht, gibt es nicht mehr.

**Zu tun:** URL auf `https://din18599-ifc.de/schema/v4.0/sidecar` und Version auf
`4.0.0` umstellen.

---

## Fundstelle 2 — Auto-Bump und Schreiber laufen auseinander

**Dateien:** `src/server/lib/sidecar-patch.ts` gegen `src/server/api/routers/qng.ts:853`

`sidecar-patch.ts` kennt zwei URL-Konstanten und hebt Sidecars beim Schreiben in
v3.1-only-Pfade automatisch auf **3.1**:

```ts
export const SCHEMA_V30_URL = 'https://din18599-ifc.de/schema/v3.0/complete'
export const SCHEMA_V31_URL = 'https://din18599-ifc.de/schema/v3.1/complete'
const V31_ONLY_PATHS = new Set(['input.energy_certificate', 'input.targets'])
```

`qng.ts:853` schreibt dagegen beim QNG-Freigabepfad **3.2.0** als Default in
`buildings_v2.sidecar_version`:

```ts
sidecar_version: (patchedSidecar as ...).schema_info?.version ?? '3.2.0'
```

Ergebnis: In der Datenbank steht `sidecar_version = '3.2.0'`, während das
Sidecar-JSON selbst nach dem Auto-Bump `schema_info.version = '3.1.0'` trägt. Die
Spalte und der Inhalt widersprechen sich, und 3.2.0 verweist auf ein verworfenes Schema.

**Zu tun:** eine einzige Konstante `SCHEMA_V40_URL`, Auto-Bump-Logik auf v4.0,
Default in `qng.ts` entfernen oder auf dieselbe Konstante ziehen. Bestandsdaten mit
`sidecar_version = '3.2.0'` beim Cutover mitmigrieren.

---

## Fundstelle 3 — TS-Typen aus v3.0

**Datei:** `scripts/schema-check.mjs:23`

```js
const SCHEMA_SOURCE = join(SCHEMA_BASE, 'schema/v3.0-complete.json')
```

Die generierten Typen in `src/types/din18599.generated.ts` stammen aus **v3.0**. Alles,
was v3.1 hinzugefügt hat (`input.energy_certificate`, `input.targets`), ist typseitig
unbekannt — obwohl `sidecar-patch.ts` genau diese Pfade schreibt. Deshalb die
`as unknown as`-Casts an den Aufrufstellen.

**Zu tun:** `SCHEMA_SOURCE` auf `schema/v4.0/sidecar.schema.json` umstellen,
`npm run schema:generate` neu laufen lassen, Casts abbauen. Achtung: der Pfad hat sich
strukturell geändert (Unterverzeichnis `v4.0/` statt Datei `vX.Y-complete.json`) — die
CI-Variable `DIN18599_IFC_PATH` bleibt, der Rest des Pfads nicht.

---

## Fundstelle 4 — `heated_area` mischt zwei Größen

**Dateien:** `din18599-ifc/api/qng/parser_nachhaltigkeit_docx.py` gegen
`parser_beg_geg_xml.py` und `parser_idi_al_ini.py`

Alle drei Parser schreiben nach `input.building.heated_area`, meinen aber nicht
dasselbe:

```python
# parser_nachhaltigkeit_docx.py — befüllt aus NRF
"nrf_m2": "input.building.heated_area",

# parser_beg_geg_xml.py — befüllt als beheizte Fläche
ki_extrahiert["input.building.heated_area"] = {"wert": nrf, "confidence": 1.0}
```

Nettoraumfläche und beheizte Fläche sind verschiedene Größen. Je nachdem, welcher
Kanal einen Eingang liefert, steht am selben Pfad etwas anderes — und niemand kann
dem Wert ansehen, welche Definition gilt.

**Zu tun beim Cutover:** nicht einfach auf `input.building.ngf_m2` umbenennen.
v4.0 definiert `ngf_m2` klar als Nettogrundfläche nach DIN 277; ein reines Umbenennen
würde die Unschärfe mitnehmen. Entweder je Parser klären, welche Größe wirklich
geliefert wird und auf `ngf_m2` bzw. ein eigenes Feld mappen, oder ein
`heated_area_source`-Feld einführen, das die Herkunftsdefinition mitführt.

---

## Fundstelle 5 — `specific_values.*.total` mischt spezifisch und absolut

**Datei:** `din18599-ifc/api/qng/parser_beg_geg_xml.py`

```python
ki_extrahiert["output.base.specific_values.primary_energy.total"]
ki_extrahiert["output.base.specific_values.final_energy.total"]
ki_extrahiert["output.base.specific_values.co2_emissions.total"]
```

Der Pfad heißt `specific_values`, das Blatt heißt `total`. Ob dort kWh/(m²·a) oder
kWh/a steht, ist aus dem Pfad nicht ableitbar und im Parser nicht dokumentiert.

v4.0 trennt beides sauber:

| Größe | absolut | spezifisch |
|---|---|---|
| Primärenergie | `output.*.primary_energy.total_kwh_a` | `.specific_kwh_m2a` |
| Endenergie | `output.*.final_energy.total_kwh_a` | — |
| CO2 | `output.*.co2.total_kg_a` | `.specific_kg_m2a` |

**Zu tun beim Cutover:** je Parser und je Kennwert prüfen, welche der beiden Größen
tatsächlich aus der Quelldatei kommt, und auf das passende Feld mappen. Ein
Sammel-Mapping auf `specific_*` wäre geraten, nicht belegt.

---

## Reihenfolge beim Cutover

1. `schema-check.mjs` auf v4.0 umstellen, Typen regenerieren → deckt auf, was bricht
2. `sidecar-patch.ts`: Konstanten und Auto-Bump-Pfade auf v4.0
3. `qng.ts`: Default-Version entfernen
4. Tests: erfundene URL korrigieren
5. Datenmigration `buildings_v2.sidecar_version` + `building_versions_v2`
6. Erst danach darf `v3.0-complete.json` archiviert werden

---

## Offene Vorfrage: Pfad-Umbenennungen

Der Cutover ist **kein reines Suchen-und-Ersetzen der Version**. v4.0 hat Feldnamen
verändert, die DWEapp heute schreibt — Details in
[QNG_SIDECAR_PFADE.md](QNG_SIDECAR_PFADE.md). Diese Liste ist vor Schritt 1 zu klären.
