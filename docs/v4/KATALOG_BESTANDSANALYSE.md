# Katalog-Bestandsanalyse — Grundlage für Schema v4.0

> **Zweck:** Diskussionsgrundlage nach [HANDOFF §8.1](HANDOFF-schema-v4-greenfield.md). Ist-Analyse des Katalog-Bestands + konsolidierte Anforderungen + offene Design-Fragen für Sebi.
> **Status:** Schritt 1 von 2. Katalog-Format wird ERST nach Sebis Feedback entworfen.
> **Stand:** 2026-07-21

---

## 0. Zusammenfassung in fünf Sätzen

Der Katalog-Bestand besteht aus **10 JSON-Dateien mit 664 KB**, von denen **keine einzige von Code konsumiert wird** — sie sind heute reine Dokumentationsartefakte ohne Laufzeit-Bindung. Damit gibt es **keine Zugriffsmuster, die v4.0 erhalten müsste**: das Katalog-Format ist echtes Greenfield. Das rechtliche Risiko C4 ist **deutlich kleiner als im Handoff angenommen** — die öffentliche Profil-Datei enthält bereits fast nur Struktur, die Tabellenwerte stehen als `"nach Tabelle"`-Platzhalter drin. Dafür existiert ein **anderes, ungeprüftes Exponat**: 605 KB norm-abgeleitete Symbol-/Index-/Glossar-Dateien im öffentlichen Repo. Die Verbindung Schema↔Katalog ist heute ein einziges unvalidiertes Freitext-Feld (`zone.usage_profile_ref`) ohne Katalog-Versionsangabe — genau die Lücke, die v4.0 schließen muss.

---

## 1. Ist-Bestand: Katalog-Dateien

### 1.1 `catalog/` — öffentlich, im Git getrackt

| Datei | Größe | Inhalt | Norm-Werte? | v4.0-Relevanz |
|---|---:|---|---|---|
| `din18599_symbols.json` | 231 KB | 562 Symbole (Symbol, LaTeX, Einheit, Datentyp, min/max, Norm-Ref) | Metadaten, keine Tabellenwerte | mittel — Symbol-Registry für Output-Kennwerte |
| `din18599_indices.json` | 177 KB | 735 Indizes (h, d, ce, …) + Kategorien | nein | niedrig |
| `din_norms_registry.json` | 98 KB | 3 Normen (DIN 277, 18599, …) mit Titel/Summary/Description | nein, aber Fließtext-Zusammenfassungen | **hoch** — Basis für `norm_editions{}` (E3) |
| `din18599_glossary.json` | 97 KB | 222 Begriffe. **Definitionen weitgehend leer oder kaputt** (z.B. `definition_de: "**GA**"`) | nein | niedrig — Datenqualität mangelhaft |
| `constructions.json` | 16 KB | 24 Konstruktionen mit Schichtaufbau + U-Wert, 9 Kategorien, 7 Bauepochen | nein (DWE-eigen) | **hoch** — Vorbild für Erweiterungs-Katalog |
| `din18599_usage_profiles.json` | 16 KB | 45 Profile (2 WG + 43 NWG) | **teilweise** — siehe §2 | **hoch** — Kern-Katalog |
| `materials.json` | 15 KB | 50 Materialien (λ, ρ, c, μ) + 11 Kategorien | nein (DIN 4108-4 abgeleitet, Grenzfall) | **hoch** — Erweiterungs-Katalog |
| `din18599_indexing_system.json` | 11 KB | Indizierungs-Systematik (3 Ebenen, Pattern `{SYMBOL}_{L1}[,{L2}]`) | nein | niedrig |
| `din18599_interface_map.json` | 2,7 KB | Datenflüsse zwischen Norm-Teilen (1 Input, 7 Outputs) | nein | niedrig — sehr unvollständig |
| `schema_mapping.json` | 1,8 KB | Symbol → JSON-Pfad-Mapping | nein | **veraltet** — mappt auf v2.1-Pfade (`zones[].usage_profile.parameters_din.*`), die es in v3.1 nicht mehr gibt |

### 1.2 `catalog-private/` — gitignored, korrekt geschützt

`din18599_nutzungsprofile.json` (4,6 KB) + README. Der `.gitignore` sperrt `catalog-private/`, `*.xlsx`, `sources/docx|markdown|images`. **Sauber umgesetzt** — `git ls-files` bestätigt: nichts davon getrackt.

Die README dort dokumentiert bereits exakt die Trennung, die der Handoff §E5 fordert (Struktur public / Werte privat) — **das Konzept existiert also schon, es ist nur nirgends in Code oder Schema verankert.**

