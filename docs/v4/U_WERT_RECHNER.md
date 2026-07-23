# U-Wert-Rechner — Verfahren und Befund am Altkatalog

> `tools/u_value.py` · DIN EN ISO 6946 · erster Rechenkern, der die Kataloge konsumiert
> **Stand:** 2026-07-21

---

## Was er tut

Rechnet aus dem Schichtaufbau einer Konstruktion den U-Wert und löst dabei
Materialkennwerte und Übergangswiderstände aus `catalog/core/` auf.

```bash
python3 tools/u_value.py --construction WALL_EXT_BRICK_WDVS_160
python3 tools/u_value.py --sidecar examples/v4.0/beispiel1/energy.din18599.json
python3 tools/u_value.py --audit-legacy-catalog
```

Er ist im Validator eingehängt: Konstruktionen mit angegebenem `u_value` werden
**gegengerechnet**, Abweichungen über 5 % melden `U_VALUE_MISMATCH` und blockieren
`calc_ready`.

### Zwei Verfahren

**Homogen** — alle Schichten durchgehend: `R_T = Rsi + Σ(d/λ) + Rse`, `U = 1/R_T`.

**Kombiniert** (DIN EN ISO 6946 §6.7) — für inhomogene Bauteile über `sequences[]`
mit Flächenanteilen:

```
R_upper = 1 / Σ(f_m / R_tot;m)                     Gl. (6), Parallelweg-Grenze
R_lower = Rsi + Rse + Σ_Schichten 1/Σ(f_m/R_mj)    Gl. (7), Reihenweg-Grenze
R_tot   = (R_upper + R_lower) / 2                  Gl. (5)
e       = (R_upper − R_lower) / (2·R_tot) · 100    Gl. (10), in Prozent
```

**Harte Anwendungsgrenze (§6.7.2.1):** Ist `R_upper / R_lower > 1,5`, gilt das
vereinfachte Verfahren **nicht**. Der Rechner liefert dann bewusst **kein Ergebnis**,
sondern einen Fehler mit Verweis auf das detaillierte Verfahren nach §5.3 — ein
Mittelwert wäre hier Scheingenauigkeit. Bei genau 1,5 beträgt der maximale Fehler 20 %.
Ab `e > 10 %` wird gewarnt, obwohl das Verfahren noch gilt.

Ebenfalls ausgeschlossen: Dämmschichten mit Wärmebrücken aus Metall. Metallische
Verbindungsmittel dürfen dagegen ignoriert und nachträglich nach Anhang F.3 korrigiert
werden.

`R_tot` wird als Endergebnis auf zwei Dezimalstellen gerundet mitgeführt (§6.7.2.2).

`R_lower` setzt deckungsgleiche Schichtung aller Abfolgen voraus. Ist das nicht
gegeben, fällt die Rechnung auf `R_upper` zurück und **sagt das** — eine ehrlich
benannte Näherung ist besser als ein falscher Mittelwert.

> **Warum das zählt:** Der Sparrenanteil verschlechtert einen Dachaufbau erheblich.
> Im Testfall 0,2358 gegen 0,1946 W/(m²K) — **+21 %**, wenn man die 10 % Sparren
> mitrechnet statt homogen zu tun. Das v4.0-`sequences[]`-Modell kann das
> ausdrücken, das flache `layers[]` des Altkatalogs nicht.

### Was er bewusst nicht kann

- **Fenster über Schichtwiderstände.** Ein Dreifachglas so zu rechnen liefert 4,85
  statt 0,70 W/(m²K), also **Faktor 7 daneben**. `berechne()` verweigert das
  ausdrücklich. Stattdessen gibt es `uw_fenster()` nach DIN EN ISO 10077-1 —
  siehe unten.
- **Erdreich.** Geliefert wird der Bauteil-U-Wert; der Erdreichwiderstand nach
  DIN EN ISO 13370 kommt in der Bilanz über Fx dazu.
- Korrekturen ΔU nach Anhang F (Befestigungen, Umkehrdach).

### Fenster: `uw_fenster()` nach DIN EN ISO 10077-1

Gleichung (2) ohne Sprossen:

```
Uw = (Ag·Ug + Af·Uf + lg·Ψg) / (Ag + Af)
```

`Ψg` kommt aus **Tabelle G.1** (typische Abstandhalter aus Aluminium oder Stahl),
abgeleitet aus Rahmenart (über Uf) und Glasart (über Ug — Anhang H wertet
Ug ≤ 2,0 als Glas mit niedrigem Emissionsgrad):

| Rahmenart | unbeschichtet | niedriger Emissionsgrad |
|---|---:|---:|
| Holz oder PVC (Uf ≤ 2,0) | 0,06 | 0,08 |
| Metall mit Trennung (2,2 ≤ Uf ≤ 3,8) | 0,08 | 0,11 |
| Metall ohne Trennung (Uf = 7,0) | 0,02 | 0,05 |

