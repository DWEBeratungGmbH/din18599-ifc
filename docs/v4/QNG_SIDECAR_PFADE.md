# QNG-Sidecar-Pfade — Ist-Bestand und v4.0-Deckung

> **Zweck:** Review-Auflage C. Dokumentiert, welche Dot-Pfade die QNG-Pipeline heute
> ungeprüft ins Sidecar patcht, und welche davon v4.0 abdeckt. **Nur Dokumentation —
> hier wird nichts gefixt.** Input für den LCA-Katalog-Block.
> **Stand:** 2026-07-21

---

## Wie die Pfade ins Sidecar kommen

Die QNG-Parser (`api/qng/parser_*.py`) liefern ein Dictionary `ki_extrahiert`, dessen
**Schlüssel Dot-Pfade ins Sidecar sind**. Bei der Auditor-Freigabe schreibt DWEapp sie
per generischem Pfad-Setter hinein:

```ts
// weclapp-manager/src/server/api/routers/qng.ts:108
function applyKiExtrahiertToSidecar(sidecar, kiExtrahiert, korrekturen) {
  for (const [pfad, entry] of Object.entries(kiExtrahiert)) {
    const wert = korrMap.has(pfad) ? korrMap.get(pfad) : entry.wert
    result = applyDotPath(result, pfad, wert)   // <- keine Schema-Prüfung
  }
}
```

`applyDotPath` legt fehlende Zwischenebenen an. **Jeder Tippfehler in einem Parser
erzeugt damit stillschweigend einen neuen Ast im Sidecar**, den kein Schema kennt und
kein Validator bemerkt. Das ist die strukturelle Ursache dafür, dass unten überhaupt
Pfade stehen, die es im Schema nie gab.

---

## Vollständige Pfadliste

Legende: **OK** = in v4.0 vorhanden · **UMBENANNT** = Feld existiert, heißt anders ·
**FEHLT** = in v4.0 nicht abgedeckt · **INTERN** = bewusst kein Schema-Pfad

### Gebäude-Kenngrößen

| Pfad (heute) | Quelle | v4.0 | Ziel in v4.0 |
|---|---|---|---|
| `input.building.gross_floor_area` | `parser_beg_geg_xml`, `parser_nachhaltigkeit_docx` | **UMBENANNT** | `input.building.bgf_m2` |
| `input.building.heated_area` | `parser_beg_geg_xml`, `parser_idi_al_ini`, `parser_nachhaltigkeit_docx` | **UMBENANNT** | `input.building.ngf_m2` |

> Achtung, inhaltliche Unschärfe: `heated_area` wird von `parser_nachhaltigkeit_docx`
> aus **NRF** befüllt (`"nrf_m2": "input.building.heated_area"`), von anderen Parsern
> als beheizte Fläche. In v4.0 ist `ngf_m2` klar als Nettogrundfläche nach DIN 277
> definiert. **Vor dem Cutover fachlich klären, welche Größe wirklich gemeint ist** —
> ein reines Umbenennen würde die Unschärfe mitnehmen.

### Adresse

| Pfad (heute) | v4.0 | Ziel in v4.0 |
|---|---|---|
| `meta.address.street` | **UMBENANNT** | `input.building.address.street` |
| `meta.address.postcode` | **UMBENANNT** | `input.building.address.zip` |
| `meta.address.city` | **UMBENANNT** | `input.building.address.city` |

Die Adresse lag schon in v3.x unter `input.building.address`, nicht unter `meta`.
`meta.address.*` ist ein Pfad, den **nur die QNG-Pipeline erfunden hat** — er existiert
in keinem veröffentlichten Schema. Zusätzlich heißt das Feld dort `zip`, nicht `postcode`.

### Ökobilanz (LCA) — der große Block

| Pfad (heute) | v4.0 |
|---|---|
| `output.base.lca.gwp_a1_a3` / `pene_a1_a3` | **FEHLT** |
| `output.base.lca.gwp_b4` / `pene_b4` | **FEHLT** |
| `output.base.lca.gwp_b6_gesamt` / `pene_b6_gesamt` | **FEHLT** |
| `output.base.lca.gwp_b6_heizung` | **FEHLT** |
| `output.base.lca.gwp_b6_kuehlung` | **FEHLT** |
| `output.base.lca.gwp_b6_tww` | **FEHLT** |
| `output.base.lca.gwp_c3_c4` / `pene_c3_c4` | **FEHLT** |
| `output.base.lca.gwp_d` / `pene_d` | **FEHLT** |
| `output.base.lca.gwp_gesamt` / `pene_gesamt` | **FEHLT** |
| `output.base.lca.qng_plus_gwp_anforderung` | **FEHLT** |
| `output.base.lca.qng_premium_gwp_anforderung` | **FEHLT** |

