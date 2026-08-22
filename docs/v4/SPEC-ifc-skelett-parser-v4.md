# SPEC — IFC-Skelett-Parser v4 (`draft`-Sidecar aus nackter IFC)

> **Status:** BUILD-READY SPEC-ENTWURF (Rolle `din18599`). Kein Code. Locks stehen aus (siehe §9).
> **Version des Ziels:** Sidecar-Schema **v4.0** (`schema/v4.0/sidecar.schema.json`, `$id .../v4.0/sidecar`).
> **Ziel-Level:** `draft` — das minimal gültige, ehrliche v4.0-Skelett.
> **Erzeugt am:** 2026-07-24 · **Belege:** Zeilenangaben gegen `schema/v4.0/sidecar.schema.json` (Commit-Stand HEAD `156d067`).

---

## 0. Einordnung & Abgrenzung

### 0.1 Wozu dieser Parser

Teil des IFC+Sidecar-Import-Konzepts der Gebäudeakte. Er bedient **ausschließlich** das Szenario **„nackte IFC ohne Sidecar"** (Eingangs-Kanal 2 „IFC-Upload", `docs/04-dossiers/app/gebaeudeakte/08-eingangs-kanaele.md`). Er erzeugt aus einer IFC-Datei ein strukturell gültiges v4.0-Sidecar auf Level `draft`, das ein Berater danach mensch-geführt (Anreicherungs-Assistent) hochzieht.

Er bedient **nicht** den `.dwe`-Container-Import (IFC + fertiger v4.0-Sidecar aus Revit/Dynamo). Dort ist der mitgelieferte Sidecar die Wahrheit und wird 1:1 übernommen — dieser Parser läuft in dem Fall gar nicht.

### 0.2 Was er ersetzt (kaputter Ist-Pfad)

| Ist heute | Problem | Beleg |
|---|---|---|
| `api/main.py` `/generate-sidecar` | verlangt **beide** Files (`ifc_file` **und** `evebi_file`, beide `File(...)`) → IFC-only ist unmöglich | `api/main.py:181-195` |
| `api/generators/sidecar_generator.py` | emittiert **Legacy-Envelope** (v3.x-Form), nicht v4.0 | `api/generators/sidecar_generator.py` (1110 Z.) |

Der neue Parser ist **eigenständig**. **Keine** Wiederverwendung des Legacy-Generators. Wiederverwendbar ist allein die reine Geometrie-Extraktion aus `api/parsers/ifc_parser.py` (siehe §5).

### 0.3 Harte Leitplanke — REIN GEOMETRIE

Der Parser berechnet **keine** Anreicherungsregeln. Verboten: `adjacency_type`/`boundary_condition`, Raumtyp→θ/Lüftung/beheizt, Konstruktion→`u_value`/`construction_ref`-Auflösung, `fx`, Wärmebrücken (`edges[]`/`delta_u_wb`), `fingerprint`-**Gruppierung** über Toleranzen. Diese Regeln sind deklarativ (din18599-Katalog) bzw. algorithmisch (geteilte Core-Engine) und werden vom Anreicherungs-Assistenten bzw. der Engine gefüllt — **nicht hier zweitimplementiert**. Details in §7 (NICHT-ZIELE).

> **⚠ Beleg-Warnung:** Die im Auftrag als Quelle genannte **ADR-033** (`weclapp-manager/docs/00-meta/DECISIONS/ADR-033-anreicherungsregel-quelle.md`) **existiert im Repo nicht** (weder Datei noch String „ADR-033"/„Anreicherungsregel" auffindbar, Stand 2026-07-24). Diese Spec übernimmt die im Auftrag zitierte Substanz von ADR-033 als bindend, kann sie aber nicht gegen ein Dokument verifizieren. Das exakte Ziehen der Grenze „Parser vs. Anreicherung" an einzelnen Feldern ist damit teils Master-Entscheidung (§9), nicht Schema-Fakt. → **OFFEN-1**.

---

## 1. Schema-Befunde zu den fünf Kern-Fragen

Alle Belege gegen `schema/v4.0/sidecar.schema.json`.

### 1.1 Frage — Dürfen/sollen `boundaries` auf `draft` emittiert werden?

**Antwort: NEIN — `boundaries[]` werden bewusst DEFERRED. Leer/weggelassen ist auf `draft` (und sogar `enriched`) schema-gültig.**

Belege:
- `input` verlangt nur `["building"]` (Z. 34). `boundaries` ist ein **optionales** Array (Z. 41).
- `boundary.required = ["id", "element_group_ref", "space_a", "adjacency_type"]` (Z. 550). `space_a` (innerer Raum, Z. 558) und `adjacency_type` (Z. 567, `$ref adjacency_type`) sind **Anreicherung**, nicht Geometrie. Ein Parser, der keine Angrenzungsart erfindet, **kann** also gar keine gültige Boundary bauen.
- Bestätigung durch das **Referenz-Beispiel**: `examples/v4.0/beispiel1/energy.din18599.json` hat `input.boundaries = []` (leer) und ist trotzdem gültig — sogar auf Level `enriched`.
- Bestätigung durch das **Manifest-Beispiel**: Befund `BOUNDARIES_EMPTY`, `severity: warning`, `blocks_level: geometry_ok` (`examples/v4.0/beispiel1/manifest.json`). Leere Boundaries blockieren erst `geometry_ok` aufwärts — **nicht** `draft`, **nicht** `enriched`.
- Validator: `pruefe_angrenzungen` meldet `BOUNDARIES_EMPTY` mit `blocks_level="geometry_ok"` (`tools/dwe_validate.py:323-326`).