**Für Einfachverglasung ist Ψg = 0** — es gibt keinen Randverbund. Das ist über
`single_glazing=True` zu setzen; ohne dieses Flag rechnet sich ein Einfachfenster
systematisch zu schlecht.

Der sichtbare Glasumfang `lg` wird geschätzt, wenn er nicht vorliegt (beide
Kantenlängen mit der Wurzel des Glasflächenanteils skaliert).

**Validierung gegen Tabelle H.1** (Referenzfenster 1,23 × 1,48 m, Rahmenanteil 30 %):
**72 von 72 Stützstellen** innerhalb 0,06 W/(m²K). Die Näherung für `lg` ist damit
für den Regelfall belegt.

> Zur Tabelle selbst: die Spalte Uf = 2,6 verletzt in vier Zeilen die Monotonie
> (Uw muss mit Uf steigen). Da der Einbruch nur in dieser einen Spalte auftritt,
> ist es ein Artefakt der Textextraktion, kein Normwert — die Spalte bleibt aus
> der Validierung heraus.

---

## Befund: der Altkatalog ist nicht mit sich selbst konsistent

`python3 tools/u_value.py --audit-legacy-catalog` über die 24 Konstruktionen in
`catalog/constructions.json`:

| Ergebnis | Anzahl |
|---|---:|
| **reproduziert** (< 5 % Abweichung) | **2** |
| weicht ab | 16 (+3 nach Tabelle 8) |
| nicht rechenbar | 3 → **0** |
| falsches Verfahren (Fenster) | 3 |

**Die angegebenen `u_value_calculated` lassen sich aus den eigenen `layers[]`
überwiegend nicht nachrechnen.** Vier Ursachen, sortiert:

### 1. Fenster — falsches Verfahren (3 Stück)

`WINDOW_SINGLE/DOUBLE/TRIPLE_GLAZING` haben Schichtaufbauten, aus denen sich kein
Fenster-U-Wert ergibt. Das ist eine Kategorieverwechslung im Katalog, kein Rechenfehler.
Fenster gehören in `window_constructions[]` mit Ug/Uf/g/ψ — die v4.0-Struktur hat das
bereits.

### 2. Luftschichten haben kein λ (3 Stück) — gelöst

`MAT_AIR_LAYER_UNVENTILATED` und `MAT_AIR_LAYER_SLIGHTLY_VENTILATED` tragen kein
`lambda`. **Das ist richtig so** — eine Luftschicht hat keine sinnvolle
Wärmeleitfähigkeit, ihr Widerstand hängt von Dicke *und* Wärmestromrichtung ab.

Seit dem Katalog `air_layers` (DIN EN ISO 6946 Tabelle 8, mit linearer Interpolation)
sind alle drei rechenbar. Eine Schicht wird über `air_layer: true` als Luftschicht
markiert, alternativ trägt sie einen expliziten `r_value`:

| Konstruktion | Katalog | berechnet | Abweichung |
|---|---:|---:|---:|
| `ROOF_PITCHED_UNINSULATED` | 1,80 | 1,461 | −18,8 % |
| `ROOF_PITCHED_BETWEEN_RAFTERS_160` | 0,28 | 0,184 | −34,2 % |
| `FLOOR_TOP_UNINSULATED` | 1,40 | 1,258 | −10,1 % |

Sie fallen damit in Ursache 3 bzw. 4 — nicht mehr in „nicht rechenbar". Der
Zwischensparren-Fall mit −34 % ist der klassische Inhomogenitätsfall.

**Ebenfalls im Katalog, noch nicht verdrahtet:** die Regeln für schwach belüftete
Luftschichten (§6.9.3, lineare Überblendung über die Öffnungsfläche A_ve) und stark
belüftete (§6.9.4, Luftschicht und alles außerhalb wird verworfen), sowie Tabelle 9
mit den Widerständen unbeheizter Dachräume (R_u = 0,06 bis 0,30) für
`adjacency_type: attic_uninsulated`.

### 3. Der Dämmstoff im U-Wert ist ein anderer als in der Schicht

Nachgerechnet für die WDVS-Familie:

| Konstruktion | Katalog-U | mit λ der Schicht | mit λ = 0,040 |
|---|---:|---:|---:|
| `WALL_EXT_BRICK_WDVS_160` (EPS 032) | 0,21 | 0,174 | **0,210** |
| `WALL_EXT_BRICK_WDVS_200` (EPS 032) | 0,17 | 0,143 | **0,174** |
| `WALL_EXT_BRICK_WDVS_100` (EPS 035) | 0,32 | 0,277 | 0,308 |

Bei 160 mm trifft λ = 0,040 den Katalogwert **auf drei Stellen genau**. Die U-Werte
wurden offenkundig mit einem schlechteren Dämmstoff gerechnet, als die Schicht
referenziert — oder sie stammen aus einer generischen Tabelle „typisches WDVS" und
haben mit diesen Schichten nie etwas zu tun gehabt.

### 4. Inhomogenität fehlt

