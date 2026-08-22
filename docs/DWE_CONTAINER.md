# Die .dwe-Container-Spezifikation (v4.0)

> Offener Datenstandard für energetische Gebäudeakten. Ein `.dwe` transportiert
> Geometrie und energetische Daten gemeinsam und bleibt dabei software-neutral.
> **Stand:** 2026-07-21 · Schema v4.0 · Apache 2.0

---

## 1. Aufbau

Ein `.dwe` ist ein ZIP-Archiv mit fester Struktur:

```
projekt.dwe
├── manifest.json          Container-Manifest — Inhaltsverzeichnis, Checksummen,
│                          Validierungsgrad. PFLICHT.
├── energy.din18599.json   Sidecar v4.0 — SOURCE OF TRUTH für alle energetischen
│                          Daten. PFLICHT.
├── model.ifc              IFC4 (ADD2). OPTIONAL.
└── attachments/           Fotos, Nachweise, PDFs. OPTIONAL.
```

Pfade sind ZIP-relativ mit Forward-Slash, ohne führenden Slash.

**Ein Container ohne `model.ifc` ist gültig.** Der Fall „reine Bestandsaufnahme ohne
Modell" ist kein Sonderfall, sondern häufig.

### Das Manifest zuerst lesen

Ein Konsument liest `manifest.json` und entscheidet daran, ob er den Container
verarbeiten kann — **bevor** er das Sidecar parst. Das Manifest trägt dafür
`contents.sidecar.schema_version` und `validation.level`.

Schemata: [`schema/v4.0/manifest.schema.json`](../schema/v4.0/manifest.schema.json) ·
[`schema/v4.0/sidecar.schema.json`](../schema/v4.0/sidecar.schema.json)

---

## 2. Der Grundsatz: wer gewinnt

> **Das Sidecar ist die Wahrheit. Das IFC ist Geometrie-Beigabe.**

Das ist keine Stilfrage, sondern die Lehre aus der Revit-Testphase:

- **IFC-SpaceBoundaries sind unbrauchbar als Rechengrundlage.** Revit-Exporte liefern
  sie notorisch lückenhaft — in den Test-IFCs: null Einträge. Die Angrenzungsmatrix
  wird deshalb extern berechnet und lebt in `input.boundaries[]`. Das Manifest
  schreibt das fest: `contents.model_ifc.space_boundaries.authoritative` ist ein
  `const: false`.
- **Autorensystem-IDs sind kein Fachdaten-Anker.** Revit-`ElementId` und selbst
  `UniqueID` überleben Copy/Monitor, Workset-Bindung und Löschen-plus-Neuzeichnen
  nicht. Fachdaten hängen deshalb an der **Bauteilgruppe** (Ebenen-Fingerprint) und
  am **Raum** (`dwe_uid` als Shared Parameter), nie an der Instanz.
- **Gemeldete Raumvolumina sind Plausibilitätswerte, keine Rechenquelle.** Ein
  Toposolid mit aktivierter Raumbegrenzung verfälscht sie still — im Testmodell um
  −2,9 % über 12 Räume. Das Sidecar führt deshalb `volume_ve_m3` (gerechnet) und
  `volume_reported_m3` (gemeldet) getrennt; der Validator warnt bei Abweichung.

Bei Widerspruch zwischen IFC und Sidecar gewinnt **immer** das Sidecar. Das Manifest
dokumentiert den Widerspruch unter `consistency`, bricht aber nicht ab.

---

## 3. Die tragenden Strukturen

### `element_groups[]` — das Bauteil als berechnete Zwischenebene