**Konsequenz für den Output-Vertrag:** `input.boundaries` wird **weggelassen** (nicht als `[]` gesetzt, um „ich habe versucht und nichts gefunden" nicht zu suggerieren — reine Konvention, beides ist gültig; Empfehlung: weglassen). Die Angrenzungsmatrix entsteht erst im Assistenten/der Engine.

### 1.2 Frage — `fingerprint` ist required: triviale 1:1-Gruppen oder ungruppierte Roh-Elemente?

**Antwort: Der Parser emittiert `element_groups[]` als TRIVIALE 1:1-Gruppen (ein IFC-Element = eine Gruppe). Der `fingerprint` wird aus der Geometrie **dieses einen** Elements berechnet — das ist Geometrie, erlaubt. Die echte tolerante GRUPPIERUNG (mehrere Elemente → eine Gruppe, 1°/2 cm) ist die algorithmische Anreicherungsregel und passiert später in der geteilten Engine.**

Belege:
- `element_group.required = ["id", "element_type", "fingerprint"]` (Z. 448). Es gibt im Schema **keinen** alternativen Platz für „ungruppierte Roh-Elemente" — kein `raw_elements[]`, kein Container ohne Fingerprint. Wer Geometrie tragen will, muss `element_groups[]` benutzen.
- `fingerprint.required = ["normal_x", "normal_y", "dist_m"]` (Z. 464). Das sind reine Ebenen-Kennwerte **eines** Elements (Normale im Projektsystem + Abstand vom Ursprung). Der bestehende Parser rechnet die Normale bereits (`_calculate_orientation_and_inclination`, `ifc_parser.py:316-360`). → parser-legitim.
- Die **Gruppierungsregel** selbst (Winkelabstand ≤ `angle_tolerance_deg`, |Δdist| ≤ `dist_tolerance_m`, gleicher Bauteiltyp, Greedy-Repräsentant) steht in der `fingerprint.description` (Z. 463) — sie ist eine algorithmische Regel, kein Parser-Job.
- `member_elements` ist „bei JEDEM Lauf neu berechnet und ausdrücklich flüchtig" (Z. 506-508). Bei 1:1-Gruppen enthält es genau **ein** Element.

**Ehrliche Nebenwirkung (Feature, kein Bug):** Zwei koplanare Wände, die eigentlich eine Gruppe wären, liegen bei 1:1-Emission als zwei Gruppen vor und lösen im Validator `FINGERPRINT_COLLISION` (warning, ohne `blocks_level`, `tools/dwe_validate.py:205-210`) aus. Das ist genau das Signal „Gruppierung steht noch aus" und ist auf `draft` unschädlich.

> **Terminologie-Konflikt zum Auftrag:** Der Auftrag spricht von Level **`grouped`**. Ein solches Level **existiert im Schema nicht**. Die Level-Enum ist `["draft", "enriched", "geometry_ok", "balanced", "calc_ready"]` (Z. 171; identisch in `manifest.schema.json` `validation_level`). Die tolerante Gruppierung müsste also innerhalb `enriched`/`geometry_ok` laufen, nicht auf einem eigenen Level. → **OFFEN-2**.

### 1.3 Frage — Welche geometrischen Felder darf der Parser füllen?

Siehe die vollständige Mapping-Tabelle in §4. Kurzfassung des Erlaubten: `building` (Aggregat-Maße, soweit aus Geometrie ableitbar), `storeys[]` (aus `IfcBuildingStorey`), `element_groups[]` (1:1, aus `IfcWall`/`IfcSlab`/`IfcRoof`/…), deren `fingerprint`, `member_elements` und die **read-only** `aggregates` (`member_count` etc.). Optional: `constructions[]` als Geometrie-Skelett (Schichtdicken + Materialnamen aus `IfcMaterialLayerSet`, **ohne** `lambda`/`u_value`). `rooms[]` sind ein Sonderfall — siehe §1.6/§2.

### 1.4 Frage — Vollständigkeits-Marker (`draft`/`enriched`/…) im Schema?

**Antwort: JA, an zwei Stellen. Für „Skelett" ist der Wert `draft`.**

Belege:
- `meta.validation.level`, Enum `["draft", "enriched", "geometry_ok", "balanced", "calc_ready"]` (`schema/v4.0/sidecar.schema.json:165-172`). „Redundant zum Manifest, damit ein herausgelöstes Sidecar selbstauskunftsfähig bleibt" (Z. 167).
- `manifest.validation.level` (`$ref validation_level`, `manifest.schema.json`), gleiche Enum, mit Semantik-Doku: **`draft = strukturell gültig`**, `enriched = Fachdaten vollständig`, …
- Der Validator gießt genau das: Level `draft` = besteht die reine JSON-Schema-Validierung (`Draft7Validator`, `tools/dwe_validate.py:106-118`), sonst nichts.

**Parser setzt:** `meta.validation.level = "draft"` (und im Manifest `validation.level = "draft"`, falls der Parser auch ein Manifest schreibt — siehe §6/OFFEN-6).

### 1.5 Frage — Provenienz: `source = IFC_PARSER` (+ `readOnly`?) pro Feld?

**Antwort: Provenienz gibt es NUR gebäudeweit, NICHT pro Feld. Der Parser setzt `meta.source.origin = "IFC_PARSER"`. Ein `readOnly`-Marker ist KEIN Provenienz-Marker.**

Belege:
- `meta.source.origin`, Enum enthält **`"IFC_PARSER"`** (`schema/v4.0/sidecar.schema.json:181-192`) — plus `tool`, `tool_version`. Das ist **eine** Herkunft für den **ganzen** Sidecar-Stand, nicht pro Feld.
- Es gibt **keinen** universellen Per-Feld-Provenienz-Mechanismus. `source` existiert nur objekt-lokal an einzelnen Sub-Entitäten mit je **anderer** Enum, etwa bei `construction.source`, `airtightness.source`, `zone.used_profile_values.source`, `shading.source`, `energy_certificate.source` und `target_entry.source`. Keiner davon deckt „wer hat dieses Geometriefeld geschrieben" ab.
- `readOnly` markiert **abgeleitete** Felder (`aggregates` Z. 523, `envelope_kpis` Z. 269, `openings_index` Z. 44, `opening.geg_reference_row` Z. 725) — „aus der Quelle berechnet, nie gepflegt". Das ist Ableitungs-Semantik, **nicht** Autorenschaft.

**Konsequenz:** Der Parser kann `IFC_PARSER` nur global stempeln. Die Unterscheidung „authored vs. assistiert **pro Feld**" trägt das Schema heute **nicht**. Wenn der Anreicherungs-Assistent das braucht, ist das eine Schema-Erweiterung (Major-relevant) oder ein DWEapp-DB-seitiges Audit (Eingangs-Kanal-Doku führt bereits ein Schreib-Audit über `building_versions_v2`). → **OFFEN-3**.

### 1.6 Zusatz-Befund (nicht explizit gefragt, aber blockierend): `room.heating_status` ist der ZWEITE Anreicherungs-Zwang

`room.required = ["id", "heating_status"]` (Z. 300). `heating_status ∈ {heated, unheated, low_heated}` (Z. 337) ist **Konditionierung = Anreicherung**, kein Geometriewert, und hat **keinen** `default`. Damit gilt für Räume dieselbe Spannung wie für Boundaries: Ein streng ADR-033-reiner Parser, der Konditionierung nicht erfindet, **kann keinen schema-gültigen Raum emittieren**.

Das ist die zentrale offene Design-Frage dieser Spec. Optionen in §2.2 / **OFFEN-4**. `building.type` (required, Enum, nicht geometrisch ableitbar) hat dasselbe Problem eine Ebene höher → **OFFEN-5**.

---

## 2. Output-Vertrag

### 2.1 Der ehrliche `draft`-Boden (was IMMER gefüllt wird)

Minimal schema-gültig braucht es: `schema_info` + `meta` + `input.building` (Top-`required`, Z. 8; `input.required`, Z. 34).

| Sidecar-Pfad | Wert im `draft` | Quelle |
|---|---|---|
| `schema_info.url` | `https://din18599-ifc.de/schema/v4.0/sidecar` (const, Z. 19) | fix |
| `schema_info.version` | `4.0.0` (Pattern `^4\.0\.\d+$`, Z. 23) | fix |
| `meta.project_name` | `IfcProject.Name` (Fallback: Dateiname) | IFC |
| `meta.norm_editions.din_18599` | `2018-09` (`default`, Z. 108) | fix-Default |
| `meta.source.origin` | `IFC_PARSER` (Z. 187) | fix |
| `meta.source.tool` / `tool_version` | Parser-Name + Version | fix |
| `meta.validation.level` | `draft` (Z. 171) | fix |
| `meta.ifc_file_ref` | `model.ifc` bzw. Upload-Dateiname (Z. 95) | IFC |
| `meta.created_at` | Export-Zeitpunkt | Laufzeit |
| `input.building.type` | **OFFEN-5** (required, nicht geometrisch) | Entscheidung nötig |

### 2.2 Geometrie, die der Parser füllen SOLL (soweit vorhanden)

| Sidecar-Pfad | Bedingung | Quelle |
|---|---|---|
| `input.storeys[]` | je `IfcBuildingStorey` | IFC (§4) |
| `input.element_groups[]` | je `IfcWall`/`IfcSlab`/`IfcRoof`/… (1:1) | IFC (§1.2, §4) |
| `input.constructions[]` | je distinktem `IfcMaterialLayerSet` (Skelett) | IFC (§4) |
| `input.building.ngf_m2`/`bgf_m2`/`envelope_area_m2`/`storeys_above/below_ground` | soweit aus Geometrie aggregierbar (§4) | IFC |

`input.rooms[]` (aus `IfcSpace`): **abhängig von OFFEN-4.** Drei mögliche Verträge:
- **(A) Räume deferren** — wie Boundaries. Geometrisch ehrlich, aber IfcSpace-Flächen gehen im `draft` verloren; Empfehlung nur, wenn `heating_status` streng als Anreicherung gilt.
- **(B) Räume mit Platzhalter** — `heating_status = "heated"` als dokumentierter Platzhalter, den der Assistent bestätigen muss (z.B. begleitet von einem Validator-Befund `HEATING_STATUS_ASSUMED`). Geometrie bleibt erhalten; verletzt aber „keine Anreicherung erfinden".
- **(C) Schema-Fix** — `heating_status` optional/mit `default` machen (Major-relevant, Master + Cross-Repo).

**Empfehlung der Rolle `din18599`:** **(B)** als Übergang, mit explizitem Platzhalter-Flag + Validator-Warnung, weil IfcSpace-Geometrie (Fläche, Höhe, Geschosszuordnung, Nummer) ein zu wertvoller Skelett-Bestandteil ist, um sie zu deferren — kombiniert mit dem Ziel, mittelfristig **(C)** sauber zu lösen. **Locken durch Master (OFFEN-4).**

### 2.3 Was der Parser bewusst LEER/DEFERRED lässt (mit Begründung)

| Feld/Bereich | Grund |
|---|---|
| `input.boundaries[]` | `adjacency_type` + `space_a` = Anreicherung (§1.1). Ganze Angrenzungsmatrix entsteht im Assistenten/der Engine. |
| `element_group.construction_ref` | Auflösung Bauteil→Konstruktion + `u_value` = Anreicherung/Rechenkern. |
| `element_group.u_value`, `delta_u_wb`, `edges[]` | Thermik/Wärmebrücken = Rechenkern. |
| `boundary.fx`, `.orientation`, `.tilt`, `.area_18599` | entstehen erst mit den Boundaries. |
| `construction[].sequences[].layers[].lambda`/`.density`/`.heat_capacity`, `construction.u_value` | Kennwerte = Katalog-Inhalt (Rolle `energiekatalog`), nicht Parser. |
| `room.room_type_ref`, `.theta_*`, `.zone_memberships[]`, `.ventilation_function` | Raumtyp/θ/Zonen = Anreicherung. |
| `input.zones[]` | Zonierung = fachliche Anreicherung. |
| `input.systems`, `.climate` (über TRY hinaus), `primary_energy_factors`, `output` | keine Geometrie. |
| Tolerante Gruppierung in `element_groups` | algorithmische Anreicherungsregel (§1.2). |

### 2.4 element_group-Objekt im `draft` (Form)

Gefüllt: `id` (generiert, z.B. `W-0001`), `element_type` (§4-Mapping), `fingerprint{normal_x, normal_y, normal_z, dist_m, coordinate_system:"project", tolerance{angle_tolerance_deg, dist_tolerance_m}}` (Toleranzwerte dokumentieren, mit welchen Defaults **gerechnet würde**, ohne zu gruppieren — Empfehlung: Schema-Defaults 1.0/0.02 eintragen), `member_elements[0]{source_id: GlobalId, source_kind:"ifc_guid", type_name, area_m2}`, `aggregates{member_count:1, boundary_count:0, area_total_m2}`.
Leer: `construction_ref`, `u_value`, `delta_u_wb`, `din_code`, `catalog_ref`.

> **Präzisions-Pflicht:** `fingerprint.normal_*`/`dist_m` in **voller** Rechenpräzision serialisieren, keine Anzeige-Rundung (Schema-Doku Z. 463). Das ist ein echter Parser-Bug-Kandidat, weil der Alt-Parser auf 1 Nachkommastelle rundet (`ifc_parser.py:357`).

---

## 3. Provenienz & Level — konkrete Belegung

```
meta.source        = { "origin": "IFC_PARSER", "tool": "<parser-name>", "tool_version": "<x.y.z>" }
meta.validation    = { "level": "draft", "validated_at": "<iso>", "ruleset_version": "<validator-x.y>" }
manifest.validation.level = "draft"   (falls Manifest geschrieben wird, OFFEN-6)
```
Per-Feld-Provenienz: **nicht abbildbar** (§1.5 / OFFEN-3).

---

## 4. IFC-Entity → v4.0-Feld — Mapping-Tabelle

**Legende Quelle:** `RW` = aus `api/parsers/ifc_parser.py` reuse-fähig · `NEU` = v4.0-Strukturierung, im Alt-Parser nicht vorhanden.

| IFC-Entity / -Attribut | v4.0-Sidecar-Feld | Quelle | Anmerkung |
|---|---|---|---|
| `IfcProject.Name` | `meta.project_name` | RW (`parse_ifc`, Z. 63-64) | Fallback Dateiname |
| `IfcBuilding.GlobalId` | `meta` (Doku) / `input.building` | RW (Z. 71, 169-170) | keine dedizierte GUID-Senke am building |
| `IfcBuilding` (Existenz) | `input.building` (Objekt) | RW | `type` bleibt OFFEN-5 |
| `IfcBuildingStorey.GlobalId` | `storeys[].ifc_guid` (Z. 286) | NEU | Alt-Parser nutzt nur `.Name` als String |
| `IfcBuildingStorey.Name` | `storeys[].name` (required, Z. 283) | RW (Z. 205-208) | |
| `IfcBuildingStorey.Elevation` | `storeys[].elevation_m` (Z. 288) | NEU | |
| Geschoss-Höhe (aus Geometrie/Nachbar-Elevation) | `storeys[].height_m` (Z. 292) | NEU | optional |
| Geschoss unter Gelände (Heuristik Elevation<0) | `storeys[].below_ground` (Z. 293) | NEU | geometrische Heuristik, kein Fachurteil |
| `IfcWall` (+`IfcWallStandardCase`) | `element_group{element_type:"wall"}` | RW (Z. 86-90) | 1:1-Gruppe |
| `IfcSlab` + `PredefinedType=FLOOR/BASESLAB/ROOF` | `element_group{element_type: floor/slab_ground/roof}` | RW (Z. 118-122, `predefined_type` Z. 200-201) | Mapping PredefinedType→`element_type`-Enum (Z. 452-454); Feinunterscheidung `slab_ground`/`slab_basement`/`ceiling` ist **teils Anreicherung** → nur setzen, was PredefinedType hergibt, sonst `other`/`floor`. → OFFEN-7 |
| `IfcRoof` (+ zugehörige `IfcSlab`s) | `element_group{element_type:"roof"}` | RW (Z. 93-115, `_calculate_roof_area_from_slabs`) | Flächenaggregation aus Slabs vorhanden |
| `IfcColumn`/`IfcBeam` | `element_group{element_type: column/beam}` | NEU | Enum deckt sie ab (Z. 454); Alt-Parser erfasst sie nicht |
| Element-`GlobalId` | `element_group.member_elements[].source_id` + `source_kind:"ifc_guid"` (Z. 511-514) | RW (Z. 188) | |
| Element-Typname (`IsTypedBy`/Name) | `member_elements[].type_name` (Z. 515) | RW (Z. 190) | |
| Ebenen-Normale (Kreuzprodukt) | `fingerprint.normal_x/y/z` (Z. 466-470) | RW (`_calculate_orientation_and_inclination`, Z. 316-360) | **volle Präzision**, nicht runden |
| Ebenen-Abstand vom Projektursprung (n·p) | `fingerprint.dist_m` (Z. 472) | NEU | Alt-Parser rechnet Normale, aber **nicht** `dist_m` — muss ergänzt werden |
| Projektsystem (nicht geo) | `fingerprint.coordinate_system:"project"` (const, Z. 478) | NEU | |
| Fläche (Mesh/BBox) | `element_group.aggregates.area_total_m2` (Z. 526) + `member_elements[].area_m2` | RW (`_calculate_area`, Z. 257-313) | |
| `IfcMaterialLayerSet` (Dicken + Materialnamen) | `constructions[]{source:"IFC", sequences[].layers[]{position, material, thickness_m, is_core_layer}}` (Z. 786-831) | RW (`ifc_material_extractor.extract_material_layers`, Z. 161) | **ohne** `lambda`/`u_value` (= Katalog). `origin_ref` = MaterialLayerSet-Id für Dedup (Z. 794-796) |
| `IfcSpace.GlobalId` | `rooms[].ifc_guid` (Z. 307) | NEU | nur falls Räume emittiert (OFFEN-4) |
| `IfcSpace.Name`/`.LongName`/`.Number` | `rooms[].name`/`.number` (Z. 308-309) | NEU | |
| `IfcSpace` → `IfcBuildingStorey` (`ContainedInStructure`) | `rooms[].storey_ref` (Z. 310) | RW-Muster (Z. 205-208) | |
| `IfcSpace`-Fläche/-Höhe (Geometrie, **nicht** `IfcSpace.Volume`) | `rooms[].area_ngf_m2` (Z. 365), `.height_m` (Z. 366) | NEU | gemeldetes Volumen nur nach `volume_reported_m3` (Z. 371), **nie** Rechenquelle (Schema-Doku Z. 373) |
| `IfcSpace` Konditionierung | `rooms[].heating_status` (required) | — | **NICHT** ableitbar → OFFEN-4 |
| `IfcWindow` / `IfcDoor` | `boundary.openings[]` | — | **DEFERRED**: Openings leben an Boundaries (Z. 614-618), die es im `draft` nicht gibt. Parent-Child-Relation (`_extract_parent_child_relationships`, Z. 410-446) ist reuse-fähig, sobald Boundaries entstehen. → OFFEN-8 |
| `IfcSite` Lat/Long | `input.climate.latitude`/`longitude` (Z. 1035-1036) | RW (Z. 67-68) | optional, geometrisch/geografisch |
| True-North (`IfcGeometricRepresentationContext.TrueNorth`) | `meta.true_north_offset_deg` (Z. 147) | NEU | **wichtig**: nötig, damit `orientation` geografisch korrekt wird (Z. 151); solange keine Boundaries, nur dokumentarisch |

**Kernaussage der Tabelle:** Geometrie-Kern (Flächen, Normalen, Material-Layer, Parent-Child) ist aus `ifc_parser.py` **wiederverwendbar**; **neu** ist die v4.0-Strukturierung (`element_groups`-1:1 mit `fingerprint.dist_m`, `storeys[]`-Objekte, `rooms[]`-Objekte, `constructions[]`-Skelett) und die volle Präzisions-Serialisierung.

---

## 5. Reuse aus `api/parsers/ifc_parser.py`

**Wiederverwenden (reine Geometrie):**
- `_extract_element` / `parse_ifc` — Element-Iteration über `IfcWall/Roof/Slab/Window/Door` (Z. 86-136).
- `_calculate_area` (Mesh-Heron für geneigte Flächen, BBox für Wände; Z. 257-313).
- `_calculate_orientation_and_inclination` — Normale via Kreuzprodukt (Z. 316-360) → Basis für `fingerprint.normal_*`.
- `_calculate_roof_area_from_slabs` (Z. 363-391).
- `_extract_parent_child_relationships` (Z. 410-446) — für spätere Openings.
- `ifc_material_extractor.extract_material_layers` (Z. 11, 161) — für `constructions[]`-Skelett.
- Geschoss-Auflösung `ContainedInStructure` (Z. 205-208).

**Neu bauen:**
- `fingerprint.dist_m` (Ebenen-Abstand n·p) — im Alt-Parser nicht vorhanden.
- **Volle Präzision** statt `round(...,1/2)` (Z. 292, 310, 357).
- 1:1-`element_group`-Strukturierung inkl. `aggregates`.
- `storeys[]`-, `rooms[]`-, `constructions[]`-Objekt-Mapping auf v4.0.
- `meta`/`schema_info`/`validation.level`/`source`-Kopf.
- **Kein** Legacy-`sidecar_generator` (v3.x-Envelope) berühren.

**Nicht wiederverwenden:** `print()`-Debug-Ausgaben mit Emoji (Z. 112, 139, 232, …) verletzen die Repo-Regel „keine Emojis" — beim Neu-Bau weglassen/durch `logging` ersetzen.

---

## 6. Endpunkt / Integration

Neuer, eigenständiger Endpunkt (Vorschlag) `POST /parse-ifc-to-sidecar` — nimmt **nur** `ifc_file: UploadFile = File(...)`, kein `evebi_file`. Gibt v4.0-Sidecar (`draft`) zurück. Der Alt-Endpunkt `/generate-sidecar` (IFC+EVEBI) bleibt für den EVEBI-Weg unberührt oder wird separat abgelöst (nicht Teil dieser Spec).
Ob der Parser zusätzlich ein `manifest.json` (`validation.level:"draft"`) und einen `.dwe`-Container schreibt oder nur das nackte Sidecar-JSON liefert, das die DWEapp in `buildings_v2.sidecar` ablegt: → **OFFEN-6**.

---

## 7. NICHT-ZIELE (ADR-033-Grenze, explizit)

Der Parser tut **nicht**:
1. **Keine Angrenzungen** — `boundaries[]`, `adjacency_type`, `space_a/space_b`, `boundary_condition`, `measurement_reference`, `relevant_18599`.
2. **Keine Konditionierung** — er erfindet kein `heating_status`, `outside_thermal_envelope`, `conditioned`. (Der Platzhalter in Variante B ist ein **markierter Nicht-Wert**, keine Berechnung — und selbst der steht unter Master-Vorbehalt, OFFEN-4.)
3. **Keine Raumtyp-/Nutzungs-Anreicherung** — kein `room_type_ref`, `usage_profile_ref`, `theta_*`, `ventilation_function`, keine Zonen (`zones[]`, `zone_memberships[]`).
4. **Keine Thermik** — kein `u_value`, `lambda`, `g_value`, `delta_u_wb`, `fx`, `edges[]`/Psi, `envelope_kpis`.
5. **Keine tolerante Gruppierung** — 1:1-Gruppen; die 1°/2 cm-Vereinigung ist Sache der Core-Engine.
6. **Keine Katalog-Auflösung** — keine `construction_ref`/`catalog_ref`/`room_type_ref`-Verknüpfung, keine Kennwerte (Rolle `energiekatalog`).
7. **Keine Anlagentechnik, kein Klima über Geo hinaus, kein `output`, keine Szenarien/Förderung.**
8. **Keine Bilanz-/Massbezugs-Umrechnung** — Roh-Geometrie, kein Achsmass/Aussenmass.

---

## 8. Definition-of-Done (Cross-Repo-Vertrag)

Dieser Parser ist **Neuentwicklung gegen ein bestehendes Schema** (v4.0), **kein Schema-Bump**. Die 5-Punkte-DoD des Sidecar-Vertrags gilt daher nur teilweise — der Vollständigkeit halber der Stand:

| # | DoD-Punkt (Schema-Bump) | Relevanz hier | Stand |
|---|---|---|---|
| 1 | Artefakt `schema/vX.Y-complete.json`, abwärtskompatibel | **entfällt** — Schema v4.0 existiert bereits, wird nicht geändert (Ausnahme: falls OFFEN-4 Variante C gewählt → dann echter v4.0-Minor mit voller DoD) | offen abhängig von OFFEN-4 |
| 2 | Herausgeber-Doku (CHANGELOG/MIGRATION/CLAUDE/ROADMAP/DB) | nur falls Schema-Fix (C) | offen |
| 3 | Konsumenten-Verdrahtung DWEapp (`package.json` + `schema-check.mjs`) | nur falls Schema-Fix | offen |
| 4 | Typen regeneriert (`schema:generate`, `schema:check`, `tsc`) | nur falls Schema-Fix | offen |
| 5 | Dossier `02-datenmodell.md`/`03-integrationen.md` | **ja** — Eingangs-Kanal 2 dokumentieren (`08-eingangs-kanaele.md` §Kanal 2) | offen |

**Nachweis-DoD für den Parser selbst (verbindlich beim Bau):**
1. **Schema-Validierung des Outputs** — jeder erzeugte `draft`-Sidecar besteht `python tools/dwe_validate.py` Stufe `draft` (Exit 0; = `Draft7Validator` grün, `tools/dwe_validate.py:106-118`).
2. **Referenz-IFC** — Test gegen **mindestens eine** echte IFC (Kandidat: die IFC hinter `examples/v4.0/beispiel1/`, falls vorhanden — sonst Master stellt eine bereit → OFFEN-9). Erwartung: Level `draft` erreicht, `BOUNDARIES_EMPTY`-Warnung erwartet und toleriert.
3. **Golden-Output** — der erzeugte Sidecar wird als Golden-File eingecheckt; ein Parser-Roundtrip-Test (IFC→Sidecar) vergleicht gegen das Golden (Parser-Roundtrip-Review-Standard: Spalten-/Feld-Diff + Idempotenz zweier Läufe).
4. **Idempotenz** — zweimaliges Parsen derselben IFC ergibt identische `element_group`-Fingerprints (member_elements dürfen driften, Z. 508).
5. **DWEapp-Konsum** — das Sidecar validiert gegen die aus v4.0 generierten Typen (`src/types/din18599.generated.ts`); da der Konsument laut Vertrag noch auf v3.0 zeigt, ist das **abhängig vom Cutover** (`docs/v4/TICKET_dweapp_cutover.md`) → nicht durch diesen Parser lösbar, nur zu melden.

---

## 9. OFFENE MASTER-ENTSCHEIDUNGEN (zum Locken durch Sebi/Master)

Nicht geraten — das Schema lässt diese Punkte offen bzw. der Auftrag widerspricht dem Repo-Stand.

- **OFFEN-1 — ADR-033 fehlt.** Die als bindende Leitplanke zitierte ADR-033 existiert im Repo nicht. Bitte anlegen oder auf die reale Quelle verweisen. Ohne sie ist die exakte „Parser vs. Anreicherung"-Grenze an Grenzfällen (OFFEN-4, OFFEN-7) nicht dokumenten-fest.
- **OFFEN-2 — Level `grouped` existiert nicht.** Auftrag nennt Level `grouped`; Schema-Enum ist `draft/enriched/geometry_ok/balanced/calc_ready`. Wo läuft die tolerante Gruppierung — innerhalb `enriched`, oder braucht das Schema ein neues Level? (Schema-Änderung = Major-relevant.)
- **OFFEN-3 — Per-Feld-Provenienz.** Schema trägt nur `meta.source.origin` global. Soll „authored vs. assistiert pro Feld" überhaupt im Sidecar leben (Schema-Erweiterung) oder DWEapp-DB-seitig (`building_versions_v2`-Audit)? Empfehlung: DB-seitig, Sidecar bleibt schlank.
- **OFFEN-4 — `room.heating_status` (required, Anreicherung).** Variante A (Räume deferren) / B (markierter Platzhalter `heated` + Validator-Warnung) / C (Schema-Fix optional/default). **Empfehlung B**, Ziel C. **Zentrale Entscheidung** — bestimmt, ob IfcSpace-Geometrie im `draft` überlebt.
- **OFFEN-5 — `building.type` (required, Enum, nicht geometrisch).** Default `non_residential`? Aus IFC-Heuristik? Oder aus dem Stammdaten-Wizard (Kanal 1), der ohnehin vor dem IFC-Upload läuft, und der Parser **merged** nur? Empfehlung: Wizard ist Quelle, Parser überschreibt `type` nicht.
- **OFFEN-6 — Output-Form.** Nacktes Sidecar-JSON (in `buildings_v2.sidecar`) oder vollständiger `.dwe`-Container inkl. `manifest.json` + `model.ifc`? Bestimmt, ob der Parser auch das Manifest-Schema bedient.
- **OFFEN-7 — Slab-Feinklassifikation.** `element_type`-Enum trennt `floor`/`ceiling`/`slab_ground`/`slab_basement`. Was davon ist aus `IfcSlab.PredefinedType`+Geometrie ableitbar (Parser), was ist Anreicherung? Vorschlag: nur `PredefinedType`-Direktabbildung im Parser, Rest `floor`/`other`, Verfeinerung im Assistenten.
- **OFFEN-8 — Openings ohne Boundaries.** `IfcWindow`/`IfcDoor` haben im v4.0-Schema **keinen** Platz außerhalb von `boundary.openings[]`. Im `draft` (ohne Boundaries) gibt es also keinen Ort für Fenster/Türen. Akzeptiert (Fenster kommen mit den Boundaries im Assistenten)? Oder braucht es einen `draft`-Zwischenspeicher? Empfehlung: akzeptieren, Parent-Child-Relation für später vormerken.
- **OFFEN-9 — Referenz-IFC.** Für DoD-Punkt 2 wird eine echte Test-IFC gebraucht. Liegt eine im Repo (Quelle von `beispiel1`)? Falls nicht, bitte bereitstellen.
- **OFFEN-10 — Zuständigkeit Parser-Doppelung.** EVEBI-Parser existiert doppelt (hier `api/qng/parser_*.py`, DWEapp `src/server/lib/evebi-parser-*.ts`). Dieser IFC-Parser ist **neu** und hat (noch) kein TS-Gegenstück — soll er als reiner Service-Endpoint bleiben (kein Zweit-Bau in der DWEapp)? Empfehlung: ja, Single-Home in `din18599-ifc`.

---

## 9.1 Master-Review — Gelockte Entscheidungen (2026-07-24, Sebi)

Die 10 OFFEN-Punkte aus §9 sind entschieden. Diese Sektion ist ab jetzt bindend für die Umsetzung.

| # | Entscheidung | Begründung |
|---|---|---|
| OFFEN-1 | **RESOLVED** — ADR-033 existiert (`weclapp-manager` `docs/00-meta/DECISIONS/ADR-033-anreicherungsregel-quelle.md`, auf `main`). Der „fehlt"-Befund war ein Sicht-Artefakt (Repo stand auf fremdem Branch). | — |
| OFFEN-2 | **RESOLVED** — Kein Level `grouped`. Die tolerante Gruppierung passiert im Übergang `draft → enriched` in der geteilten Core-Engine; der Parser bleibt auf `draft` mit 1:1-Gruppen. | Schema-Enum hat nur `draft/enriched/geometry_ok/balanced/calc_ready`. |
| OFFEN-3 | **RESOLVED** — Per-Feld-Herkunft DB-seitig (`building_versions_v2`-Audit in DWEapp). Der Sidecar trägt nur `meta.source.origin` gebäudeweit. | Schema sieht keine Per-Feld-Provenienz vor; Sidecar bleibt schlank. |
| **OFFEN-4** | **LOCKED: Variante B jetzt / C später.** Der Parser setzt `room.heating_status` auf den Platzhalter `heated` + eine laute Validator-Warnung `HEATING_STATUS_UNCONFIRMED` (blockiert `geometry_ok`). Kein Schema-Eingriff jetzt. | B entsperrt den Parser ohne Schema-Minor. Der Platzhalter ist ungefährlich, **weil** ein `draft` mit `HEATING_STATUS_UNCONFIRMED` nicht auf `geometry_ok` klettern darf — der Assistent muss bestätigen, bevor gerechnet wird. C (Schema-Feld optional, abwärtskompatibel) fällt in den ohnehin fälligen DWEapp-v3.0→v4.0-Typ-Cutover. |
| OFFEN-5 | **LOCKED** — `building.type`: der Stammdaten-Wizard (Kanal 1) ist Quelle, der Parser **merged** nur und überschreibt `type` nicht. | Wizard läuft vor dem IFC-Upload; `type` ist nicht geometrisch. |
| OFFEN-6 | **LOCKED** — Output = nacktes Sidecar-JSON (in `buildings_v2.sidecar`). Der `.dwe`-Container ist die Revit-Export-Form, nicht die des IFC-Bootstrap. | — |
| OFFEN-7 | **LOCKED** — Slab: nur `IfcSlab.PredefinedType`-Direktabbildung im Parser; Rest `floor`/`other`; `floor/ceiling/slab_ground/slab_basement`-Feinklassifikation im Assistenten. | Feinklassifikation ist Anreicherung. |
| OFFEN-8 | **LOCKED** — Openings ohne Boundaries: akzeptiert (Fenster/Türen kommen mit den Boundaries im Assistenten). Parent-Child-Relation (`IfcWindow`→Wand) im Parser mitführen (z.B. in `member_elements`-Metadaten), damit der Assistent sie zuordnen kann. | Kein Boundary auf `draft` → kein Ort für Openings. |
| OFFEN-9 | **RESOLVED** — Referenz-IFCs liegen im Repo: primär `sources/IFC_EVBI/DIN18599TestIFCv4.ifc`. **Golden-Vergleich:** `/opt/dwe-revit/tests/fixtures/model.ifc` ist die IFC von **Beispiel1** — dafür existiert der Revit-authored v4.0-Sidecar; der Parser-Output muss geometrisch (Element-Zahlen, Flächen ±Toleranz) dazu passen. | Konvergenz-Nachweis IFC-Weg ↔ Revit-Weg. |
| OFFEN-10 | **LOCKED** — Single-Home in `din18599-ifc`, kein TS-Zweitbau in DWEapp. Der Parser bleibt Service-Endpoint. | Vermeidet die EVEBI-Parser-Doppelung. |

**Nächster Schritt:** Bau durch die Rolle `din18599` gegen diese gelockte Spec, auf eigenem Branch (Worktree-isoliert vom Energiekatalog-WIP).

---

## 10. Anhang — geprüfte Belege

- `schema/v4.0/sidecar.schema.json` (1394 Z.): Top-`required` Z. 8 · `input.required` Z. 34 · `meta` Z. 83-195 (`validation.level` 165-172, `source.origin` 181-192) · `building.required` 199 · `room.required` 300, `heating_status` 337 · `element_group.required` 448, `fingerprint` 461-491, `member_elements` 506-519, `aggregates` (readOnly) 521-543 · `boundary.required` 550 · `construction` 786-833 · `adjacency_type` 764-784.
- `schema/v4.0/manifest.schema.json`: `validation_level`-Enum + Semantik-Doku (draft = strukturell gültig).
- `examples/v4.0/beispiel1/energy.din18599.json`: `boundaries: []` leer, 13 `element_groups`, 23 `rooms`, `meta.source.origin: REVIT_DYNAMO`, `validation.level: enriched`.
- `examples/v4.0/beispiel1/manifest.json`: Befund `BOUNDARIES_EMPTY` (warning, `blocks_level: geometry_ok`).
- `tools/dwe_validate.py`: `STUFEN` Z. 43 · draft = `Draft7Validator` Z. 106-118 · `BOUNDARIES_EMPTY` Z. 323-326 · `FINGERPRINT_COLLISION` Z. 205-210.
- `api/parsers/ifc_parser.py` (583 Z.): Reuse-Punkte siehe §5.
- `api/main.py`: `/generate-sidecar` verlangt IFC+EVEBI Z. 181-195.
- **Nicht auffindbar:** `ADR-033-anreicherungsregel-quelle.md`; `08-eingangs-kanaele.md §8.A` (Dossier hat keinen `§8.A`-Abschnitt, Status „skelett").
