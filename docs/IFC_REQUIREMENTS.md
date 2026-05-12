# IFC-Anforderungen und buildingSMART-Andockpunkte

**Stand:** 06.05.2026
**Status:** Strategiepapier — IDS-Template und bSDD-Domäne in Vorbereitung

> **Leitsatz:** Wir definieren maschinenlesbar (IDS), was ein IFC-Export liefern
> muss, damit unser Sidecar verlässlich andockt. Wo IFC strukturelle Lücken hat
> — Wärmebrücken, Verschattung, GUID-Stabilität, 2nd-Level-Boundaries — gehen
> wir mit drei konkreten Forderungen auf buildingSMART zu.

---

## 1. IFC-Mindestanforderungs-Spec

Diese 10 Punkte muss ein IFC-Export erfüllen, damit das Sidecar **ohne manuelle
Nacharbeit** andocken kann. Die Spec wird als IDS-Datei (Information Delivery
Specification, ISO/buildingSMART-Standard seit 01.06.2024) ausgeliefert und ist
mit `ifctester` automatisch prüfbar.

| # | Anforderung | Begründung |
|---|-------------|------------|
| 1 | **IFC-Version**: IFC4 ADD2 minimum, IFC4.3 ADD2 empfohlen, IFC2x3 nur lesend | IFC4.3 brachte für Hochbau-Energie keine substanziellen Pset-Erweiterungen — ADD2 reicht. |
| 2 | **MVD**: Design Transfer View 1.0 oder volle Schema-Konformität, **nicht** Reference View | RV liefert nur Tessellation, keine SweptSolid → Schichtinterpretation unmöglich. |
| 3 | **GUID-Persistenz**: Authoring-Tool muss `IfcGUID` als Element-Parameter persistent speichern (Revit-Setting an, Archicad default) | Sonst rotieren GUIDs bei Re-Export → Sidecar-Verknüpfung bricht. |
| 4 | **Räumliche Hierarchie** vollständig: `IfcSite → IfcBuilding → IfcBuildingStorey → IfcSpace`, jede `IfcSpace` mit `LongName` und `Name` | Zonierung im Sidecar referenziert `IfcSpace.GlobalId` — ohne Hierarchie keine Aggregation. |
| 5 | **Space Boundaries**: `IfcRelSpaceBoundary` 2nd Level bevorzugt, 1st Level akzeptiert mit Validator-Warnung. Innen/Außen-Differenzierung Pflicht | DIN 18599 braucht 2nd Level für die Hüllflächen-Bilanz pro Zone. 1st Level ist nur für Schnellschätzung tragfähig. |
| 6 | **Materialien**: `IfcMaterialLayerSetUsage` → `IfcMaterialLayerSet`, mindestens `LayerThickness` + `Material.Name` pro Schicht | Layer-Resolution-Strategie verlangt vollständige Schichten (siehe [LAYER_RESOLUTION_STRATEGY.md](LAYER_RESOLUTION_STRATEGY.md)). |
| 7 | **Common Psets**: `Pset_WallCommon`, `Pset_WindowCommon`, `Pset_DoorCommon`, `Pset_SlabCommon`, `Pset_RoofCommon` mit `IsExternal` (Pflicht). `ThermalTransmittance` optional — Sidecar kann überschreiben | `IsExternal` ist die einzige Information, die Sidecar nicht zuverlässig aus Geometrie ableiten kann. |
| 8 | **Geometrie**: SweptSolid oder Brep, keine reinen Tessellated-only-Walls | Sonst kein Volumen, keine Schichten, keine Orientierungs-Berechnung. |
| 9 | **Einheiten**: SI explizit deklariert (`IfcSIUnit`, Meter, Watt, Kelvin) | Bilanzen brechen ohne Einheiten-Auflösung. |
| 10 | **IDS-Validierung**: IFC muss gegen unsere mitgelieferte IDS-Datei validieren (`ifctester` exit 0) | Maschinell prüfbarer Vertrag, keine Auslegungsfragen. |

---

## 2. Real-World-Probleme, die buildingSMART HEUTE NICHT löst

