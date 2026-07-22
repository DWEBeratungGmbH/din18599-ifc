# Changelog

Alle wichtigen Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt folgt [Semantic Versioning](https://semver.org/lang/de/).

---

## [Unreleased] - Schema v4.0 (.dwe-Container)

### Added

- **`schema/v4.0/manifest.schema.json`** — Container-Manifest der `.dwe`-Datei (ZIP):
  Inhaltsverzeichnis, SHA256-Checksummen, GUID-Konsistenzprüfung IFC↔Sidecar,
  Validierungsgrad. Einzige Datei, die ein Konsument lesen muss, um zu entscheiden
  ob er den Container verarbeiten kann.
- **`schema/v4.0/sidecar.schema.json`** — Sidecar v4.0, Greenfield-Neuentwurf:
  - **`input.boundaries[]`** — Angrenzungsmatrix analog IfcRelSpaceBoundary 2nd Level.
    Wird extern berechnet und lebt im Sidecar; IFC-SpaceBoundaries sind Best-Effort
    und nie Rechengrundlage. Splits bei Raumwechsel, Wechsel der Angrenzungsart
    (Pflicht) und optional Materialwechsel. Geometrie als `z_range` oder `polygon`.
  - **`input.element_groups[]`** — Bauteilgruppen als berechnete Zwischenebene mit
    Koplanaritäts-Fingerprint im Projektsystem. DIN 18599 rechnet auf Gruppen-,
    Heizlast auf Boundary-Ebene. Fachdaten hängen an der Gruppe, nie an der Instanz.
  - **`rooms[].zone_memberships[]`** — Mehrfach-Zonenzugehörigkeit (thermal,
    dwelling_unit, ventilation, fire, acoustic) statt fester Einzel-Refs.
  - **`meta.norm_editions{}`** — Norm-Edition als projektweiter Default je Norm-Teil.
    Referenzen bleiben ohne Editions-Suffix stabil.
  - **`meta.catalogs[]`** + `catalog_ref`/`catalog_source` — reproduzierbare
    Katalogstände; ergänzt durch `zone.used_profile_values`-Snapshot.
  - **`meta.true_north_offset_deg`** + `azimuth_reference: "geographic"` — alle
    exportierten Azimute sind bereits geo-korrigiert, der Fingerprint bleibt im
    Projektsystem.
  - **`meta.ve_method`** — Ermittlungsmethode des beheizten Volumens ist immer zu
    dokumentieren; `room.volume_reported_m3` ist ausdrücklich nur Plausibilitätswert.
  - `adjacency_type`-Enum mit 14 Werten (Fx und Maßbezug im Katalog, nicht im Schema),
    `opening_type`-Enum mit 9 Werten, 5 Validierungsstufen `draft` … `calc_ready`.

- **`schema/v4.0/paths.json`** — generierte Pfad-Whitelist des Sidecars (615 Pfade,
  22 davon abgeleitet). Macht aus der Präfix-Konvention „abgeleitete Pfade nicht
  schreiben" eine prüfbare Liste. Zwei Konsumenten haben denselben Semantikbedarf —
  DWEapps `applyDotPath` und der Python-Export — deshalb liegt das Artefakt im
  Standard-Repo statt in einem der beiden. Erzeugt von `scripts/build-paths.py`,
  per `--check` in der CI verriegelt. Die Semantik kommt aus dem Schema
  (`readOnly`), nicht aus dem Generator.
- **`readOnly: true`** (Draft-07-Standardkeyword) auf `input.openings_index`,
  `element_groups[].aggregates` und `openings[].geg_reference_row`. Vererbt sich
  auf den Teilbaum und ist damit die Quelle für die `readonly`-Spalte in `paths.json`.

### Changed

- **`fingerprint.tolerance.normal_decimals` → `angle_tolerance_deg`.** Rundungs-
  Dezimalen sind kein Toleranzmaß: gleich gerundete Werte trennen zwei Wände schon
  ab rund 0,3°, vereinigen aber nie zwei Wände über eine Rundungsgrenze hinweg. Die
  Regel war nicht transitiv und hatte bei `normal_x ≈ 0` einen Vorzeichen-Kipppunkt.
  Die Gruppierung vergleicht jetzt den Winkelabstand zum Gruppen-Repräsentanten;
  `normal_*`/`dist_m` werden in voller Rechenpräzision serialisiert. `tolerance` ist
  auf `additionalProperties: false` gesetzt — ein Sidecar mit `normal_decimals`
  fällt laut durch, statt lautlos den 1°-Default zu bekommen.
  Kein Versions-Bump: v4.0 ist unveröffentlicht, die Änderung fällt in 4.0.0.
- **`FINGERPRINT_COLLISION`** vergleicht Ebenen über den Winkelabstand statt über
  Gleichheit gerundeter Werte. Die Paar-Toleranz ist das Maximum beider Gruppen
  (sonst hängt der Befund von der Listenreihenfolge ab), `|n_a · n_b|` fängt den
  Kanonisierungs-Kipppunkt mit ab, und die Vorsortierung nach Bauteiltyp und
  `|dist|` hält den Aufwand bei vielen Gruppen im Rahmen. Sechs Grenzfälle sind
  in `tools/test_dwe_validate.py` abgesichert.
- **CI (`catalog-guard.yml`)** — der Schema-Check läuft nicht mehr über zwei hart
  verdrahtete Dateien, sondern über `schema/**/*.schema.json` plus die
  `v*-complete.json`. Bewusst kein `**/*.json`: unter `schema/` liegen auch reine
  Datendateien, bei denen `check_schema` vakuum „ok" sagt. Ergänzt um einen Guard
  auf `v3.0-complete.json` (DWEapp liest sie an vier Stellen) und `v3.1-complete.json`,
  sowie um eine Validierung von `catalog/core/*.json` gegen
  `catalog-envelope.schema.json` — das trifft die `catalog_version`-Falle am realen
  Objekt statt vakuum am Schema.

### Removed

- **Schema v3.2 verworfen.** Es war nie in einem Release dokumentiert und hatte zwei
  Defekte: `schema_info.url`-const und `version`-Pattern (`^3\.1\.\d+$`) wurden nie
  hochgezogen — das Schema lehnte seine eigene Version ab — und `step_refs[]` verwies
  auf `scenarios[].steps[].id`, was in keiner Version existierte. Beide v3.2-Felder
  (`funding_entry.step_refs[]`, `status_erweitert`) sind in v4.0 übernommen, `steps[]`
  dort erstmals als echte Struktur unter `scenarios[]` definiert.
- **v2.1 / v2.2 / v2.3** samt zugehörigen Migrations-Dokumenten nach
  `archive/schema-legacy/` verschoben.

### Notes

- v3.0 und v3.1 bleiben eingefroren in Betrieb, bis DWEapp auf v4.0 umgestellt ist.
  DWEapp generiert seine TS-Typen aus **v3.0** (`scripts/schema-check.mjs`) — diese
  Datei darf bis dahin nicht entfernt werden.
- v4.0 ist bewusst **kein** abwärtskompatibler Diff auf v3.x. Ein Migrationsskript ist
  keine Release-Pflicht; die Parser-Anpassung ist ein eigenes Arbeitspaket.
- Katalog-Format ist noch offen — siehe [docs/v4/KATALOG_BESTANDSANALYSE.md](docs/v4/KATALOG_BESTANDSANALYSE.md).

---

## [3.1.0] - 2026-04-13

### Added

#### Schema v3.1 (abwärtskompatibel zu v3.0)

- **`input.energy_certificate`** — Energieausweis-Daten (Typ `VERBRAUCH` oder `BEDARF`),
  alle Felder optional. `source` = `MANUAL_ENTRY | PDF_UPLOAD | NEXTCLOUD_LINK` für
  Audit-Trail (typischer Fall: Energieberater tippt Werte aus einem PDF ab).
- **`input.targets`** — freie Zielwerte (`FINAL_ENERGY_KWH_M2A`, `PRIMARY_ENERGY_KWH_M2A`,
  `CO2_KG_M2A`, `HEATING_ENERGY_KWH_M2A`, `OTHER`) mit Jahr und Source-Typ. Gedacht für
  den "nur IFC vorhanden"-Fall, wo noch keine Messwerte existieren.

### Changed

- `schema_info.$id` const + `version` pattern auf v3.1 hochgezogen.

### Migration

Siehe [schema/MIGRATION_v3.0_to_v3.1.md](schema/MIGRATION_v3.0_to_v3.1.md).
Jedes valide v3.0-Sidecar ist auch ein valides v3.1-Sidecar — keine Änderung an
bestehenden Dateien nötig.

---

## [3.0.0] - 2026-04-10

### 🏛️ Gebäudeakte-Release

**Additiv zu v2.3 — jedes valide v2.3-Sidecar ist auch ein valides v3.0-Sidecar.**
Erweitert das Schema um die für die energetische Gebäudeakte nötigen Sektionen
(Dokumente, Förderungen, Sanierungsfahrplan, SLA-Kontext).

### Added

#### Schema v3.0 — neue Top-Level-Sektionen

- **`documents[]`** — Pläne, Nachweise, Fotos, Rechnungen, Förderdokumente als
  Cloud-Links. Nutzt logische `storage_ref`-Pfade, die ein Storage-Resolver-Service
  auf Nextcloud, S3 o.ä. auflöst (Provider-Wechsel = nur Resolver-Config ändern).
- **`funding[]`** — Förderungen (BEG, KfW, BAFA) als Hybrid-Modell: technische
  Zuordnung im Sidecar + `erpnext_ref` zum ERPNext-Datensatz (Source of Truth für
  Finanzen) + `snapshot` mit letztem Sync-Stand (n8n-Workflow).
- **`roadmap`** — Sanierungsfahrplan mit priorisierten Schritten (`steps[]`), inkl.
  geplantem Jahr, Status, Priorität und geschätzten Kosten.
- **`sla_context`** — Brücke zur SLA-Sandbox: abgeleitete Parameter (BGF, WE, BT,
  Gebäudeart) und Mapping von Sidecar-Szenarien auf SLA-Szenarien + Maßnahmen.

#### Neue Definitions

`document`, `funding_entry`, `roadmap_step` — wiederverwendbare Strukturen für die
neuen Sektionen.

#### Datenbank (`database/schema.sql`)

- Statistik-Spalten auf `din18599.sidecars`: `document_count`, `funding_count`,
  `roadmap_step_count` (beim Import befüllt, vermeiden JSONB-Aggregation in Listen).
- Spiegelung der Stat-Felder in `din18599.v_projects_overview`.
- Helper-Funktionen für direkten Zugriff ohne Client-Side-JSONB-Logik:
  - `din18599.get_documents(sidecar_id)`
  - `din18599.get_funding(sidecar_id)`
  - `din18599.get_roadmap_steps(sidecar_id)`
  - `din18599.sum_approved_funding(sidecar_id)`

### Changed

- `schema_info.$id` auf `https://din18599-ifc.de/schema/v3.0/complete`,
  `version` pattern auf `^3\.0\.\d+$`.
- `database/schema.sql` Header auf v3.0, Kommentare aktualisiert.

### Migration

Siehe [schema/MIGRATION_v2.3_to_v3.0.md](schema/MIGRATION_v2.3_to_v3.0.md).

**Datenbank-Hinweis:** Bestehende Datenbanken benötigen ein Migrationsskript
(`ALTER TABLE` für die 3 neuen Statistik-Spalten + `CREATE FUNCTION` für die
Helper). `schema.sql` allein ist nur für frische Deployments autoritativ.

### Notes

- v2.1, v2.2 und v2.3 wurden zwischen v2.0 und v3.0 veröffentlicht, aber nicht im
  CHANGELOG dokumentiert. Siehe Git-History (`git log schema/`) für die Details.

---

## [2.0.0] - 2026-03-27

### 🎉 Major Release - Production Ready

**Vollständige Überarbeitung des Schemas und der Dokumentation**

### Added

#### Schema v2.0
- **LOD-Konzept** (Level of Detail 100-500) für verschiedene Planungsphasen
- **Varianten-Management** (Delta-Modell: Base + Scenarios)
- **Layer Structures** (Schichtaufbauten von außen nach innen)
- **Materials erweitert** (STANDARD + AIR_LAYER nach EN ISO 6946)
- **Wärmebrücken-Typen** (DEFAULT, REDUCED, DETAILED)
- **u_value_override** für manuelle U-Wert-Überschreibung
- **construction_catalog_ref** für Katalog-Referenzen
- **data_quality** Metadaten (geometry, envelope, systems)

#### Kataloge
- **Bundesanzeiger 2020** Katalog (97 U-Wert-Referenzen, BEG-konform)
- Katalog-Schema (`$schema: https://din18599-ifc.de/schema/catalog/v1`)
- 10 Baualtersklassen (bis 1918 bis ab 2010)
- Opake Bauteile (Wände, Dächer, Decken, Bodenplatten)
- Transparente Bauteile (Fenster, Türen)

#### Beispiele
- **LOD 100** - Schnellschätzung (Minimal-Input, Katalog-basiert)
- **LOD 200** - iSFP Bestandsaufnahme (Begehung, Bundesanzeiger)
- **LOD 300** - Sanierungsvarianten (Delta-Modell, Schichtaufbauten)
- **LOD 400** - GEG-Nachweis (Vollständig, Produktdatenblätter)

#### Viewer
- **Beispiel-Auswahl** Dropdown (LOD 100-400)
- **Bauteilliste** mit U-Werten und IFC GUIDs
- **Wärmebrücken-Analyse** (Ø ΔU_WB, Typen-Verteilung)
- **Fenster-Liste** (U_g, U_f, g-Wert, Rahmenanteil)

#### Dokumentation
- **ARCHITECTURE.md** - 5-Layer-Architektur, DB-Schema, Deployment
- **IFC_SIDECAR_LINK.md** - GUID-Mapping, Datenfluss, Best Practices
- **LOD_GUIDE.md** - LOD 100-500 Definitionen, Use Cases, Genauigkeit
- **KATALOG_VERWENDUNG.md** - Bundesanzeiger, Custom Catalogs
- **CONTRIBUTING.md** - Contribution Guidelines
- **CHANGELOG.md** - Versionshistorie (diese Datei)

#### Pläne & Konzepte
- **master-implementierung.md** - Master-Plan (LOD + Layer Structures)
- **ifc-viewer-integration-konzept.md** - IFC-Viewer Integration (Option C)
- **schichtaufbau-architektur.md** - Schichtaufbau-Konzept
- **lod-defaults-kataloge.md** - LOD-Konzept + Bundesanzeiger

### Changed

- **Schema-Struktur** - oneOf für Legacy vs. Varianten-Format
- **Materials** - `type` Feld hinzugefügt (STANDARD | AIR_LAYER)
- **Air Layers** - EN ISO 6946 konforme Luftschichten
- **README.md** - Vollständig überarbeitet (v2.0 Features, Quick Start)
- **Lizenz** - Von MIT zu Apache 2.0 (Patent-Klausel)

### Fixed

- **Validator** - Alle Ausgaben auf Deutsch übersetzt
- **API** - Alle Responses auf Deutsch übersetzt
- **Parameter-Matrix** - Feldnamen konsistent (`_kwh_a` Suffix)

### Deprecated

- **Legacy Format** - Einzelne Datei ohne Varianten (weiterhin unterstützt via oneOf)

---

## [1.0.0] - 2024-XX-XX

### Added

- **Initiales JSON Schema** (Draft-07)
- **Parameter-Matrix** (DIN 18599 Teil 1-10)
- **Python Validator** (CLI-Tool)
- **Web Viewer** (HTML/JS, Drag & Drop)
- **FastAPI Service** (REST-API für Validierung)
- **Beispiel-Datei** (musterhaus.din18599.json)
- **README.md** (Projekt-Übersicht)
- **LICENSE** (MIT)

### Schema v1.0

- **meta** - Projekt-Metadaten
- **input** - Eingabedaten (Zonen, Bauteile, Systeme)
- **output** - Ergebnisdaten (Energiebilanz, Kennwerte)
- **climate_location** - Klimadaten (Postleitzahl, TRY-Region)
- **zones** - Thermische Zonen
- **elements** - Opake Bauteile (U-Werte)
- **windows** - Transparente Bauteile
- **materials** - Materialien (λ, ρ, Ökobaudat)
- **systems** - Wärmeerzeuger
- **distribution** - Wärmeverteilung
- **dhw** - Trinkwarmwasser
- **ventilation** - Lüftung
- **lighting** - Beleuchtung
- **automation** - Gebäudeautomation
- **pv** - Photovoltaik

---

## [Unreleased]

### Geplant für v2.1

- **Validator-Erweiterung** (GUID-Checks, Referenz-Checks, LOD-Validierung)
- **Viewer-Erweiterung** (Layer Structures Visualisierung, Materials-Liste, LOD-Badge)
- **Editing MVP** (Inline-Edit U-Werte, Save/Export JSON)

### Geplant für v2.2

- **Schichtaufbau-Editor** (Modal, Drag-to-Reorder, Live U-Wert-Berechnung)
- **API-Erweiterung** (OpenAPI/Swagger, Merge-Endpoint)
- **Docker Compose** (Lokale Entwicklungsumgebung)

### Geplant für v3.0 (Optional)

- **IFC-Viewer Integration** (xeokit, GUID-Highlighting, Click-to-inspect)
- **IFC-Geometrie-Extraktion** (Normalenvektor → Orientierung, Flächen-Berechnung)
- **Multi-User-Editing** (WebSockets, Real-Time Collaboration)

---

## Versionsschema

**Format:** `MAJOR.MINOR.PATCH`

- **MAJOR:** Breaking Changes (Schema-Änderungen, API-Änderungen)
- **MINOR:** Neue Features (abwärtskompatibel)
- **PATCH:** Bugfixes (keine neuen Features)

**Beispiele:**
- `1.0.0` → `2.0.0` - Schema v2.0 (Breaking Changes)
- `2.0.0` → `2.1.0` - Validator-Erweiterung (neue Features)
- `2.1.0` → `2.1.1` - Bugfix (U-Wert-Berechnung korrigiert)

---

## Links

- **Repository:** https://github.com/DWEBeratungGmbH/din18599-ifc
- **Issues:** https://github.com/DWEBeratungGmbH/din18599-ifc/issues
- **Discussions:** https://github.com/DWEBeratungGmbH/din18599-ifc/discussions
- **Releases:** https://github.com/DWEBeratungGmbH/din18599-ifc/releases

---

[2.0.0]: https://github.com/DWEBeratungGmbH/din18599-ifc/releases/tag/v2.0.0
[1.0.0]: https://github.com/DWEBeratungGmbH/din18599-ifc/releases/tag/v1.0.0
[Unreleased]: https://github.com/DWEBeratungGmbH/din18599-ifc/compare/v2.0.0...HEAD
