# PLAN: Gebäudeakte v3.0 → v4.0 Big-Bang

**Stand:** 2026-07-23 (v2, nach Advisor-Gegencheck am Code) · **Entscheider:** Sebi
(Master, Modul-Owner Gebäudeakte) · **Status:** ENTWURF zum Abgeben.
**Begleitender Beschluss:** ADR-029 (DWEapp `docs/00-meta/DECISIONS/`).

> **Auslöser:** Das Revit-Plug-In produziert die feingranulare Topologie
> (`element_groups`, `boundaries`, `rooms` mit `zone_memberships`). Beim Sync-Test
> haben wir sie auf das aggregierte v3.0-`envelope` heruntergerechnet und dabei
> verworfen. Soll die Akte die *volle Wahrheit* halten, braucht sie das v4.0-Modell.
> Entscheidung Sebi: **Big-Bang jetzt** (alles Testdaten), UI/UX-Umbau parallel.

---

## 1. Ausgangslage (grounded + Advisor-verifiziert)

- **v4.0-Schema liegt bereit und ist self-contained:** `schema/v4.0/sidecar.schema.json`
  (43 interne `#/definitions/`-Refs, **0 externe File-Refs**, draft-07 wie v3.0).
  Der Typgenerator-Flip ist damit trivial. Validator, Referenz-Container,
  `paths.json` ebenfalls da. (Kein `v4.0-complete.json` — für den Flip nicht nötig.)
- **Die äußere Sidecar-Struktur ist identisch:** nur `input.*` ändert sich
  (`envelope` → `element_groups[]` + `boundaries[]` + `rooms[]`). `input.building`,
  `funding`, `roadmap`, `output`, `scenarios`, `sla_context` bleiben strukturell.
- **⚠ KORREKTUR ggü. v1 des Plans:** Es gibt **keinen rechnenden Solver**, der ein
  Sidecar konsumiert. `din18599-ifc:8000` exponiert nur `/health · /validate ·
  /parse-ifc · /parse-evebi · /generate-sidecar · /qng/parse` — ein **Produzent**.
  DWEapp *sendet* nie ein Sidecar dorthin (`din18599-client.ts` ruft nur
  `/generate-sidecar`: IFC+EVEBI rein → Sidecar raus). Und der Generator emittiert
  heute **Legacy `version "2.0.0"` mit `input.envelope`** (`sidecar_generator.py:60,
  115-150`) — also schon jetzt Drift.
- **`output.*` wird nicht gerechnet, sondern geseedet** — keine Engine in DWEapp
  oder im Service produziert es. Die „Rechnung" ist heute nicht live; das
  entschärft die Dringlichkeit von WS3 (aber verschiebt sie nicht).
- **Schema-First:** `din18599.generated.ts` wird per `pnpm run schema:generate`
  (`json2ts --input …/v3.0-complete.json`) generiert; ein Flip bricht den TS-Build
  an den Konsumenten (geführte Liste). **Wichtig:** der Drift-Guard
  `scripts/schema-check.mjs:23` (`SCHEMA_SOURCE`) muss **im selben Commit**
  mitflippen, sonst ist CI ab Commit 1 rot.

## 2. Bestehende Versions-Drift, die der ADR mit auflösen muss

Drei-Wege-Drift **heute schon**: TS-Typen `v3.0` · Doku „produktiv `v3.1`
eingefroren" · Generator emittiert `2.0.0`. Ein ADR, der nur „v3.0 → v4.0" sagt,
lässt v3.1 und die 2.0.0-Generate-Strecke offen → **vierte Wahrheitsquelle** statt
Auflösung. Der ADR setzt v4.0 als die *eine* Wahrheit und benennt, was mit der
Generate-Strecke passiert (→ Adapter, s. WS3).

## 3. Was NICHT bricht (der stabile Teil)

- **JSONB-Storage + Versionierung** schema-blind: `sidecar-patch.ts` (generische
  Pfad-Arrays), `building_versions_v2`, `saveSidecar`/`create` (lesen nur
  `schema_info.version`). Kein DB-Migrations-Skript nötig.