**17 Pfade, keiner davon in v4.0 gedeckt.** Die Struktur ist sauber nach
EN-15804-Lebenszyklusmodulen aufgebaut (A1–A3 Herstellung, B4 Ersatz, B6 Betrieb mit
Untergliederung Heizung/Kühlung/TWW, C3–C4 Entsorgung, D Gutschriften) plus
Gesamtwerte und die beiden QNG-Anforderungsschwellen.

**Das ist die konkrete Vorlage für den LCA-Block.** Empfehlung: `output.*.lca` als
eigene Definition mit `modules{}` je EN-15804-Modul, statt der heutigen flachen
`gwp_*`/`pene_*`-Namen — dann skaliert es auf weitere Indikatoren (AP, EP, ODP, POCP),
die QNG ebenfalls kennt und die hier noch fehlen.

### Energie-Kennwerte

| Pfad (heute) | v4.0 | Ziel in v4.0 |
|---|---|---|
| `output.base.specific_values.primary_energy.total` | **UMBENANNT** | `output.base.primary_energy.specific_kwh_m2a` |
| `output.base.specific_values.final_energy.total` | **UMBENANNT** | `output.base.final_energy.total_kwh_a` |
| `output.base.specific_values.co2_emissions.total` | **UMBENANNT** | `output.base.co2.specific_kg_m2a` |

> Auch hier eine Unschärfe: `specific_values.*.total` mischt spezifische Werte
> (pro m²) und Absolutwerte unter einem Namen. v4.0 trennt `total_kwh_a` von
> `specific_kwh_m2a`. Beim Mapping ist je Parser zu prüfen, welche Größe geliefert wird.

### Photovoltaik

| Pfad (heute) | v4.0 | Anmerkung |
|---|---|---|
| `input.electricity.pv_ertrag_kwh_a` | **TEILWEISE** | v4.0 hat `input.systems.electricity.pv[]` als Array mit `peak_power_kwp`, `orientation`, `tilt`, `self_consumption_share` — aber **kein Ertragsfeld** |

**Lücke:** Der Jahresertrag [kWh/a] ist ein Rechenergebnis, kein Eingabewert. In v4.0
gehört er nach `output`, nicht nach `input`. Vorschlag: `output.*.electricity.pv_yield_kwh_a`.
Bis dahin ist dieser Pfad nicht sauber abbildbar.

### Interne Prüf-Pfade (kein Schema-Ziel)

| Pfad | Zweck |
|---|---|
| `_check.gwp_abc` / `_check.pene_abc` | Plausibilitätscheck Summe A+B+C, im Parser als „kein offizieller Sidecar-Pfad" kommentiert |
| `_check.qng_anforderung_gwp` / `_check.qng_anforderung_pene` | QNG-Schwellwerte zum Abgleich |
| `_meta.projekt_name_elca` | Projektname aus der eLCA-Datei zur Zuordnung |

Diese fünf sind bewusst mit `_` präfigiert und sollen **nicht** ins Sidecar. Sie landen
aber trotzdem dort, weil `applyDotPath` nicht zwischen ihnen und echten Pfaden
unterscheidet — die Präfix-Konvention ist reine Absprache, nicht durchgesetzt.

---

## Bilanz

| Kategorie | Anzahl | Anteil |
|---|---:|---:|
| **OK** — unverändert übernehmbar | 0 | 0 % |
| **UMBENANNT** — Feld existiert, Mapping nötig | 8 | 28 % |
| **TEILWEISE** — Struktur da, Feld fehlt | 1 | 3 % |
| **FEHLT** — v4.0 deckt nicht ab (alles LCA) | 17 | 59 % |
| **INTERN** — soll gar nicht ins Sidecar | 5 | — |

**Kein einziger QNG-Pfad überlebt den v4.0-Cutover unverändert.** Das ist keine
Überraschung — v4.0 ist Greenfield — aber es bedeutet: der Cutover ist ein
Mapping-Projekt, kein Versions-String-Tausch.

---

## Drei Punkte, die über das Mapping hinausgehen

1. **`applyDotPath` braucht eine Whitelist.** Solange beliebige Pfade durchgehen,
   wiederholt sich das Problem bei jedem neuen Parser. Der v4.0-Validator kann die
   Whitelist aus dem Schema ableiten — dann wird aus der Konvention eine Prüfung.

2. **Der LCA-Block ist die größte inhaltliche Lücke in v4.0.** 17 Pfade mit sauberer
   EN-15804-Struktur liegen produktiv vor und haben kein Zuhause im Schema.

3. **Zwei fachliche Unschärfen sind vor dem Mapping zu klären:**
   `heated_area` (beheizte Fläche oder NRF?) und `specific_values.*.total`
   (spezifisch oder absolut?). Beide würden sonst als Fehler mitwandern.