DIN 18599 rechnet nicht auf Wandinstanzen, sondern auf Bauteilen („Außenwand Süd").
Die Gruppe entsteht über einen **Koplanaritäts-Fingerprint**:

```json
"fingerprint": {
  "normal_x": 0.17, "normal_y": 0.98, "normal_z": 0.0,
  "dist_m": 4.20,
  "coordinate_system": "project",
  "tolerance": { "angle_tolerance_deg": 1.0, "dist_tolerance_m": 0.02 }
}
```

Ein Element gehört zu einer Gruppe, wenn der **Winkelabstand** seiner Normale zum
Gruppen-Repräsentanten ≤ 1° beträgt, der Ebenenabstand ±2 cm einhält und der
Bauteiltyp gleich ist — sonst eröffnet es selbst eine Gruppe. Im Testmodell:
28 Instanzen → 13 Gruppen, 12 davon geschossübergreifend.

> **Winkelabstand, nicht gerundete Werte.** Runden ist Quantisierung, keine
> Toleranz: gleich gerundete Werte trennen zwei Wände schon ab ~0,3° und
> vereinigen nie zwei Wände über eine Rundungsgrenze hinweg. Die Regel wäre
> nicht transitiv und hätte bei `normal_x ≈ 0` einen Vorzeichen-Kipppunkt.
> Deshalb werden `normal_*` und `dist_m` in **voller Rechenpräzision**
> serialisiert; Anzeige-Rundung ist Sache der UI und darf den Wert im Sidecar
> nicht ersetzen.

**Der Fingerprint lebt im Projektsystem, nicht geografisch.** Eine Korrektur der
Nordrichtung darf die Gruppierung nicht zerstören — deshalb ist
`coordinate_system` ein `const: "project"`.

`member_elements[]` ist ausdrücklich **flüchtig**: bei jedem Export neu berechnet.
Wechselnde Mitglieder sind kein Datenverlust, solange der Fingerprint stabil bleibt.

### `boundaries[]` — die Angrenzungsmatrix

Analog `IfcRelSpaceBoundary` 2nd Level. Ein Element ist die Bauteil-Definition, eine
Boundary die Raum-Bauteil-Beziehung mit eigener Fläche.

- `space_a` ist **immer** der innere bzw. wärmere Raum. Diese Konvention ist
  verbindlich, sonst kippen Vorzeichen und Fx-Zuordnung.
- `space_b` ist `null` bei `exterior`, Erdreich und `adjacent_building`. Bei
  `internal_unheated` — der Grenze zwischen zwei unbeheizten Räumen innerhalb der
  Akte — ist er dagegen **Pflicht**: das ist eine innere Grenze. Sie ist nie
  bilanzrelevant und wird nur für die vollständige Topologie mitgeführt. Welche
  Art einen Gegenraum braucht, steht im Katalog (`space_b_required`), nicht im Code.
- Getrennte Flächen für Bilanz (`area_18599`) und Heizlast (`area_heizlast`) — die
  Heizlast rechnet raumweise und mit anderem Maßbezug.
- `measurement_reference` folgt im Regelfall deterministisch aus der Angrenzungsart.
  Der dritte Wert `clear_structural` (lichtes Rohbaumaß) ist die Ausnahme: ein
  **Übergangszustand** für Flächen, deren Umrechnung noch aussteht. An einer
  bilanzrelevanten Fläche meldet der Validator `MEASUREMENT_CLEAR_RELEVANT` und
  sperrt `calc_ready` — die Hüllfläche wäre sonst zu klein gerechnet.
- Geometrie als `z_range` (Regelfall) oder `polygon` (Giebel, Schrägen), in
  2D-Koordinaten der Bauteilebene.

**Split-Regeln:** bei Raumwechsel auf der Gegenseite, bei Wechsel der Angrenzungsart
(Pflicht — Hanglage, teilüberdeckendes Nachbargebäude) und optional bei Materialwechsel.

DIN 18599 rechnet auf **Gruppen**-, die Heizlast auf **Boundary**-Ebene.

### `zone_memberships[]` — Mehrfachzugehörigkeit

Ein Raum gehört gleichzeitig einer thermischen Zone, einer Wohneinheit und ggf. einer
Lüftungs-, Brandschutz- oder Akustikzone an. Die Zugehörigkeit steht **nur am Raum** —
`zones[]` führt keine Mitgliederliste. Eine Kante, eine Richtung, keine
widersprüchliche Doppelpflege.

### Orientierung

Alle `orientation`-Werte im Sidecar sind **geografische Azimute** (0° = Nord, im
Uhrzeigersinn). `meta.azimuth_reference` ist ein `const: "geographic"` — eine
Wahlmöglichkeit hier würde stillschweigend falsche Solareinträge erzeugen.

Die Korrektur passiert einmalig beim Export:

```
azimuth_geo = (azimuth_projekt + meta.true_north_offset_deg) mod 360
```

Positiver Offset = gegen den Uhrzeigersinn (empirisch bestätigt, Revit 2026).

---

## 4. Norm- und Katalogstände

`meta.norm_editions{}` setzt den projektweiten Default je Norm-Teil. **Referenzen
bleiben ohne Editions-Suffix stabil** — kein `"NWG_01@2018-09"`.

> **GEG bindet datiert DIN V 18599:2018-09.** Das ist die Nachweis-Edition.
> 2025-10 (DIN/TS) ist im Schema vorbereitet, aber erst mit der GEG-Novelle scharf.

Reproduzierbarkeit auf zwei Ebenen:

| | Feld | Zweck |
|---|---|---|
| Referenz | `meta.catalogs[]` | welcher Katalogstand wurde verwendet |
| Kopie | `zones[].used_profile_values` | welche Werte konkret, mit `norm_cell` je Wert |

Die Kopie bleibt nachvollziehbar, auch wenn der Katalogstand nicht mehr beschaffbar
ist. Format und Overlay-Mechanik: [`docs/v4/KATALOG_FORMAT.md`](v4/KATALOG_FORMAT.md).

---

## 5. Validierungsstufen

Aufsteigend, jede setzt die vorherige voraus:

| Stufe | Bedeutung |
|---|---|
| `draft` | Strukturell gültig gegen das JSON-Schema |
| `enriched` | Fachdaten vollständig — Raumtypen, Zonen, Konstruktionen aufgelöst |
| `geometry_ok` | Angrenzungen vorhanden, Flächen und Volumina plausibel |
| `balanced` | Hüllfläche, Ve und NGF innerhalb der Toleranzen |
| `calc_ready` | Alle Katalogwerte aufgelöst, rechenbar |

**Toleranzen stehen NICHT im Schema.** 3 % Hüllflächenabgleich, 10 % Ve, 15 % NGF sind
Validator-Konstanten (`ruleset_version`) — Auslegungssache, die sich ohne Formatbruch
ändern darf.

**Beta:** alle Stufen-Checks sind Warnungen, keine Blocker. Scharfschaltung später.

```bash
python3 tools/dwe_validate.py examples/v4.0/beispiel1/energy.din18599.json \
    --manifest examples/v4.0/beispiel1/manifest.json
```

Referenz-Container: [`examples/v4.0/beispiel1/`](../examples/v4.0/beispiel1/).
Er steht auf `balanced` — `boundaries[]` ist synthetisch gefüllt (Skript
[`scripts/build-example-beispiel1.py`](../scripts/build-example-beispiel1.py)),
bis die Revit-Pipeline (Stufe 2d) die echte Angrenzungsmatrix liefert.
`calc_ready` blockiert am gitignored Normwerte-Overlay
(`catalog/values/adjacency_types.2018-09.values.json` u. a. — aus eigener
Normlizenz bereitzustellen). Ein Zwischenstand, kein Fehler.

---

## 6. Lossy Consumers

Nicht jedes Zielsystem kann alles abbilden, was im Container steht. Das ist
eingeplant — aber es gibt Regeln, damit ein Roundtrip nichts zerstört.

### Externe, verlustbehaftete Consumer

Ein Consumer, der die vollständige Raumtopologie nicht abbilden kann, bekommt eine
**Gruppen-Aggregation**: je `element_group` eine Bauteilzeile mit Fläche, U-Wert und
Orientierung, aufgeteilt nach Angrenzungsart (`aggregates.by_adjacency[]`). Ein
produktspezifischer Adapter definiert die konkrete Abbildung.

**Was den Roundtrip nicht überlebt:**

| Struktur | Grund |
|---|---|
| `boundaries[]` | Das Zielsystem hat kein Gegenstück zur Raum-Bauteil-Beziehung |
| `rooms[]` mit `zone_memberships[]` | Zonen ja, Räume darunter nein |
| `geometry.polygon` | Nur Flächensummen, keine Umrisse |
| `element_groups[].member_elements[]` | Kein Bezug ins Autorensystem |

> ### Die eine harte Regel
>
> **Ein verlustbehafteter Re-Import überschreibt NIEMALS `boundaries[]` oder `element_groups[]`.**
>
> Er darf U-Werte, Konstruktionen, Anlagentechnik und `output` aktualisieren. Die
> Topologie stammt aus dem autoritativen Geometrie-/Anreicherungsprozess und ist dort
> neu zu erzeugen — aus einem verlustbehafteten Consumer ist sie **nicht
> rekonstruierbar**. Wer sie überschreibt, zerstört
> Daten, die niemand zurückholen kann.

Praktisch: ein Re-Import ist ein **Merge auf Feldebene**, kein Ersetzen des `input`-Astes.
`meta.source.origin` dokumentiert, woher der jeweilige Stand kommt.

### DWEapp

Konsumiert den vollen Sidecar und generiert seine TypeScript-Typen daraus. Felder, die
DWEapp nicht kennt, dürfen beim Speichern **nicht verloren gehen** — der Standard ist
Autorität, die App arbeitet mit `passthrough`.

Der Umstiegsstand ist offen: [`docs/v4/TICKET_dweapp_cutover.md`](v4/TICKET_dweapp_cutover.md).

### IFC-Konsumenten

Bekommen `model.ifc` und ignorieren das Sidecar. `construction_ref` und `dwe_uid`
reisen als **Custom-Psets** mit — ohne `Pset_`-Präfix, das ist buildingSMART
vorbehalten. Das Manifest erzwingt das über ein `not: {pattern: "^Pset_"}`.

---

## 7. Was v4.0 noch nicht kann

Ehrliche Lücken, keine Absichtserklärungen:

- **Wärmebrücken:** nur `boundaries[].edges[]` als Hook, darf leer bleiben. v1 rechnet
  pauschal über `element_groups[].delta_u_wb`.
- **Verschattung:** `shading`-Objekt vorhanden, v1 arbeitet mit dem Default Fs = 0,9.
  `source: "computed"` ist vorgesehen, aber nicht belegt.
- **Erdreich-Fx:** v1 vereinfacht 0,6 (Fußnote a zu Tabelle 6). Die **Eingangsgrößen**
  für B'/Rf sind mit W1 da — `building.ground_geometry` als Gebäude-Aggregat und
  `boundaries[].ground` je Fläche (bei Widerspruch gewinnt die Fläche). Die
  **Auflösung** der Matrix fehlt weiterhin, ebenso die Geometrieregeln nach
  DIN V 18599-2 §6.1.4.4 (Reihenbebauung, Teilunterkellerung). Das Format kann die
  Daten transportieren, der Rechenweg steht aus.
- **LCA/Ökobilanz:** vollständig offen. 17 produktiv geschriebene QNG-Pfade nach
  EN-15804-Modulen liegen als Vorlage vor, siehe
  [`docs/v4/QNG_SIDECAR_PFADE.md`](v4/QNG_SIDECAR_PFADE.md).
- **GEG-Referenzwerte:** Struktur und Mapping stehen, die Zahlenwerte fehlen.
- **Bogenwände:** der Fingerprint erzeugt über die Sehnen-Normale Einzelgruppen. Für
  v1 akzeptiert und im Schema nicht verbaut.

---

## 8. Verwandte Dokumente

| Thema | Datei |
|---|---|
| Katalog-Format und Overlay-Mechanik | [`v4/KATALOG_FORMAT.md`](v4/KATALOG_FORMAT.md) |
| Katalog-Bestandsanalyse (Vorgeschichte) | [`v4/KATALOG_BESTANDSANALYSE.md`](v4/KATALOG_BESTANDSANALYSE.md) |
| Offene Normprüfungen | [`v4/PRUEFLISTE_normpruefung.md`](v4/PRUEFLISTE_normpruefung.md) |
| DWEapp-Umstieg | [`v4/TICKET_dweapp_cutover.md`](v4/TICKET_dweapp_cutover.md) |
| QNG-Pfade und v4.0-Deckung | [`v4/QNG_SIDECAR_PFADE.md`](v4/QNG_SIDECAR_PFADE.md) |
| Ursprungs-Handoff (Design-Entscheidungen) | [`v4/HANDOFF-schema-v4-greenfield.md`](v4/HANDOFF-schema-v4-greenfield.md) |