`ROOF_PITCHED_FULL_INSULATION_240` (−34 %) und `WALL_EXT_WOOD_FRAME_240` (−8 %)
rechnen sich homogen zu gut. Beides sind Konstruktionen mit Sparren bzw. Holzständern,
deren Flächenanteil das flache `layers[]` nicht ausdrücken kann. Der Katalogwert ist
hier vermutlich **richtiger** als meine homogene Rechnung — nur lässt sich das mit den
vorhandenen Daten nicht zeigen.

### Nachrechenbares Beispiel

```
WALL_EXT_BRICK_WDVS_160
  Kalkzementputz   0,005 m   λ 0,870   R 0,0057
  EPS 032          0,160 m   λ 0,032   R 5,0000
  Hochlochziegel   0,240 m   λ 0,450   R 0,5333
  Gipsputz         0,015 m   λ 0,350   R 0,0429
                                       Σ 5,5819
  R_T = 0,13 + 5,5819 + 0,04 = 5,7519 (m²K)/W
  U   = 1 / 5,7519 = 0,174 W/(m²K)          Katalog: 0,21
```

---

## Konsequenz

**Ich habe keinen einzigen Katalogwert korrigiert.** Bei 16 Abweichungen ohne geklärte
Ursache wäre jede „Korrektur" eine Wette. Die Diagnose steht, die Entscheidung nicht.

Zu klären ist je Konstruktion, welche Seite stimmt:

- Sind die **Schichten** falsch (falscher Dämmstoff referenziert)? → Schicht korrigieren.
- Sind die **U-Werte** aus einer Fremdquelle übernommen? → dann sind sie keine
  `u_value_calculated`, sondern Literaturwerte und gehören als solche gekennzeichnet —
  mit eigenem Feld, nicht als vermeintliches Rechenergebnis.

Sobald das entschieden ist, wird der Katalog auf das v4.0-Envelope-Format migriert
und `u_value` fällt weg, wo er sich aus den Schichten ergibt. Redundante
Speicherung eines ableitbaren Werts ist genau die Drift-Quelle, die dieser Befund
sichtbar macht.

---

## Offene Punkte

1. **C4-Entscheidung zu `air_layers` offen.** Der Katalog enthält 27 Zahlenwerte aus
   Tabelle 8 — deutlich mehr als die zwölf verstreuten Fx-Einzelfakten. Die Einordnung
   als gemeinfreie Einzelfakten ist hier weniger eindeutig. Bleibt vorerst öffentlich,
   weil die U-Wert-Berechnung eine Grundfunktion ist; bei anderer Einschätzung genügt
   ein Verschieben nach `catalog/values/` plus `values_overlay.required: true`.
2. **§6.9.3 und §6.9.4 sind katalogisiert, aber noch nicht im Rechner verdrahtet** —
   belüftete Luftschichten werden derzeit wie ruhende behandelt. Ebenso Tabelle 9
   (unbeheizte Dachräume) für `attic_uninsulated`.
3. **Flächenanteile für inhomogene Bauteile** — Sparren- und Ständeranteile sind
   konstruktionsspezifisch, keine Normwerte. Müssen je Konstruktion erfasst werden.
4. **λ-Herkunft geklärt (DIN 4108-4).** Tabelle 1 enthält **Bemessungswerte**,
   ermittelt nach DIN EN ISO 10456 bei 80 % rel. Luftfeuchte, 23 °C und 10 °C
   Mitteltemperatur. „Für wärmeschutztechnische Nachweise ist der Bemessungswert
   anzusetzen." Die μ-Werte sind dagegen ausdrücklich nur **Richtwerte** und
   „können erheblichen Schwankungen unterliegen".

   **Damit ist die WDVS-Abweichung erklärt — negativ.** Tabelle 2 beziffert den
   Aufschlag Nennwert → Bemessungswert für Dämmstoffe auf **+0,001 W/(mK)**
   (aus 0,032 wird 0,033; erst bei 0,050 sind es +0,002). Das sind rund 3 %,
   nicht die beobachteten 25 %. Die naheliegende harmlose Erklärung scheidet
   damit aus: die Katalog-U-Werte wurden mit einem **anderen Dämmstoff**
   gerechnet, nicht mit einem Sicherheitszuschlag.
5. **Fenster-Konstruktionen** aus `constructions.json` nach `window_constructions[]`
   überführen — der Rechenkern dafür steht jetzt (`uw_fenster()`).
   Nebenbefund aus DIN 4108-4 Tabelle 7: für Außentüren ohne Nachweis gelten
   pauschal 2,9 W/(m²K) (Holz, Holzwerkstoffe, Kunststoff) bzw. 4,0 (Metallrahmen
   mit metallenen Bekleidungen). Für Fenster gilt Bemessungswert = Nennwert
   nach DIN EN 14351-1.
6. **Envelope-Migration** von `constructions.json` und `materials.json` — steht
   ohnehin an (KATALOG_FORMAT.md, offener Punkt 5) und ist die Gelegenheit,
   `sequences[]` einzuführen.