### 1.3 `catalogs/` (Plural) — leer

Leeres Verzeichnis, im Git nicht vorhanden. Wird in [CLAUDE.md](../../CLAUDE.md) als „Bundesanzeiger 2020 Katalog" beschrieben — **Doku-Drift, der Inhalt existiert nicht.** Ebenso `api/catalogs/` und `api/examples/`: beide leer.

---

## 2. C4 — rechtliche Betroffenheit, real gemessen

**Der Handoff-Befund („liegt aktuell MIT Normwerten im öffentlichen Repo") ist so nicht korrekt.** Gemessener Ist-Zustand von `catalog/din18599_usage_profiles.json`:

- **43 NWG-Profile: enthalten KEINE Parameter.** Nur `id`, `number`, `name_de/en`, `category`, `norm_ref`, `description`. Das ist reine Struktur.
- **2 WG-Profile: 7 Parameter**, davon 3 mit Platzhalter `"value": "nach Tabelle"` (q_I, q_w_b_a, q_el_b) und 4 mit konkreten Zahlen: `theta_i_h_soll=20 °C`, `theta_i_c_soll=26 °C`, `delta_theta_i_NA=4 K`, `n_nutz=0,5 1/h`.

Diese vier Werte sind in GEG/EnEV-Kontext derart verbreitet, dass sie kaum als schutzfähige Schöpfungshöhe durchgehen — juristisch zu klären, aber **kein akutes Leck**. Der Platzhalter-Ansatz `"nach Tabelle"` ist faktisch bereits die vom Handoff §E5 geforderte Struktur-ohne-Werte-Strategie, nur unsystematisch (Platzhalter als String im `value`-Feld statt `value: null` + eigenes Referenzfeld).

### ⚠️ Stattdessen: ein anderes, bisher unbewertetes Exponat

`din18599_symbols.json` + `din18599_indices.json` + `din18599_glossary.json` + `din_norms_registry.json` = **605 KB, aus den gitignorierten Norm-Quellen (`sources/docx/`) extrahiert, im öffentlichen Repo.**

Einschätzung nach Stichprobe:
- **Symbole/Indizes:** Formelzeichen, Einheiten, Wertebereiche. Einzelfakten ohne schöpferische Gestaltung — Risiko gering, aber die *Auswahl und Systematik* von 562 Symbolen ist als Datenbankwerk (§87a UrhG) grundsätzlich angreifbar.
- **Glossar (222 Begriffe mit Nummer + Norm-Abschnitt):** Wäre bei vollständigen Definitionen das größte Risiko — die Definitionstexte sind aber überwiegend leer oder Extraktionsmüll. Faktisch also ein Inhaltsverzeichnis der Norm.
- **`din_norms_registry.json`:** enthält mehrzeilige Fließtext-Zusammenfassungen (`description`) zu Normen. Selbst formuliert = unproblematisch, aus der Norm übernommen = Zitat-Frage.

**Empfehlung für Sebis DIN-Media-Gespräch:** nicht nur über Tabellenwerte sprechen, sondern über diese vier Dateien mit. Sie sind das größere Volumen und das schlechtere Preis-Leistungs-Verhältnis (605 KB Risiko, davon wird heute nichts benutzt).

---

## 3. Wie werden die Kataloge heute konsumiert?

**Gar nicht.** Belegt durch Volltextsuche über `api/**/*.py` und `tools/`:

- **Kein Parser lädt eine Katalog-Datei.** Der einzige Treffer im gesamten Backend ist ein hartkodierter Default in [api/generators/sidecar_generator.py:724](../../api/generators/sidecar_generator.py#L724): `"usage_profile": "17"  # Wohnen (default)` — ein Magic String ohne Katalog-Lookup.
- **Der Validator kennt keine Kataloge.** [tools/validate.py](../../tools/validate.py) ist ein 60-Zeilen-`jsonschema.validate()`-Wrapper. Er prüft ausschließlich JSON-Schema-Konformität, keine Referenz-Auflösung. Sein Default-Schemapfad (`../gebaeude.din18599.schema.json`) **zeigt ins Leere** — die Datei liegt nur noch unter `archive/old-versions/`.
- **`schema_mapping.json` ist tote Doku** — mappt auf v2.1-Pfade, die seit v2.3 nicht mehr existieren.

### Konsequenz für v4.0

> **Es gibt keine zu erhaltenden Zugriffsmuster.** Der Handoff §8.1 fragt „welche Zugriffsmuster müssen weiter funktionieren bzw. sind Vorbild" — die Antwort ist: keine, und kein Vorbild. Das Katalog-Format kann frei entworfen werden, muss aber erstmals *überhaupt* einen Konsumenten bekommen, sonst wiederholt sich die Situation.

Das ist zugleich die wichtigste Lehre aus dem Bestand: **Kataloge ohne Code-Bindung driften garantiert.** v4.0 sollte den Validator als ersten echten Katalog-Konsumenten mitliefern (Handoff §6 Punkt 5) — sonst sind die Kataloge in sechs Monaten wieder Deko.

---

## 4. Referenztabellen, die heute IM Schema statt im Katalog leben

v3.1 enthält 28 Enums. Auslagerungs-Kandidaten (Kriterium: ändert sich mit Norm-Edition ODER braucht mitgeführte Fachdaten wie Fx/Offset-Regeln):

| Enum in v3.1 | Werte | v4.0-Empfehlung |
|---|---:|---|
| `opaque_element.din_code` | 16 (WA, WI, WE, WU, WZ, DA, DE, …) | **→ Katalog.** Bauteil-Code-System der DIN, editionsabhängig |
| `transparent_element.din_code` | 9 (FA, FD, FL, FU, FZ, TA, TD, …) | **→ Katalog**, gemeinsam mit obigem |
| `opaque/transparent.boundary_condition` | 4 (`exterior`, `ground`, `unheated`, `adjacent`) | **→ Katalog** als `adjacency_types`. Direkter Vorgänger von Handoff §4 (12+ Codes mit Fx **und** Maßbezugs-Regel) — ein Enum kann Fx + Offset-Regel nicht mittragen |
| `zone.usage_profile_ref` (Freitext) | — | **→ Katalog-Ref mit Auflösung.** Heute `type: string` ohne Pattern, ohne Katalog-Version, ohne Validierung |
| `primary_energy_factors.source` | 4 (`GEG_2024`, `BEG_2024`, …) | **→ Katalog**, editionsabhängig (f_P-Werte) |
| `funding_entry.program` | 7 (BEG_EM, KFW_261, …) | **→ Katalog.** Förderprogramme ändern sich häufiger als das Schema |
| `document.type`, `roadmap_step.status`, `target_entry.kind/source`, `meta.lod`, `ventilation_system.type`, `automation.bacs_class`, `energy_certificate.energy_class` | 4–9 | **im Schema lassen.** Prozess-/Struktur-Enums, nicht norm-abhängig |

**Leitregel-Vorschlag:** Im Schema bleibt, was den *Datenzustand* beschreibt (Status, Dokumenttyp, LOD). In den Katalog wandert, was *Fachwissen* trägt (Norm-Codes, Fx-Werte, Profile, Programme) — erkennbar daran, dass es pro Norm- oder GEG-Edition abweichen kann.

---

## 5. Konsolidierte Katalog-Anforderungen aus dem Handoff

| Katalog | Umfang | Struktur (public ok) | Normwerte (C4-kritisch) | DWE-eigen (public ok) | Dimensioniert nach |
|---|---|---|---|---|---|
| `room_types` | ~55 Typen | Code, Name, 3-Normen-Mapping (18599/277/GEG) | — | Vorschlagslogik, Default-Zuordnung | ggf. `norm_edition` |
| `adjacency_types` | 12+ Codes | Code, Name, Norm-Zeilen-Ref (T5-Z1 …) | **Fx-Zahlenwerte** | **Offset-/Maßbezugs-Regel** (Handoff §4 — reine DWE-Auslegung) | `norm_edition` |
| `usage_profiles` | 42 (2018-09) / 43 (2025-10) | Nummer, Name, Kategorie, Parameter-*Namen* | **alle Parameterwerte** (Tab. 5–7) | — | **`norm_edition` (Pflicht)** |
| `geg_reference_building` | 7+ Zeilen | Zeilen-Struktur, Mapping opening_type→Zeile | **U-Werte/g-Werte der Referenz** | Mapping-Logik (Handoff §3) | **`geg_edition` (Pflicht)** |
| `constructions` | 24 → wachsend | vollständig | — | vollständig | `catalog_version` |
| `materials` | 50 → wachsend | vollständig | λ-Werte aus DIN 4108-4 = Grenzfall | vollständig | `catalog_version` |
| `oekobaudat` (perspektivisch) | — | — | — | DWEapp-seitig, eigene Lizenz | `catalog_version` + `valid_from/to` |

**Beobachtung zur Versionierungs-Frage:** Die Anforderung ist *nicht* pauschal. Es zerfällt in drei saubere Klassen:
1. **Norm-dimensioniert** (`usage_profiles`, `adjacency_types`): brauchen `norm_edition` als Achse — mehrere Editionen parallel vorhalten.
2. **Recht-dimensioniert** (`geg_reference_building`, `primary_energy_factors`): brauchen `geg_edition` + `valid_from/valid_to`, weil rechtlich datumsgebunden.
3. **Kuratiert** (`constructions`, `materials`, `room_types`): brauchen nur ein monoton steigendes `catalog_version` — keine Editionsachse, hier gibt es keine „richtige" Parallelwelt.

Ein Meta-Schema müsste alle drei tragen. Das ist die Kernfrage in §6.2 unten.

---

## 6. Offene Design-Fragen — Entscheidungsbedarf Sebi

### 6.1 Overlay-Mechanismus: so gewollt?

Handoff-Vorschlag: Struktur-Datei public (`value: null` + Norm-Referenz) + Values-Overlay privat, Merge zur Laufzeit; ohne aufgelöste Werte kein `calc_ready`.

**Meine Empfehlung: ja, aber mit einer Präzisierung.** Der Merge sollte nicht auf `value: null` aufsetzen, sondern auf explizite Slots:

```json
{ "id": "PROFILE_NWG_01", "norm_ref": "DIN V 18599-10:2018-09, Tab. 6, Zeile 1",
  "parameters": { "theta_i_h_soll": { "unit": "°C", "value_source": "norm_table",
                                      "norm_cell": "T6-Z1-S19" } } }
```

Grund: `value: null` ist nicht unterscheidbar von „Wert existiert für dieses Profil nicht". Ein `norm_cell`-Zeiger macht den Overlay-Merge **prüfbar** — der Validator kann melden, welche Zellen fehlen, statt nur „irgendwas ist null". Das ist auch die ehrlichere Dokumentation dessen, was das offene Repo bewusst *nicht* enthält.

**Unterfrage aus dem Handoff — eine Overlay-Datei pro Norm oder eine gesamt? Empfehlung: pro Katalog + pro Edition**, also `usage_profiles.values.2018-09.json`. Begründung: die Lizenzlage kann pro Norm unterschiedlich ausgehen (18599 lizenziert, 277 nicht), und ein Nutzer mit eigener Teil-Lizenz kann dann genau das befüllen, was er darf. Eine Sammeldatei erzwingt Alles-oder-nichts.

### 6.2 Ein generisches Rahmenformat oder Schema pro Katalog?

**Empfehlung: generischer Rahmen (Envelope) + katalogspezifisches `entries[]`-Schema.** Also *ein* Meta-Schema für Kopf und Versionierung:

```json
{ "catalog_id": "adjacency_types", "catalog_version": "1.0.0",
  "catalog_source": "core", "dimension": { "type": "norm_edition", "value": "2018-09" },
  "entry_schema_ref": "catalog/schemas/adjacency_types.schema.json",
  "entries": [ … ] }
```

Grund: Der Rahmen ist der Teil, der wirklich für alle gleich sein muss (Auflösung, Versions-Pinning, Overlay-Merge, `catalog_source`). Die Einträge sind fachlich zu verschieden — ein Fx-Wert und ein Materialschichtaufbau in ein gemeinsames Entry-Schema zu zwingen, erzeugt nur ein generisches `properties: {}`-Loch. Der Loader muss dann genau einen Rahmen kennen, nicht sieben.

Die drei Versionierungs-Klassen aus §5 fallen damit in ein einziges `dimension`-Feld (`norm_edition` | `legal_edition` | `none`).

### 6.3 Wo leben die Kern-Kataloge physisch?

**Empfehlung: in diesem Repo unter `catalog/`, nicht als eigenes Repo.** Kern-Kataloge und Schema entwickeln sich synchron (jede neue `adjacency_type` braucht ggf. ein Schema-Feld). Ein zweites Repo verdoppelt die Release-Koordination für einen Gewinn, der erst bei externen Katalog-Beitragenden entsteht — den Fall gibt es heute nicht. Die Werte-Overlays liegen ohnehin außerhalb (DWEapp bzw. lokal).

Trennung stattdessen über Verzeichnisse: `catalog/core/` (public, Struktur) und ein per `.gitignore` gesperrtes `catalog/values/` für lokale Overlays — das setzt das heutige `catalog-private/`-Muster fort, das nachweislich funktioniert.

### 6.4 Wie referenziert das Sidecar Katalogstände reproduzierbar?

**Empfehlung: beides, auf zwei Ebenen.**
- `meta.catalogs[]` — pro verwendetem Katalog `catalog_id` + `catalog_version` + `dimension`. Das ist die Reproduzierbarkeits-Angabe.
- Zusätzlich der `used_profile_values`-Snapshot aus Handoff §E5 bei Berechnung/Einfrieren — der macht das Sidecar auch dann noch rechenbar-nachvollziehbar, wenn der Katalogstand nicht mehr beschaffbar ist.

Das eine ist die Referenz, das andere die Kopie. Bitemporales Muster analog `offerSnapshot`, wie im Handoff vorgesehen.

### 6.5 `room_types`: flache Liste oder getrennt WG/NWG?

**Empfehlung: flache Liste mit `applicability`-Feld** (`["WG"]` / `["NWG"]` / `["WG","NWG"]`). Der heutige Bestand ist getrennt (`residential_profiles` / `non_residential_profiles`) und erzeugt genau das Problem, das im Bestand sichtbar ist: die zwei WG-Profile haben ein *anderes Parameter-Set* als die NWG-Profile, was die Struktur inkonsistent macht. Mischgebäude (`sla_context.gebaeudeart: "MISCH"` existiert bereits) brauchen ohnehin beides in einer Liste. Ein Filter-Feld ist billiger als zwei Listen mit divergierenden Feldern.

### 6.6 Neu, nicht im Handoff: braucht `adjacency_types` überhaupt Werte-Overlay?

Die Fx-Werte aus Handoff §4 (1,0 / 0,8 / 0,5 / 0,35 / 0,7 …) stehen bereits **im Handoff-Dokument selbst** und in jedem GEG-Kommentar. Es sind 12 Zahlen, keine Tabelle mit 43×24 Zellen. **Vorschlag: `adjacency_types` komplett public inkl. Fx** — mit Norm-Zeilen-Referenz. Sonst blockiert der Overlay-Mechanismus den einen Katalog, der für die Grundfunktion (Boundary-Validierung) zwingend zur Laufzeit da sein muss. Zu klären mit DIN Media, aber der Aufwand-Nutzen-Schnitt liegt hier anders als bei den Nutzungsprofilen.

---

## 7. Korrekturen an Handoff-Annahmen

Drei Punkte, die vor dem v4.0-Entwurf geradegezogen gehören:

1. **„Parser IFC/EVEBI laufen weiter gegen v3.1"** (§1) — stimmt nicht. [ifc_parser_v3.py:1170](../../api/parsers/ifc_parser_v3.py#L1170) emittiert `version: "2.3.0"`, [sidecar_generator.py:101](../../api/generators/sidecar_generator.py#L101) sogar `url: ".../schema/v1"`. Kein Parser erzeugt v3.x. **Der einzige echte v3.x-Konsument ist DWEapp** — und der generiert seine TS-Typen aus **v3.0** ([scripts/schema-check.mjs:23](/opt/weclapp-manager/scripts/schema-check.mjs#L23)). Beim Aufräumen alter Schemata ist v3.0 der Stand, der Produktivcode bricht, nicht v3.1.

2. **„v3.2 ist nur v3.1-Kopie mit geändertem Title"** (§9) — fast. Es sind zwei echte neue Felder in `funding_entry` (`step_refs[]`, `status_erweitert`), die DWEapp bereits schreibt ([qng.ts:853](/opt/weclapp-manager/src/server/api/routers/qng.ts#L853)). Zusätzlich hat v3.2 zwei Defekte: `schema_info.url` const und `version`-Pattern (`^3\.1\.\d+$`) wurden nie hochgezogen — **das Schema lehnt seine eigene Version ab** — und `step_refs[]` verweist auf `scenarios[].steps[].id`, was es in keiner Version gibt (Schritte liegen unter `roadmap.steps[]`). Beim Verwerfen zugunsten v4.0 müssen diese zwei Felder in v4.0 landen, sonst verliert DWEapp Daten.

3. **C4-Lage** — siehe §2: die benannte Datei ist weit weniger exponiert als angenommen, dafür sind 605 KB andere Dateien bisher gar nicht bewertet.

---

## 8. Vorschlag: nächster Schritt

Nach Handoff §8.2 wartet der Katalog-Feinentwurf auf Sebis Feedback zu §6. Unabhängig davon startbar (Handoff §6 Punkte 1–2):

- `schema/v4.0/manifest.schema.json` — Container-Manifest
- `schema/v4.0/sidecar.schema.json` — Sidecar-Kern mit `boundaries[]`, `element_groups[]`, `zone_memberships[]`

Beide mit bereits vorgesehenen, aber noch nicht ausdefinierten Katalog-Referenzfeldern (`catalog_ref`, `catalog_source`) — die Felder stehen, ihre Auflösungssemantik kommt aus der Feedback-Schleife.