Das sind die strukturellen Lücken, die das Sidecar-Format überhaupt erst
rechtfertigen:

| Lücke | Status in IFC | Wie das Sidecar es löst |
|-------|---------------|-------------------------|
| **Wärmebrücken (Ψ-Wert)** | nicht im IFC4-Schema, kein Pset, keine Geometriereferenz | `elements[].thermal_bridge_delta_u` mit Typen DEFAULT/REDUCED/DETAILED |
| **Fensterverschattung mit Zeitprofil** | `IfcShadingDevice` ohne Verknüpfungssemantik zum Fenster, kein g_total-Schema | Sidecar bindet Verschattung explizit an Fenster-GUID |
| **DIN 18599 Anlagentechnik (Teile 5–9)** | keine Pset-Familie für RLT/TWE/Heizung/Beleuchtung mit deutschen Bilanzkennwerten | Vollständige `systems[]`-Struktur mit Erzeuger / Verteilung / Übergabe |
| **Nutzungsprofile DIN V 18599-10** | `Pset_SpaceOccupancyRequirements` deckt deutsche Standardprofile nicht ab | Eigener Profil-Katalog mit Norm-Referenz |
| **GUID-Stabilität bei Re-Export** | reine Tool-Konvention, kein Standard, `IfcSpace`-GUIDs in Revit dokumentiert instabil (revit-ifc Issue #521) | Fallback-Resolver Name + Type + Hierarchiepfad + Geometrie-Hash |
| **2nd-Level Space Boundaries** | Standard existiert, Tool-Realität ist Trümmerfeld | Validator + optionaler Geometrie-Recompute |
| **U-Wert-Provenienz** | IFC kennt nur den Wert, nicht die Quelle | `source: "ifc_material_layer_set" \| "evebi_construction" \| "catalog_template" \| "manual_override"` |
| **Sanierungsvarianten / Ist-Soll** | IFC ist single-state | Sidecar trägt `base` + `scenarios[]` als Delta-Modell |

**Pitch-Argument:** Reines IFC bildet DIN 18599 nicht ab — und die Tool-Realität
befüllt die existierenden Psets nicht zuverlässig. Genau hier rechtfertigt sich
ein Sidecar gegenüber der Frage „Warum kein reines IFC?".

---

## 3. Drei Forderungen an buildingSMART

Vorgetragen werden sie an die **Fachgruppe Nachhaltigkeit** von buildingSMART
Deutschland (Neustart 20.10.2025 online, Treffen 10.11.2025 Fulda) sowie an die
**bSI Building Room** (international), die 2025/2026 ohnehin an einer
IfcSpace-Pset-Konsolidierung arbeitet — gutes Zeitfenster.

### Forderung 1 — IDS-Template „DIN 18599"

> Wir liefern eine offizielle, MIT-lizenzierte IDS-Spezifikation für
> DIN-18599-fähige IFC-Modelle und beantragen ihre Aufnahme in den
> IDS-Template-Katalog von buildingSMART, damit jeder Energieberater per
> Knopfdruck prüfen kann, ob ein IFC-Modell bilanzierfähig ist.

**Status bei uns:** Spec aus Abschnitt 1 wird als IDS-Datei in `schema/ids/`
abgelegt. Tools: BIMcollab Zoom, Solibri, ACCA usBIM, IfcOpenShell `ifctester`.

### Forderung 2 — bSDD-Domäne „DIN 18599 Property Dictionary"

> Wir registrieren ein deutschsprachiges bSDD-Property-Dictionary mit den
> DIN-18599-Kennwerten (Wärmebrückenzuschlag ΔU_WB, Nutzenergie-Bedarfskennwerte
> Teil 5–9, Anlagenaufwandszahlen) und fordern bSI auf, dieses als Referenz-
> Domäne für deutsche Energiebilanzen zu listen.

**Status bei uns:** Org-Registrierung als Publisher (DWE Beratung GmbH)
einleiten, Datenstruktur nach ISO 23386 / ISO 12006-3 vorbereiten. Realistisch
in 3–6 Monaten.

### Forderung 3 — Pset-Erweiterungen für IFC4.3 ADD3

> Wir beantragen formell die Aufnahme von `Pset_ThermalBridge` (linearer Ψ-Wert
> plus Geometrie-Referenz) und `Pset_ShadingDeviceWindow` (zeitabhängige
> Verschattungsfaktoren mit Fenster-Bezug) in IFC4.3 ADD3. Solange das nicht
> passiert, schließt unser Sidecar die Lücke.

**Status bei uns:** Sidecar-Felder sind bereits da — wir liefern die Erfahrung,
die in den bSI-Antrag einfließt.

---

## 4. Roadmap-Schnittstelle

| Quartal | Lieferbar |
|---------|-----------|
| **Q2 2026** | IDS 1.0 Draft `schema/ids/din18599-base.ids` |
| **Q3 2026** | bSDD-Domäne registriert (Publisher-Account + erste Properties) |
| **Q3 2026** | IDS-Template-Antrag bei buildingSMART eingereicht |
| **Q4 2026** | Pset-Antrag (`Pset_ThermalBridge`, `Pset_ShadingDeviceWindow`) bei bSI |

Diese Punkte sind in [ROADMAP.md](../ROADMAP.md) zu spiegeln.

---

## 5. Pitch-Aussagen (3 Sätze)

> „Wir definieren maschinenlesbar, was ein IFC-Export liefern muss — als IDS-
> Datei, prüfbar mit Standard-Tools."
>
> „Wir gehen mit drei konkreten Forderungen auf buildingSMART zu: ein IDS-
> Template DIN 18599, eine bSDD-Domäne mit den deutschen Bilanzkennwerten, und
> Pset-Erweiterungen für Wärmebrücken und Fensterverschattung."
>
> „Bis der Standard das löst, schließt unser Sidecar die Lücke — und liefert
> gleichzeitig die Praxiserfahrung, die in den Antrag einfließt."

---

## Quellen

- [IFC MVD Database](https://technical.buildingsmart.org/standards/ifc/mvd/mvd-database/)
- [IFC4.3.2 Documentation](https://ifc43-docs.standards.buildingsmart.org/)
- [Reference View RV1.2](https://standards.buildingsmart.org/MVD/RELEASE/IFC4/ADD2_TC1/RV1_2/HTML/schema/views/reference-view/index.htm)
- [Design Transfer View Documentation](https://github.com/buildingSMART/IFC/blob/master/ModelViews/Design%20Transfer%20View/Documentation.md)
- [Revit IFC Issue #521 — Room GUID instability](https://github.com/Autodesk/revit-ifc/issues/521)
- [IDS 1.0 Standard](https://www.buildingsmart.org/standards/bsi-standards/information-delivery-specification-ids/)
- [IDS GitHub Repository](https://github.com/buildingSMART/IDS)
- [bSDD Service](https://www.buildingsmart.org/users/services/buildingsmart-data-dictionary/)
- [bSDD Data Structure](https://technical.buildingsmart.org/services/bsdd/data-structure/)
- [Pset_WallCommon Revit Export Issue (Autodesk)](https://www.autodesk.com/support/technical/article/caas/sfdcarticles/sfdcarticles/Not-all-Pset-WallCommon-parameters-exported-automatically-to-IFC-from-Revit.html)
- [Pset_SpaceThermalRequirements](https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2/HTML/schema/ifcproductextension/pset/pset_spacethermalrequirements.htm)
- [IfcRelSpaceBoundary Validation Research](https://www.sciencedirect.com/science/article/abs/pii/S0926580521001758)
- [bSI MVD Policy IFC4.x](https://www.buildingsmart.org/wp-content/uploads/2021/05/20210425_MVD-policy_IFC4.x.pdf)
- [Fachgruppe Nachhaltigkeit Neustart](https://web.buildingsmart.de/termin/neustart-der-fachgruppe-nachhaltigkeit)
- [buildingSMART Deutschland Gremien](https://www.buildingsmart.de/buildingsmart/gremien-regularien)
