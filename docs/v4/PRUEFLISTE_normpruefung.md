# Prüfliste Normprüfung — offene Punkte für Sebi

> Zwei Sachverhalte, die nur gegen die lizenzierte Norm bzw. den Gesetzestext
> entschieden werden können. Bewusst **nicht** selbst aufgelöst.
> **Stand:** 2026-07-21

---

## 1. Profilanzahl: 45 im Bestand gegen 42 im Handoff

### Befund

| Quelle | Anzahl |
|---|---|
| `catalog/din18599_usage_profiles.json` (Altbestand v1.0, 28.03.2026) | **2 WG + 43 NWG = 45** |
| Ursprungs-Handoff §8.1 | „2018-09 mit **42** + 2025-10 mit **43** Profilen" |

**Die Nummerierung der NWG-Profile ist lückenlos 01 bis 43.** Es gibt keine Lücke,
keine Dublette, keinen Eintrag ohne `description` oder `name_en`. Aus den Daten allein
lässt sich also nicht ableiten, welche Einträge zu viel sind — deshalb keine Löschung.

### Die Zählbasis ist die erste offene Frage

Bevor man nach „den drei zusätzlichen Profilen" sucht, muss klar sein, was der
Handoff zählt:

- **Zählt er nur NWG?** Dann steht 43 (Bestand) gegen 42 (2018-09) → **ein** Profil
  zu viel. Auffällig: 43 ist exakt die Zahl, die der Handoff für **2025-10** nennt.
  Naheliegende Hypothese: der Altbestand trägt bereits die Liste der neueren Ausgabe,
  ist aber als `DIN/TS 18599-10:2018-09` deklariert.
- **Zählt er WG und NWG zusammen?** Dann steht 45 gegen 42 → **drei** zu viel.

### Konkret zu prüfen

Wenn die erste Hypothese stimmt, ist der wahrscheinlichste Kandidat der höchste
Zähler. Zu verifizieren gegen DIN V 18599-10:2018-09 Tabelle 6:

| Nr. | Name | Kategorie | Prüffrage |
|---|---|---|---|
| **43** | Tiefkühlhaus | storage | In 2018-09 enthalten oder erst 2025-10 ergänzt? |
| **42** | Intensivstation | healthcare | dito |
| **41** | OP-Bereich | healthcare | dito — trägt zusätzlich `parent_profile` (erbt Betriebszeiten) |

Ergänzend, falls die Zählung WG einschließt: sind `R1 Einfamilienhaus` und
`R2 Mehrfamilienhaus` in der Zählung „42" überhaupt enthalten? Sie stehen in
Tabelle 5, nicht in Tabelle 6.

### Was passiert nach deiner Entscheidung

Der Katalog wird per Generator neu erzeugt, das ist ein Einzeiler:

```bash
python3 scripts/build-usage-profiles-catalog.py --edition 2018-09
```

Für die Ausgabe 2025-10 läuft derselbe Generator, sobald deren Profilliste vorliegt.
Solange die Frage offen ist, bleibt `catalog/core/usage_profiles.2018-09.json` mit
45 Einträgen bestehen — überzählige Profile schaden nicht, fehlende schon.

---

## 2. GEG-Referenzwerte

### Rechtslage geklärt, Werte offen

Deine Einschätzung ist übernommen: das GEG ist ein amtliches Werk nach § 5 UrhG und
damit gemeinfrei. Die Referenzwerte dürfen öffentlich in `catalog/core/` stehen —
anders als DIN-Tabellenwerte.

**Trotzdem sind sie nicht eingetragen.** Ich habe in dieser Session keinen belegten
Zugriff auf den Gesetzestext bzw. den Bundesanzeiger. Werte aus dem Gedächtnis oder
aus Sekundärquellen einzutragen wäre bei einer Nachweisgröße das falsche Risiko —
sie sähen autoritativ aus und würden ungeprüft in GEG-Nachweise wandern.

### Was zu liefern ist

Je Zeile ein U-Wert, bei den transparenten Zeilen zusätzlich der g-Wert, jeweils mit
Fundstelle als `norm_cell`:

| `code` | Bauteil | benötigt | Fundstelle |
|---|---|---|---|
| `1.1` | Außenwand gegen Außenluft | `u_value` | GEG 2024 Anlage 1, Zeile 1.1 |
| `1.2` | Außenwand/Bodenplatte gegen Erdreich oder unbeheizt | `u_value` | Anlage 1, Zeile 1.2 |
| `1.3` | Dach / oberste Geschossdecke | `u_value` | Anlage 1, Zeile 1.3 |
| `2` | Fenster, Fenstertüren, verglaste Türen | `u_value` + `g_value` | Anlage 1, Zeile 2 |
| `3` | Dachflächenfenster | `u_value` + `g_value` | Anlage 1, Zeile 3 |
| `4` | Lichtkuppeln | `u_value` + `g_value` | Anlage 1, Zeile 4 |
| `5` | Außentüren | `u_value` | Anlage 1, Zeile 5 |

Format je Eintrag — `value_pending` fällt weg, sobald der Wert steht:

```json
{ "code": "1.1", "u_value": null, "norm_cell": "GEG2024-A1-Z1.1", "value_pending": true }
```

Das Entry-Schema erzwingt bereits: sobald `value_pending: false` gesetzt wird, **muss**
`u_value` vorhanden sein.

### Zusätzlich offen

- **GEG Anlage 2 (Nichtwohngebäude) fehlt vollständig.** Dort ist das Referenzgebäude
  zonenweise definiert, die Zeilenstruktur ist eine andere. Entweder ein zweiter
  Katalog `geg_reference_building_nwg.2024.json` oder eine `applicability`-Dimension
  im bestehenden.
- **Wärmebrückenzuschlag und Luftdichtheit** des Referenzgebäudes sind noch nicht
  abgebildet.

---

## 3. DIN 277 — zur Erinnerung

`room_types[].mapping.din_277_category` ist für alle 61 Einträge `null`. Laut deinem
Feedback lieferst du die Zuordnung nach der Normprüfung nach. Kein Blocker: der
Katalog ist ohne diese Spalte nutzbar, sie wird für Flächenauswertungen nach DIN 277
gebraucht, nicht für die Energiebilanz.