- `field-resolver.ts`, `din18599-client.ts` (Proxy), **Snapshots, Dashboard, Admin,
  ERPNext-Bridge (Stub), QNG-Export** (liest andere flache Form), `sla-service`
  (0 Treffer), `energy_calculations.prisma` (nur Skalar `envelope_area`).
- `funding · roadmap · output · sla_context` strukturell; `updateMeta`/`updateSystems`
  solange `meta`/`input.systems` bleiben.

## 4. Workstreams

### WS0 — Aggregations-Adapter (Kompatibilitäts-Spine) · **ZUERST** · DWEapp (api)
> Advisor-Kern-Empfehlung: **vor** dem Typen-Flip.
- Ein serverseitiger **v4 → v3-Aggregations-View** in `src/server/lib/` (portiert die
  Logik aus `state_to_sidecar_v3.py`: `element_groups`/`boundaries` → aggregierte
  `walls/roofs/floors/windows`). Gehört in die bestehende Ableitungs-Schicht
  `src/lib/helpers/building-elements.ts`.
- Dieser eine Adapter versöhnt **drei** Konsumenten gleichzeitig: (a) Legacy-Viewer
  rendert weiter, (b) die 2.0.0/v3-Generate-Strecke wird beim Ingest normalisiert,
  (c) ein etwaiger künftiger Rechenpfad. → Build bleibt in Phase 1 **grün** statt
  wochenlang rot.

### WS1 — Typkette (Wurzel) · din18599-ifc + DWEapp (api)
- `pnpm run schema:generate` auf v4.0 umbiegen (`package.json` **+**
  `scripts/schema-check.mjs:23` im selben Commit, Husky-Pre-Commit).
- `src/types/din18599.generated.ts` (neu aus v4.0), `src/types/din18599.ts` (Zod +
  Re-Exports `Envelope/OpaqueElement/…` → `ElementGroup/Boundary/Room/…`),
  `src/schemas/gebaeude.ts` (`envelopeSchema` → `elementGroups/boundaries`).
  Konsumenten brechen compiler-geführt.

### WS2 — Server-Schreibpfade · DWEapp (api)
- `buildings-sidecar.ts::updateEnvelope` (`['input','envelope']`) →
  `updateElementGroups`/`updateBoundaries`. `sidecar-patch.ts` URL/Bump auf v4.0.
  `buildings.ts:94/108` BGF aus `input.building` (bleibt gültig).

