# Katalog-Strategie: Hersteller- und Produktdaten

**Stand:** 06.05.2026
**Status:** Strategie verabschiedet, Implementierung geplant Q3 2026

> **Leitsatz:** Wir docken an drei offene, behördlich oder gemeinnützig gepflegte
> Quellen an. Wir erfinden nichts nach, was es schon gibt. Wo es keine offene
> Quelle gibt — und das ist real der Fall für die Bauhülle — pflegen wir selbst.

---

## 1. Drei-Säulen-Strategie

| Säule | Quelle | Zweck im Sidecar | Identifier-Feld |
|-------|--------|------------------|-----------------|
| **LCA / EPD** | [ÖKOBAUDAT](https://www.oekobaudat.de) (BBSR) | Ökobilanz-Referenz für Materialien und Bauteile | `materials[].oekobaudat_uuid` + Version |
| **TGA-Energielabel** | [EPREL](https://eprel.ec.europa.eu) (EU-Kommission) | Eindeutige Produkt-ID für Heizung, Lüftung, WW, Klima | `systems[].eprel_id` |
| **Klassifikation / Properties** | [buildingSMART bSDD](https://search.bsdd.buildingsmart.org) | International anschlussfähige Klassifikation und Property-Definitionen | bSDD-GUID auf Material-, Element- und System-Ebene |

**Begründung:**
- Alle drei haben **echte REST-APIs**, kostenfreie Lizenzen, behördliche bzw. gemeinnützige Trägerschaft.
- Sie ergänzen sich orthogonal (LCA × Produktregister × Klassifikation), keine Doppelung.
- ETIM-Klassen sind in bSDD gespiegelt — wir docken über bSDD an, nicht zusätzlich an ETIM.

---

## 2. Bewertungstabelle (alle geprüften Quellen)

Skala: 1 = perfekter Andockkandidat, 5 = nicht relevant.

| Quelle | Träger | API offen? | Lizenz | Eignung | Bemerkung |
|--------|--------|-----------|--------|---------|-----------|
| **ÖKOBAUDAT** | BBSR/BMWSB | ✅ REST (Soda4LCA) | CC-frei mit Quelle | **1** | EPD-Daten, ~1.500–2.000 Datensätze. Read offen, Schreibzugriff via Token. |
| **EPREL** | EU-Kommission | ✅ REST (API-Key per Antrag) | Kostenfrei, public | **1** | Pflicht-Register seit 2019. Heizung/Lüftung/WW vollständig. **Fenster sind nicht in EPREL** (CPR-Welt, nicht Energy-Labelling). |
| **bSDD** | buildingSMART Int. | ✅ REST (SwaggerHub `Dictionaries/v1`) | Pro Dictionary unterschiedlich, Lesen offen | **1** | Klassifikations-Server. ETIM gespiegelt. STLB-Bau **nicht** vollständig integriert. |
| **VDI 3805** / ISO 16757 | VDI + Hersteller-Konsortium | Datei-Download, **keine Such-API** | Norm kostenpflichtig | **2** | Inhaltlich der relevanteste DACH-TGA-Datensatz, aber zugangstechnisch sperrig. Abgriff über Dateireferenz. |
| **ETIM** | ETIM e.V. | ✅ REST (Client-ID/Secret) | ODC-By, kostenfrei | **2** | Über bSDD ohnehin gespiegelt → wir andocken nicht doppelt. |
| **Open Masterdata (OMD)** | BVBS/ZVSHK + ITEK | REST, **B2B-Vertrag nötig** | Kommerziell | **4** | Echtzeit-Großhandelsdaten (DATANORM-Nachfolger). Für Open-Source-Projekt ohne Großhandelsvertrag nicht zugänglich. |
| **DATANORM** | Großhandel | ❌ Datei-Format (ASCII), kein Server | — | **4** | Veraltet, nur Stammdaten + Preise. Wird durch OMD abgelöst. **Nicht im Energie-Sidecar-Scope** — gehört in ERP/Einkauf. |
| **Blauer Engel** | UBA + RAL gGmbH | ❌ nur Frontend, XML auf Anfrage | Public | **3** | Reines Label, keine technischen Kennwerte. Optionales Boolean-Flag im Sidecar. |
| **RAL Gütezeichen** | RAL e.V. | ❌ keine API | — | **4** | Föderiert, heterogen, kein maschinenlesbares Schema. |
| **ausschreiben.de** | Heinze (kommerziell) | ❌ nur Softwarepartner-API | Bilateralvertrag | **4** | Praktisch unzugänglich für ein offenes Projekt. |
| **DIBT / abZ-Suche** | Deutsches Institut für Bautechnik | ❌ keine offizielle API | Public PDF | **4** | Politisch zitierbar, technisch nicht andockbar. |
| **EU CPR / DoP** | EU-Kommission | ❌ keine zentrale DB (vor DPP) | — | **5** | Erst mit Digital Product Passport (CPR-Revision 2024) perspektivisch nutzbar. 2026 nicht produktiv. |
| **EU Level(s)** | EU-Kommission (DG ENV) | ❌ Methodik, keine DB | — | **5** | Indikator-Framework, kein Produktregister. |

---

## 3. Schema-Andockung (Vorschlag für v3.2)

### 3.1 Material-Ebene

```jsonc
{
  "materials": [
    {
      "id": "MAT-001",
      "name": "EPS 032 WLG",
      "lambda": 0.032,
      "references": {
        "oekobaudat_uuid": "8e1...",
        "oekobaudat_version": "00.03.000",
        "bsdd_guid": "https://identifier.buildingsmart.org/uri/...",
        "manufacturer": "Hersteller XYZ",     // freier Text, optional
        "product_code": "EPS-032-180"          // freier Text, optional
      }
    }
  ]
}
```

### 3.2 System-Ebene (Anlagentechnik)

```jsonc
{
  "systems": [
    {
      "id": "WP-01",
      "type": "HEAT_PUMP",
      "references": {
        "eprel_id": "1234567",                 // EU-Produkt-ID (Pflicht für Label-pflichtige TGA)
        "vdi3805_blatt": "5",                  // optional, falls VDI-Datei vorhanden
        "vdi3805_file_ref": "viessmann_xyz.vdi3805"
      }
    }
  ]
}
```

### 3.3 Versionierung der Referenzen

**Pflicht:** Alle externen IDs werden mit Datum/Version gespeichert.

- ÖKOBAUDAT-Datensätze sind versioniert → ohne Version ist die Referenz ambig.
- EPREL-Modelle werden archiviert → ohne `retrieved_at` keine Reproduzierbarkeit.

---

## 4. Offene Flanke (ehrlich)

> **Für die Bauhülle (Fenster, Dämmstoffe, Mauerwerk, Türen) gibt es 2026 keine
> offene, vollständige Produktdatenbank in Deutschland.**

- EPREL deckt sie nicht (Fenster fallen unter CPR, nicht Energy-Labelling).
- ÖKOBAUDAT hat nur generische Datensätze, kein konkretes Hersteller-Produkt.
- DIBT/BZP hat keine API.
- ausschreiben.de ist verschlossen.
- VDI 3805 ist TGA, nicht Hülle.

**Wer einen U-Wert für ein konkretes Fenstermodell braucht, scrapt heute PDF-Datenblätter
oder bindet jeden Hersteller einzeln an.**

Das ist die offene Flanke und gleichzeitig der politische Hebel, mit dem wir
gegenüber Verbänden, Herstellern und buildingSMART argumentieren.

---

## 5. Eigene Pflege-Aufgaben (Projekt-Backlog)

Bis es offene Quellen gibt, pflegen wir community-getragen:

- [ ] **Bauhüllen-Produktregister** — leichtgewichtige, community-gepflegte Liste mit U-Wert / g-Wert / λ + Hersteller-DOI/DoP-URL.
- [ ] **Mapping-Tabelle** ÖKOBAUDAT-UUID ↔ DIN-18599-Bauteilkategorie ↔ bSDD-GUID — gibt es nirgendwo zentral.
- [ ] **VDI-3805 → Sidecar-Konverter** — Hersteller-Onboarding-Pfad ohne manuellen Aufwand.
- [ ] **Versionierungs-Konvention** — alle externen IDs mit `retrieved_at` + `source_version`.

---

## 6. Pitch-Aussage (1 Satz)

> „Hersteller- und Produktanbindung läuft bei uns über drei offene Standards mit
> echten APIs — ÖKOBAUDAT für LCA, EPREL für TGA-Produkte, buildingSMART bSDD
> für Klassifikation. Die Lücke bei der Bauhülle benennen wir offen und schließen
> sie community-getragen, bis CPR/DPP eine zentrale EU-Datenbank liefern."

---

## Quellen

- [ÖKOBAUDAT Downloads / API](https://www.oekobaudat.de/service/downloads.html)
- [EPREL Public API Key Request](https://eprel.ec.europa.eu/screen/requestpublicapikey)
- [buildingSMART bSDD Service](https://www.buildingsmart.org/users/services/buildingsmart-data-dictionary/)
- [bSDD Search Portal](https://search.bsdd.buildingsmart.org/)
- [bSDD Technical Documentation](https://technical.buildingsmart.org/services/bsdd/using-the-bsdd-api/)
- [VDI 3805 Herstellerdaten](https://www.vdi3805.eu/vdi-3805/herstellerdaten)
- [ETIM International API](https://www.etim-international.com/)
- [Open Masterdata ITEK](https://www.itek.de/plattformen/fuer-grosshaendler/webservice-open-masterdata/)
- [DIBT Zulassungs-Suche](https://www.dibt.de/de/service/zulassungsdownload/suche)
- [EU Construction Products Regulation](https://single-market-economy.ec.europa.eu/sectors/construction/construction-products-regulation-cpr_en)
- [DIN SPEC 91400](https://www.din.de/resource/blob/698744/d8401125e89ebd9f472b9a84b42390bc/flyer-din-spec-91400-data.pdf)
