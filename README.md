# IFC + DIN 18599 Sidecar
**Ein offenes Austauschformat für die energetische Gebäudeakte in Deutschland**

> **Status:** Draft / Request for Comments (RFC)  
> **Lizenz:** MIT  
> **Repository:** [github.com/DWEBeratungGmbH/din18599-ifc](https://github.com/DWEBeratungGmbH/din18599-ifc)

## 🎯 Zielbild

Wir definieren einen **software-neutralen Datenstandard** für die energetische Gebäudeakte.
Ziel ist die Entkopplung von **Geometrie** (BIM/IFC), **physikalischer Beschreibung** (Sidecar) und **Berechnung** (Software).

Ein Energieberatungsprojekt besteht künftig aus mindestens zwei Dateien:

1.  **`gebaeude.ifc`** (Standard IFC4/IFC5)
    *   **Inhalt:** Reine Geometrie, Bauteilstruktur, Raumgeometrie.
    *   **Rolle:** Bleibt "dumm" (keine komplexe Physik, keine Heizungslogik, keine proprietären Psets).
    *   **Kompatibilität:** Lesbar mit jedem BIM-Viewer.

2.  **`gebaeude.din18599.json`** (Sidecar)
    *   **Inhalt:** Zonierung, bauphysikalische Qualitäten, Anlagentechnik, Varianten, iSFP.
    *   **Rolle:** "Veredelt" das IFC-Modell mit der energetischen Intelligenz.
    *   **Referenz:** Verknüpft Eigenschaften via GUID mit den IFC-Objekten.

**Das Ziel:** Ein Architekt exportiert ein IFC, der Energieberater ergänzt es mit dem Sidecar (Zonen, U-Werte, Technik), und jede Fachsoftware kann das Projekt verlustfrei lesen und weiterberechnen.

---

## 📦 Scope & Datenmodell

Das Datenmodell ist strikt in **Eingabedaten (Input)** und **Ergebnisdaten (Output)** unterteilt. Dies gewährleistet Interoperabilität, ohne die Berechnungshoheit der Fachsoftware anzutasten.

### 1. Eingabedaten (The Definition)
Alle Parameter, die notwendig sind, um eine Norm-Berechnung (z.B. DIN 18599) zu starten. Dies ist der "Source of Truth" für den energetischen Zustand.

*   **Topologie & Zonierung:**
    *   Gruppierung von IFC-Räumen zu **thermischen Zonen** nach DIN 18599-1.
    *   Definition von **Nutzungsprofilen** (DIN 18599-10).
    *   **Nachbarschaften (Adjacencies):** Definition der Randbedingungen für Bauteile (Außenluft, Erdreich, Unbeheizt), entscheidend für Temperatur-Korrekturfaktoren ($F_x$).

*   **Bauphysik (Hülle):**
    *   Ergänzung der IFC-Elemente um energetisch relevante Attribute.
    *   **Hülle:** U-Werte, Schichtaufbauten (optional), Wärmebrückenzuschläge ($\Delta U_{WB}$).
    *   **Material:** Referenzierung auf Ökobilanz-Datenbanken (z.B. Ökobaudat) für QNG/LCA-Nachweise.
    *   **Fenster:** $g_{tot}$-Werte, Rahmenanteile, detaillierte Verschattungsfaktoren.

*   **Anlagentechnik (Systeme):**
    *   Strukturiertes Modell für Erzeuger, Speicher, Verteilung und Übergabe (DIN 18599 Teil 5-9).
    *   **Detailtiefe:** Erfassung von Baujahr, Energieträger, Wirkungsgraden (z.B. COP-Kennlinien), Kältemittel (GWP) und Regelungsstrategien.

### 2. Ergebnisdaten (The Snapshot)
Die resultierenden Bilanzwerte eines Berechnungslaufs. Dies ermöglicht die Nutzung in Drittsystemen (ERP, Förderantrag, Dashboard), ohne dass diese über einen eigenen Rechenkern verfügen müssen.

*   **Bedarf:** Endenergie, Primärenergie, Nutzenergie (aufgeschlüsselt nach Gewerken: Heizung, WW, Kühlung, Licht).
*   **Bewertung:** CO₂-Emissionen, Primärenergiefaktoren, Effizienzklassen (GEG).
*   **Status:** Metadaten zur Berechnung (verwendete Software, Norm-Version, Datum) zur Sicherung der Validität.

### 3. Der Rechenkern (Blackbox)
Der Standard beschreibt **Daten**, keine Algorithmen.
Der Rechenweg selbst (die "Blackbox") bleibt Aufgabe der zertifizierten Software-Kernel. Das Format stellt sicher, dass jede normkonforme Software die gleichen Eingabewerte erhält ("Lossless Roundtrip") und Ergebnisse einheitlich zurückschreibt.

---

## 🔄 Workflow-Integration

Das Format unterstützt den gesamten Lebenszyklus:

1.  **Bestandsaufnahme:** Erfassung des Ist-Zustands (Status Quo).
2.  **Variantenvergleich:** Definition von Sanierungsszenarien (Maßnahmenpakete) als Delta zum Ist-Zustand.
3.  **Sanierungsfahrplan (iSFP):** Zeitliche Einordnung der Maßnahmen in eine Roadmap.
4.  **Monitoring:** Vergleich von berechnetem Bedarf (Output) mit gemessenen Verbräuchen.

## Dateistruktur

```
projekt_musterstrasse1/
├── gebaeude.ifc                  ← Geometrie (IFC4, Standard)
├── gebaeude.din18599.json        ← DIN 18599 Sidecar (Input & Output)
└── assets/
    ├── fotos/
    └── dokumente/
```

## Lizenz

MIT License - Open Standard