### WS3 — Ingest-Normalisierung + Aggregations-View · DWEapp (api) + energiekatalog
> **Neu gerahmt (war in v1 falsch als „Solver-Bridge"):** kein Solver. Die reale
> Bruchstelle ist die **Ingest-Strecke** `trpc.buildings.sidecar.generate` →
> `/generate-sidecar`, die heute `input.envelope` + `version "2.0.0"` zurückliefert.
- **(D1)** Entweder: DWEapp normalisiert die Generator-Antwort beim Ingest auf v4.0
  (Adapter aus WS0 rückwärts / Mapping) — **empfohlen**, Service unangetastet,
  billigste Rückbaubarkeit. Oder: `sidecar_generator.py` auf v4.0 heben — teurer,
  ändert den Produzenten-Vertrag auch für den Plug-In-Export (P4), an P4 koppeln.
- Der v4 → v3-View (WS0) deckt die aggregierte Sicht für EVEBI/Legacy ab.

### WS4 — UI/UX-Umbau · DWEapp (ui) — größter Brocken, parallel
- **17 Dateien** `src/components/building-viewer/*` (three-scene, sidebar-tree,
  inspector, Tabs, Meshes wall/roof/window/floor, Store) lesen `input.envelope`
  direkt → aus `element_groups`/`boundaries` rendern. **Kann nicht billig hinter
  ein Flag** — bis zum Rewrite rendert der Viewer nur über den WS0-Adapter (v4→v3).
- `scenario-merge.ts` + `building-elements.ts` (Element-`id`-Kopplung,
  `scenario.delta.elements`) neu.
- Hülle-Editor (`huelle-editor-client.tsx`, `envelope-detail-modal.tsx`),
  Berechnung/Zonen (`BerechnungZones.tsx` schreibt Zonen als `input.envelope.zones`-
  Hack → `zone_memberships`), Neu-Wizard (`step-manual-sidecar.ts`),
  `status-checklist.ts`, `sidecar-to-sandbox.ts`, `pii-filter.ts`.

### WS5 — Tests / Fixtures · alle
v3.0-Fixtures mitziehen (`din18599-schema.test.ts`, `sidecar-patch.test.ts`,
`gebaeude.test.ts`, `pii-filter.test.ts`, `status-checklist`/`kpi-derivation`,
`qng-evebi-parser.test.ts`, `din18599-evebi.test.ts`, `buildings-update.test.ts`).

### WS6 — Testdaten-Reset + Reseed · Sebi
8 Testgebäude leeren; mit v4.0 neu befüllen (Quelle: Plug-In-Export ab P4,
zwischenzeitlich `examples/v4.0/beispiel1/` + der Sync-Weg von heute).

## 5. Sequenzierung (Advisor-korrigiert)

```
Phase 0  ADR-029 beschließen (löst W4-27-Schema-Richtung ab)      Sebi        S
Phase 1  WS0 Aggregations-Adapter (v4→v3) — Kompatibilitäts-Spine api         M
Phase 2  WS1 Typen-Flip + WS2 Server-Write (schema-check im       api,        M
         selben Commit); Konsumenten kompilieren gegen den        din18599
         Adapter statt gegen zu leere v4-Reads → Build bleibt grün
Phase 3  WS4 UI-Umbau, parallel; ersetzt den Adapter Stück        ui          L
         für Stück durch native v4-Views
Phase 4  WS3 Ingest-Normalisierung                                api, energ. M
Phase 5  WS5 Tests grün + WS6 Reseed                              alle        S/M
```
Weil alles Testdaten ist, ist der **Cut hart möglich** (kein Bestandsdaten-Skript).

## 6. Die drei Entscheidungen, die VOR dem Hand-off stehen müssen

Sonst blockiert die Build-Session (Advisor):
- **D1 — WS3-Variante:** Ingest-Normalisierung in DWEapp *(empfohlen)* vs.
  `sidecar_generator.py` auf v4.0 heben. → im ADR gelockt.
- **D2 — Wo lebt die Aggregation:** DWEapp `src/server/lib` *(empfohlen, entkoppelt,
  rückbaubar)* vs. din18599-Service. Entscheidet Repo/Rolle und ob P4-Export jetzt
  v4 sein muss. → im ADR gelockt.
- **D3 — CI-Guard:** `package.json`-`schema:generate` **und**
  `scripts/schema-check.mjs:23` im selben Commit flippen. → als DoD im ADR.

## 7. Ehrliche Rest-Risiken

- **v4.0-Akte wird erst vom Plug-In-Export (P4) + Auth (P5) voll gefüttert.**
  Big-Bang jetzt baut die Aufnahme, nicht die Fütterung — deckt sich mit „später
  neu befüllen".
- **Am wenigsten reversibel wäre ein v4.0-Rewrite von `sidecar_generator.py`** (ändert
  den Produzenten-Vertrag auch für P4). Der Adapter-Ansatz (D1/D2 in DWEapp) hält
  das rückbaubar.
- **Nicht verifiziert:** woher `output.*` in den Seed-Akten stammt; exakte Zahl der
  brechenden Konsumenten (~30, Klassen bestätigt); Timo-`/projekte` (plausibel
  unberührt, nicht gegengeprüft).

## 8. Empfehlung

**GO mit Auflagen** (Advisor). Richtung tragfähig, Schema-Flip trivial, Aufwand in
**WS4 (UI, L)** und **WS0/WS3 (Aggregation/Ingest, M)**. Reihenfolge:
**Adapter-Spine → Typen-Flip → UI parallel → Ingest → Reseed.** Der ADR lockt
D1/D2/D3 und löst die Versions-Drift auf; W4-27-`.dwe`-Container + energy-DB-Katalog
bleiben gültig.
