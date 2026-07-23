# HANDOFF: Schema v4.0 Greenfield

**An:** Claude Code Session am Repo `github.com/DWEBeratungGmbH/din18599-ifc`
**Von:** Workshop- und Test-Session mit Sebi (claude.ai, Juli 2026)
**Auftrag:** Entwurf des Schema v4.0 als vollständige .dwe-Container-Spezifikation — Greenfield, NICHT als Diff auf v3.1.

> **Hinweis zur Ablage (21.07.2026):** Übertragung des Original-Handoffs ins Repo,
> Zeichenkodierung korrigiert (das Original kam mit defekten Umlauten an). Inhaltlich
> unverändert. Zwei Angaben haben sich nach der Übergabe geändert und sind in
> [FEEDBACK-Abschnitten](#nachtraege-nach-uebergabe) am Ende ergänzt statt im Text
> überschrieben.

---

## 1. Kontext in drei Sätzen

INDICAMUS baut eine Pipeline **Revit 2026 → Dynamo (Anreicherung + Export) → .dwe-Datei (IFC4 + Sidecar JSON) → DWEapp-Gebäudeakte → EVEBI**. Das bestehende Sidecar-Schema v3.1 (`schema/v3.1-complete.json`) kann die neue Raum-Topologie (Angrenzungsmatrix, Bauteilgruppen, Mehrfach-Zonen) nicht abbilden. Alle Design-Entscheidungen sind in einem Workshop gefallen und die kritischen Revit-Annahmen wurden empirisch validiert — dieses Dokument ist die verbindliche Spec-Grundlage.

**Wichtig:** v3.1 bleibt unangetastet in Betrieb (Parser IFC/EVEBI laufen weiter dagegen). v4.0 wird parallel entworfen; Parser-Anpassung ist ein SPÄTERES Arbeitspaket. Kein Migrationsscript als Release-Pflicht.

---

## 2. Die .dwe-Container-Spezifikation (Zielbild)

v4.0 spezifiziert nicht nur das Sidecar, sondern den gesamten Container:

```
projekt.dwe (ZIP)
├── manifest.json        → Container-Manifest (NEU, Teil der Spec)
├── model.ifc            → IFC4 (ADD2), Best-Effort-SpaceBoundaries,
│                          construction_refs als Custom-Psets (KEIN Pset_-Prefix!)
├── energy.din18599.json → Sidecar v4.0 → SOURCE OF TRUTH für alle
│                          energetischen Daten
└── attachments/         → optional: Fotos, Nachweise, PDFs
```

**manifest.json** trägt: Format-Version, Inhaltsverzeichnis, Checksummen (Konsistenzprüfung IFC↔Sidecar über GUIDs), `validation_level` (siehe §6), Erstellungszeitpunkt, erzeugendes Tool.

**Grundprinzip Source of Truth:** Die Angrenzungsmatrix (`boundaries[]`) wird in Dynamo berechnet und lebt im Sidecar. IFC-SpaceBoundaries sind Best-Effort-Beigabe (Revit-Export notorisch lückenhaft — in Test-IFCs: null Einträge), niemals Rechengrundlage.

---

## 3. Gelockte Design-Entscheidungen (Workshop)

Diese Entscheidungen sind final — nicht neu diskutieren, sondern umsetzen:

### E1 — `input.boundaries[]` als eigenes Top-Level-Array

Analog IfcRelSpaceBoundary2ndLevel. Element = Bauteil-Definition; Boundary = Raum-Bauteil-Beziehung mit eigener Fläche. Felder je Boundary: `id`, `element_group_ref`, `space_a` (innen/wärmere Zone — Konvention!), `space_b` (außen/Nachbar), `adjacency_type`, `fx`, `area_18599`, `area_heizlast`, `orientation` (Geo-Azimut!), `tilt`, `geometry`, `openings[]`, `shading` (optional), `relevant_18599`, `relevant_heizlast`.

### E7 — Boundary-Splits nach IFC-Regeln + Polygon-Geometrie

Split bei: (1) Raumwechsel auf Gegenseite, (2) Wechsel der Angrenzungsart (PFLICHT — Hanglage, teilüberdeckendes Nachbargebäude), (3) optional Materialwechsel.

```json
"geometry": {
  "type": "z_range" | "polygon",
  "z_from": 0.0, "z_to": 4.2,
  "polygon": [[0,0],[8.2,0],[8.2,2.8],[4.1,4.9],[0,2.8]]
}
```

Polygon in 2D-Koordinaten der Bauteilebene (für Giebel-Schräggrenzen). Fläche = Polygonfläche.

### E2 — `zone_memberships[]` ersetzt feste Refs (sauberer Schnitt)

```json
"zone_memberships": [
  { "zone_type": "thermal", "zone_id": "Z1" },
  { "zone_type": "dwelling_unit", "zone_id": "WE01" },
  { "zone_type": "ventilation", "zone_id": "LZ01" }
]
```

zone_types: `thermal` (Pflicht bei konditioniert), `dwelling_unit` (Pflicht), optional `ventilation`, `fire`, `acoustic`, custom. Plus `zone.parent_zone_ref` für untergeordnete NWG-Profile (16/18/19/20/41 erben Betriebszeiten der Eltern-Zone).

### E3 — `norm_edition` als separates Feld

`meta.norm_editions{}` als projektweiter Default pro Norm-Teil; Override pro Kennwert nur in Ausnahmen. Refs bleiben stabil (KEIN "@2018-09"-Suffix). **GEG bindet datiert DIN V 18599:2018-09** — das ist die Nachweis-Edition. 2025-10 (DIN/TS) als parallele Katalog-Ausgabe vorbereiten (Scharfschaltung bei GEG-Novelle).

### E4 — `openings[]` in der Boundary + `openings_index[]` als Sicht

Fenster/Türen: Abzug von der opaken Fläche UND eigene Hüllfläche.
`opening_type`-Enum: `window`, `roof_window` (Messregel: Blendrahmen-Außenmaß!), `skylight`, `fixed_glazing`, `curtain_wall`, `door`, `glazed_door` (thermisch wie Fenster!), `garage_door`, `special` (description-Pflicht). `openings_index[]` = read-only Aggregat-Sicht, Validator prüft Konsistenz.

### GEG-Referenzgebäude

`catalog/geg_reference_building.json`, versioniert nach `geg_edition`. Deterministisches Mapping (keine Pflichtfelder am Objekt):

```
window/glazed_door → Zeile 2 | roof_window → Zeile 3 | skylight → Zeile 4
door/garage_door → Zeile 5 | Wand+exterior → 1.1 | Wand+ground/unheated → 1.2
Dach+exterior → 1.3
```

### E8 — element_groups[] als berechnete Zwischenebene (KERN-INNOVATION)

```
element_groups[]     → das 18599-Bauteil (W01 "Außenwand Süd")
  ├── plane-Fingerprint: {normal_x, normal_y, dist_m}  (PROJEKTSYSTEM!)
  ├── wall_type, construction_ref
  ├── member_elements[]   → Revit-IDs, bei jedem Lauf NEU berechnet
  └── Aggregate (Fläche, Länge, adjacency-gruppiert)
boundaries[]         → Kinder: Teilfläche je Raum, ref auf Gruppe
```

Gruppierung: Koplanarität = gleiche Normale (±1°/gerundet 2 Dezimalen) + gleicher Ebenenabstand (±2 cm) + gleicher Bauteiltyp. DIN 18599 rechnet auf Gruppen-, Heizlast auf Boundary-Ebene. **Empirisch validiert** (siehe §5). DWE-Fachdaten hängen an der GRUPPE, nie an der Instanz.

### E9 — Validierungsstufen (Beta)

`draft → enriched → geometry_ok → balanced → calc_ready`. Toleranzen (3% Hüllflächenabgleich / 10% Ve / 15% NGF) als Validator-Konstanten, NICHT im Schema. Rollout erst Warnung, dann Blocker. Neuer Check aus Testphase: „Toposolid mit Raumbegrenzung=aktiv → Warnung".

### E5 — Zweistufiges Katalog-Modell + Werte-Strategie

- **Kern-Kataloge (offenes Repo):** nur norm-notwendige STRUKTUR (Raumtyp-Enum, adjacency_types+Fx-Logik, Profil-Struktur, GEG-Zeilen-Struktur). Werte-Felder als Platzhalter mit Norm-Referenz („siehe DIN V 18599-10:2018-09, Tab. 7, Sp. 19") + Befüll-Template.
- **Erweiterungs-Kataloge (nur DWEapp):** Bauteilaufbauten, ÖKOBAUDAT, Nutzungsdauern. Gleiches Schema-Muster. `catalog_ref` + `catalog_source: "core"|"dweapp"`.
- **Werte-Strategie (Option B + Snapshot):** DIN-Zahlenwerte leben NUR im privaten DWEapp-Katalog (versioniert). Rechen-Engine lädt zur Laufzeit. Bei Berechnung/Einfrieren: verwendete Werte als Snapshot ins Sidecar (`used_profile_values` mit source, norm_edition, snapshot_date) — bitemporales Muster analog offerSnapshot/WI-11.

### C4 — RECHTLICHER BLOCKER (nicht von Claude Code lösbar, aber beachten)

`catalog/din18599_usage_profiles.json` liegt aktuell MIT Normwerten im öffentlichen Repo. DIN-Tabellenwerte sind urheberrechtlich geschützt. **Beim v4.0-Entwurf: keine neuen Normwerte-Dateien ins öffentliche Repo committen.** Struktur ja, Zahlenwerte nein (Platzhalter + Referenz). Sebi klärt Datenlizenz mit DIN Media.

---

## 4. adjacency_type-Enum (final, DIN V 18599-2:2018-09)

| Code | Norm | Fx | Offset-Regel |
|---|---|---|---|
| `exterior` | T5-Z1 | 1,0 | Außenmaß (volle Stärke inkl. Dämmung+Putz) |
| `attic_uninsulated` | T5-Z2 | 0,8 | Außenmaß der beheizten Zone |
| `unheated` | T5-Z3 | 0,5 | Außenmaß der beheizten Zone |
| `low_heated` | T5-Z4 | 0,35 | Achsmaß (Mitte ROHBAU) — NUR wenn Nachbar NICHT bilanziert |
| `glass_single/double/triple` | T5-Z5–7 | 0,8/0,7/0,5 | Außenmaß |
| `ground_slab` | T6-Z1–10 | var. (vereinfacht 0,6) | Außenmaß |
| `ground_basement_heated` | T6-Z11 | var. | Außenmaß |
| `ground_basement_unheated` | T6-Z12–20 | var. | — |
| `floor_suspended` | T6-Z21 | 0,9 | — |
| `other_zone` | — | aus Δθ | Achsmaß (Mitte Rohbau) |
| `same_zone` | — | 0 (nur Heizlast!) | Achsmaß |
| `adjacent_building` | — | 0 (adiabat) | Achsmaß Grundstücksgrenze |

**Validierungsregel (Pflicht):** `low_heated` ↔ `other_zone` schließen sich pro Bauteil aus. Wenn Nachbarraum mit heating_status=low_heated einer bilanzierten Zone zugehört → MUSS other_zone sein. Fx=0,35 ist ERSATZ für fehlende Nachbarzonen-Bilanz, kein Zusatz.

**Maßbezüge (DIN 18599-1 §8):** Horizontal: Außenmaß bei exterior/unheated (Außenmaß der beheizten Zone), Achsmaß (Mitte Rohbau-Kernschicht!) zwischen beheizten Zonen. Vertikal: OK Rohdecke → OK Rohdecke; Ausnahme oberer Abschluss: OK oberste wärmetechnisch wirksame Schicht. Fenster: lichtes Rohbaumaß (Dachfenster: Blendrahmen-Außenmaß).

**Relevanz-Flags:** `same_zone` → relevant_18599=false, relevant_heizlast=true. Alle anderen: beides true (other_zone für 18599 nur bei Δθ>4K).

---

## 5. Empirisch validierte Annahmen (Revit-2026-Testphase, Juli 2026)

Testmodell „Beispiel1": 22 Räume, 28 Wandinstanzen, 2 Geschosse, 3 Wandtypen, Toposolid.

| # | Annahme | Ergebnis |
|---|---|---|
| A1 | Room-Boundary-Segmente liefern Bauteil + Nachbarraum (GetRoomAtPoint jenseits der Wand) | OK — 102 Segmente, 0 ohne Element, 72 mit Nachbar |
| A2 | Koplanaritäts-Fingerprint gruppiert korrekt | OK — 28 Instanzen → 13 Gruppen, 12 geschossübergreifend |
| A3 | Kernschicht aus CompoundStructure (GetFirst/LastCoreLayerIndex) | OK (einschichtige Typen: Kern=Gesamt, ok) |
| A4 | Toposolid für Hanglagen-Split greifbar | OK |
| A5 | Ve-Solid-Union (SpatialElementGeometryCalculator + BooleanOperationsUtils) | OK — 22 Räume in 0,06 s |
| A6 | True-North-Offset via ActiveProjectLocation.GetProjectPosition(XYZ.Zero).Angle | OK — +35° = gegen Uhrzeigersinn |
| E8 | Fingerprint überlebt Löschen+Neuzeichnen | OK — **Beweiszeile: Mitglieder −[2521171] +[2527976], Gruppe stabil** |

**Befunde mit Schema-/Validator-Konsequenz:**

1. **True-North-Drehung ändert Fingerprints NICHT** → Fingerprint bleibt im Projektsystem, Geo-Korrektur NUR beim Export: `azimuth_geo = (azimuth_projekt + true_north_offset) mod 360`, positiver Offset = gegen Uhrzeigersinn. `meta.true_north_offset_deg` + `meta.azimuth_reference: "geographic"` → alle exportierten Azimute sind bereits korrigiert.
2. **Toposolid mit „Raumbegrenzend" verfälscht still Raumvolumina** (−23,6 m³ / −2,9% im Test, 12 EG-Räume) → Revit-Raumvolumina sind Plausibilitäts-Vergleich, NIE Rechenquelle. Validator-Check ergänzen.
3. **Revit-IDs sind wertlos als Fachdaten-Anker** (auch UniqueID instabil bei Copy/Monitor, Workset-Binding, Löschen+Neuzeichnen) → Gruppen-Fingerprint für Bauteile, DWE_UID (Shared Parameter) für Räume, JSON-Snapshot + Diff-Report als Sicherungsnetz.

**Technik-Learnings für Dynamo/Stufe 2 (PythonNet3 in Revit 2026):**

- Systematische „property cannot be read"-Fälle: `w.WallType`, `w.Orientation`, `location.Curve`. Workaround-Muster: `doc.GetElement(w.GetTypeId())` bzw. universeller `P(obj, name)`-Helper mit `get_Xxx()`-Fallback. Normale aus LocationCurve-Endpunkten berechnen statt Orientation-Property.
- Dynamo cached: Modell-Änderungen triggern keine Neuberechnung des Python-Nodes → Dynamo Player als Standard-Ausführungsweg.
- Zwei validierte Referenz-Skripte existieren (Stufe-1-Testskript v1.3, Diff-Tool v1.0) — bei Sebi, als Basis für Stufe 2.

---

## 6. Konkrete Deliverables der Greenfield-Session

Vorschlag Reihenfolge (mit Sebi abstimmen):

1. **`schema/v4.0/manifest.schema.json`** — Container-Manifest
2. **`schema/v4.0/sidecar.schema.json`** — das Sidecar komplett:
   - `meta` (norm_editions{}, true_north_offset_deg, validation{}, ve_method)
   - `input.building` / `storeys[]` / `rooms[]` (mit zone_memberships[], room_type, theta_heizlast_standard + _override [Warnung >3K, beide Werte mitführen], ventilation_function, heating_status: heated|unheated|low_heated, dwe_uid)
   - `input.zones[]` (usage_profile_ref + norm_edition, parent_zone_ref, used_profile_values-Snapshot)
   - `input.element_groups[]` (fingerprint, construction_ref, member_elements[])
   - `input.boundaries[]` (siehe §3/E1, inkl. geometry, openings[], shading-Hook, edges[]-Hook für ψ später — leer erlaubt)
   - `input.constructions[]` (voll ausgeschrieben = offline-fähig, origin_ref, Dedup-Konvention)
   - `openings_index[]`, `output`, `scenarios`, `funding`, `roadmap` (Struktur aus v3.1 übernehmen wo passend — Greenfield heißt frei entwerfen, nicht alles anders machen)
3. **`catalog/`-Strukturen — NICHT direkt bauen, sondern zweistufig nach §8:** zuerst Bestandsanalyse + Anforderungsdokument, Feedback von Sebi, dann erst Format-Entwurf. (Inhaltlicher Umfang zur Orientierung: room_types ~55 Typen mit 3-Normen-Mapping, adjacency_types mit Fx-Logik, geg_reference_building geg_edition-versioniert, usage_profiles norm_edition-dimensioniert — Details in §8.1)
4. **Beispiel-Sidecar** (validierend) auf Basis des Testmodells „Beispiel1" (22 Räume, 13 Gruppen) — oder FL38 als Referenzfall
5. **Validator-Grundgerüst** mit den 5 Leveln (Checks als Beta/Warnung)
6. **`docs/DWE_CONTAINER.md`** — Spec-Dokumentation inkl. „Lossy Consumers"-Abschnitt (EVEBI erhält Gruppen-Aggregation, Raumtopologie überlebt Roundtrip nicht; EVEBI-Re-Import überschreibt NIE boundaries[]/element_groups[])

---

## 7. Offene Punkte (nicht blockierend, im Hinterkopf behalten)

- **C4/DIN-Lizenz:** Sebi klärt mit DIN Media. Bis dahin: keine Werte ins Public-Repo.
- **API-Topologie Revit-Plugin → DWEapp:** vertagt auf Plugin-Sprint mit Timo. Vorentscheidung: kein dritter Service, Schreibpfade nur über tRPC/Upload-Flow.
- **Wärmebrücken (ψ):** nur `edges[]`-Hook vorsehen, v1 pauschal ΔU_WB.
- **Verschattung:** `shading`-Objekt mit source: default|manual|computed, v1 default Fs=0,9.
- **Erdreich-Fx:** v1 vereinfacht 0,6 (Fußnote a, T6); volle B'/Rf-Matrix später. B'=Ag/(0,5·P) — Geometrie-Regeln DIN V 18599-2 §6.1.4.4 beachten (Reihenbebauung, Teilunterkellerung).
- **Bogenwände:** Fingerprint via Sehnen-Normale → Einzelgruppen. Akzeptiert für v1, im Schema nicht verbauen.
- **Ve-Berechnung:** `ve_method: "solid"|"approximation"` — Methode immer dokumentieren.

---

## 8. Katalog-Spezifikation — ZWEISTUFIGES VORGEHEN (Analyse zuerst!)

**Der Katalog-Feinentwurf ist bewusst NICHT vorentschieden.** Ablauf: (1) Claude Code analysiert den Bestand und erstellt eine Anforderungs-/Ist-Analyse, (2) Sebi gibt Feedback, (3) erst DANN wird das Katalog-Format gemeinsam am konkreten JSON erarbeitet. Nicht direkt ein Katalog-Schema festschreiben.

### 8.1 Schritt 1 — Bestandsanalyse (erster Arbeitsauftrag)

Analysiere und dokumentiere kompakt (eine MD-Datei als Diskussionsgrundlage):

**Im din18599-ifc-Repo:**

- `catalog/din18599_usage_profiles.json` — Ist-Struktur: Welche Felder, wie referenziert (zone.usage_profile_ref), welche Werte enthalten (→ C4-Betroffenheit markieren), Versionierungs-Ansatz vorhanden ja/nein
- Alle weiteren Katalog-artigen Dateien im Repo (Klimadaten? Materiallisten? Enums im Schema selbst?)
- Wie konsumieren die bestehenden Parser (IFC, EVEBI) und der Validator die Kataloge heute — welche Zugriffsmuster müssen weiter funktionieren bzw. sind Vorbild
- Welche Enums/Referenztabellen leben aktuell IM Schema v3.1 statt als Katalog (din_code-Liste, boundary_condition etc.) — Kandidaten für Auslagerung?

**Anforderungen aus diesem Handoff konsolidieren:**

- Benötigte Kataloge sammeln: room_types (~55 Einträge, 3-Normen-Mapping), adjacency_types (Fx-Logik + Norm-Zeilen-Ref), usage_profiles (norm_edition-dimensioniert: 2018-09 mit 42 + 2025-10 mit 43 Profilen), geg_reference_building (geg_edition-dimensioniert), perspektivisch Bauteilaufbauten/ÖKOBAUDAT (DWEapp-seitig)
- Pro Katalog klären: Welche Felder sind Struktur (öffentlich ok), welche sind Normwerte (C4-kritisch), welche sind DWE-eigene Zusätze (öffentlich ok, z.B. Offset-Regeln, Vorschlagslogik)
- Versionierungs-Anforderungen: norm_edition, geg_edition, valid_from/to, catalog_version — was braucht welcher Katalog wirklich (nicht pauschal alles überall)

**Offene Design-Fragen explizit auflisten** (für Sebis Feedback), mindestens:

- Overlay-Mechanismus für Werte: Struktur-Datei (public, value: null + Norm-Referenz) + Values-Overlay (privat: DWEapp oder lokale Nutzer-Datei aus eigener Normlizenz) → Merge zur Laufzeit. Validator: ohne aufgelöste Werte kein `calc_ready`, Meldung „Werte-Katalog fehlt — DWEapp verbinden oder Overlay befüllen". → Ist dieser Mechanismus so gewollt? Eine Overlay-Datei pro Norm oder eine gesamt?
- Ein generisches Katalog-Rahmenformat für ALLE Kataloge (ein Meta-Schema) vs. individuelle Schemata pro Katalog?
- Wo leben die Kern-Kataloge physisch: im Schema-Repo unter catalog/ oder eigenes Repo?
- Wie referenziert das Sidecar Katalogstände reproduzierbar (catalog_version im Snapshot?)
- room_types: flache Liste oder getrennt WG/NWG?

### 8.2 Schritt 2 — Feedback-Schleife

Analyse-Dokument an Sebi, Feedback abwarten. ERST DANACH Katalog-Schemata entwerfen. Die Deliverables aus §6 Punkt 3 stehen solange zurück; manifest + sidecar (§6 Punkt 1–2) können unabhängig davon beginnen — Katalog-Referenzfelder (`catalog_ref`, `catalog_source`) dort aber schon vorsehen.

---

## 9. Bestehende Repo-Artefakte (Orientierung)

- `schema/v3.1-complete.json` — aktuelles Schema (2229 Zeilen), Referenz für bewährte Teile (constructions/sequences-Modell, window_constructions mit Ug/Uf/g/ψ, funding, roadmap)
- `schema/v3.2-complete.json` — existiert, ist aber nur v3.1-Kopie mit geändertem Title → kann zugunsten v4.0 verworfen/ignoriert werden (mit Sebi klären)
- `catalog/din18599_usage_profiles.json` — v1.0 auf 2018-09-Basis, MIT Werten (C4-Problem!)
- Parser (IFC, EVEBI) — laufen gegen v3.1, NICHT anfassen

**Arbeitsweise mit Sebi:** iterativ, kritisch, pragmatisch. Design-Entscheidungen am konkreten JSON treffen, nicht abstrakt. Er reviewt alles selbst. Bei Unsicherheit: fragen statt annehmen — aber die in §3 gelockten Entscheidungen gelten.

---

## Nachträge nach Übergabe

Diese Punkte weichen vom Text oben ab. Der Text bleibt unverändert, damit die
Entscheidungsgrundlage nachvollziehbar bleibt.

### Korrekturen aus der Bestandsanalyse (21.07.2026)

Belegt in [KATALOG_BESTANDSANALYSE.md](KATALOG_BESTANDSANALYSE.md) §7:

1. **§1 „Parser laufen weiter gegen v3.1"** trifft nicht zu. `ifc_parser_v3.py` emittiert
   `version: "2.3.0"`, `sidecar_generator.py` sogar `url: ".../schema/v1"`. Kein Parser
   erzeugt v3.x. Einziger echter v3.x-Konsument ist DWEapp — und der generiert seine
   TS-Typen aus **v3.0**.
2. **§9 „v3.2 ist nur v3.1-Kopie"** trifft nicht ganz zu. Zwei echte Felder in
   `funding_entry` (`step_refs[]`, `status_erweitert`), die DWEapp produktiv schreibt,
   plus zwei Defekte: `schema_info.url`/`version`-Pattern nie hochgezogen (das Schema
   lehnte seine eigene Version ab) und `step_refs[]` verwies auf
   `scenarios[].steps[].id`, was in keiner Version existierte. Beide Felder sind in
   v4.0 übernommen, `steps[]` dort erstmals als echte Struktur.
3. **C4** ist milder als angenommen: die benannte Profil-Datei ist bereits weitgehend
   wertfrei (43 NWG-Profile ohne jeden Parameter). Dafür lagen 605 KB norm-abgeleitete
   Symbol-/Index-/Glossar-Dateien unbewertet im öffentlichen Repo — seit 21.07. nach
   `catalog-private/norm-derived/` verschoben.

### Aktualisierte Modelldaten „Beispiel1" (Feedback 21.07.2026)

§5 nennt 22 Räume. Der aktuelle Modellstand ist:

- **23 Räume** (Garage als Nebenfläche ergänzt)
- **2 WE als Maisonetten**, je 11 Räume über zwei Ebenen, n_WE = 2
- **Wohnfläche 240,96 m²**, `true_north_offset_deg` = 35,0, 1 Toposolid
- 13 element_groups mit finalen Namen: `AW-NO-01..03`, `AW-SO-01..05`,
  `IW-WE1-01/02`, `IW-WE1-WE2-01`, `IW-WE2-01/02`

Umgesetzt in [`examples/v4.0/beispiel1/`](../../examples/v4.0/beispiel1/).

### room_types: Quellenlage

§6 Punkt 3 und §8.1 nennen „~55 Typen mit 3-Normen-Mapping". Eine Liste dazu existiert
im Handoff nicht — §5 enthält die Revit-Testbefunde, keine Raumtypen. Der Katalog wurde
deshalb aus zwei belegten Quellen gebaut: 43 NWG-Typen 1:1 aus den Nutzungsprofilen und
18 WG-Typen aus der praxisvalidierten RAUMTYPEN-Tabelle der Revit-Pipeline
(nachgeliefert im Feedback vom 21.07.). `din_277_category` bleibt offen.

### Katalog-Entscheidungen

Die sechs offenen Design-Fragen aus §8.1 sind entschieden — siehe
[KATALOG_FORMAT.md](KATALOG_FORMAT.md). Abweichend von §E5 ist `adjacency_types`
**vollständig öffentlich inklusive Fx-Werten**: zwölf Einzelfakten, kein Datenbankwerk,
und die Boundary-Validierung als Grundfunktion darf nicht am Overlay hängen.
