# Nächste Schritte - DIN 18599 IFC Sidecar

**Stand:** 29. März 2026  
**Status:** Katalog-System komplett, LOD-Scope definiert, Feldliste 85-90% vollständig

---

## ✅ **HEUTE ERREICHT (29. März 2026)**

### **1. DIN 18599 Registries auf 100%**
- ✅ 222 Begriffe (Glossar komplett)
- ✅ 562 Symbole (alle Formelzeichen)
- ✅ 735 Indizes (alle Indizes)
- ✅ 45 Nutzungsprofile (Wohn + Nichtwohn)
- ✅ Beiblatt 1 hinzugefügt (Bedarfs-/Verbrauchsabgleich)
- **= 1564 Einträge total**

### **2. Katalog-System komplett**
- ✅ 52 Materialien (λ, ρ, c, μ nach DIN 4108-4)
- ✅ 24 Schichtaufbauten (U-Werte 0.14-5.8 W/(m²K))
- ✅ 45 Nutzungsprofile (Enum-validiert)
- ✅ Katalog-Referenzen im Schema v2.1 Extensions
- ✅ Demo-Projekt mit Sanierungsszenarien
- ✅ CATALOG_GUIDE.md (409 Zeilen)

### **3. LOD-Scope & Dynamisches Datenmodell**
- ✅ LOD-Konzept analysiert (100, 200, 300, 400, 500)
- ✅ **Dynamisches Datenmodell** statt starre LODs
- ✅ **16 Kategorien** mit ~100 Feldern definiert
- ✅ 2x Perplexity-Review (kritische Prüfung)
- ✅ Feldliste 85-90% vollständig

### **4. Strategische Entscheidungen**
- ✅ Schema v2.1: Maximal norm-konform
- ✅ Envelope: Hybrid (opak/transparent + bauteilspezifisch)
- ✅ Systems: Detailliert (Erzeugung/Verteilung/Übergabe/Regelung)
- ✅ Breaking Changes: Maximal (komplette Neustrukturierung)

---

## 🎯 **PRIORITÄTEN FÜR SCHEMA v2.1**

### **Phase 1: Feldliste finalisieren (1-2 Tage)**

#### **Kategorie 17: Gebäudeautomation (BACS)** ⚠️ **KRITISCH!**
**Warum:** DIN 18599-11, Effizienzfaktoren, Primärenergie-Reduktion

**Felder:**
- `automation.bacs_class` - Automatisierungsklasse (A-D nach DIN EN 15232)
- `automation.efficiency_factor` - Effizienzfaktor [-]
- `automation.control_quality` - Regelungsqualität
- `automation.sensors` - Sensoren (Temperatur, CO₂, Präsenz)
- `automation.actuators` - Aktoren (Ventile, Klappen, Dimmer)
- `automation.building_management_system` - Gebäudeleittechnik vorhanden?
- `automation.room_automation` - Raumautomation-Stufe

**LOD-Zuordnung:**
- LOD 100: ❌
- LOD 200: Optional
- LOD 300: ✅ Required

---

#### **Kategorie 18: Primärenergiefaktoren** ⚠️ **KRITISCH!**
**Warum:** Primärenergiebilanz, Energieausweis, GEG-Grenzwerte

**Felder:**
- `primary_energy.factors.electricity` - fp Strom [-]
- `primary_energy.factors.natural_gas` - fp Erdgas [-]
- `primary_energy.factors.oil` - fp Heizöl [-]
- `primary_energy.factors.district_heating` - fp Fernwärme [-]
- `primary_energy.factors.wood_pellets` - fp Holzpellets [-]
- `primary_energy.factors.renewable_share` - EE-Anteil [-]
- `primary_energy.source` - Quelle (GEG, BEG, custom)
- `primary_energy.reference_year` - Referenzjahr

**LOD-Zuordnung:**
- LOD 100: ✅ Required (aus Energieausweis)
- LOD 200: ✅ Required
- LOD 300: ✅ Required

---

#### **Kategorie 19: Sanierungsmaßnahmen** (Optional, für iSFP/KfW)
**Warum:** Sanierungsfahrplan, Förderanträge, Wirtschaftlichkeit

**Felder:**
- `measures[].id` - Maßnahmen-ID
- `measures[].category` - Kategorie (envelope, heating, ventilation, etc.)
- `measures[].description` - Beschreibung
- `measures[].priority` - Priorität (1-3)
- `measures[].investment_cost_eur` - Investitionskosten [€]
- `measures[].energy_savings_kwh_a` - Energieeinsparung [kWh/a]
- `measures[].co2_savings_kg_a` - CO₂-Einsparung [kg/a]
- `measures[].payback_period_years` - Amortisationszeit [Jahre]
- `measures[].funding_eligible` - Förderfähig (BEG)?
- `measures[].funding_amount_eur` - Förderbetrag [€]
- `measures[].implementation_year` - Umsetzungsjahr

**LOD-Zuordnung:**
- LOD 100: ❌
- LOD 200: Optional
- LOD 300: Optional (nur für iSFP)

---

### **Phase 2: Schema v2.1 strukturieren (3-5 Tage)**

**Aufgaben:**
1. ✅ Katalog-Referenzen (bereits in v2.1-catalog-extensions.json)
2. **Envelope-Struktur** neu aufbauen
   - `opaque_elements` (walls, roofs, floors)
   - `transparent_elements` (windows, doors)
   - `thermal_bridges` (method, delta_u_wb, linear_bridges)
3. **Systems-Struktur** detaillieren
   - `heating` (generation, distribution, emission, control)
   - `ventilation` (type, heat_recovery, air_flow)
   - `cooling` (type, power, eer)
   - `lighting` (power, control, daylight)
   - `dhw` (generation, distribution, circulation)
4. **Zonen erweitern**
   - Nutzungsprofile mit Betriebszeiten
   - Solltemperaturen, Luftwechsel
5. **Neue Kategorien integrieren**
   - Lüftung & Luftdichtheit
   - Interne Lasten
   - Gebäudeautomation
   - Primärenergiefaktoren

---

### **Phase 3: Migration-Script v2.0 → v2.1 (2-3 Tage)**

**Aufgaben:**
1. Mapping-Tabellen erstellen
   - `usage_profile` "17" → `usage_profile_ref` "PROFILE_NWG_17"
   - `elements[]` → `envelope.opaque_elements.*[]` + `envelope.transparent_elements.*[]`
2. IFC GUID generieren (wenn fehlend)
3. Automatische Kategorisierung (wall → walls_external/internal)
4. Validierung nach v2.1 Schema

---

### **Phase 4: Demo-Projekt aktualisieren (1 Tag)**

**Aufgaben:**
1. Einfamilienhaus auf v2.1 migrieren
2. Alle neuen Kategorien demonstrieren
3. LOD 100 → 200 → 300 Progression zeigen

---

### **Phase 5: Dokumentation (2-3 Tage)**

**Aufgaben:**
1. **SCHEMA_V2.1_GUIDE.md**
   - Vollständige Feldliste
   - LOD-Zuordnung
   - Beispiele pro Kategorie
2. **MIGRATION_GUIDE.md**
   - v2.0 → v2.1 Breaking Changes
   - Migration-Script Anleitung
   - Häufige Probleme
3. **LOD_GUIDE.md**
   - Dynamisches Datenmodell
   - Progressive Datenerfassung
   - Validierung pro LOD
4. **CATALOG_GUIDE.md** erweitern
   - Gebäudeautomation-Katalog
   - Primärenergiefaktoren-Katalog

---

## 📅 **ZEITPLAN (April 2026)**

| Woche | Phase | Aufgaben | Status |
|-------|-------|----------|--------|
| **KW 14 (1.-7. April)** | Phase 1+2 | Feldliste finalisieren + Schema v2.1 strukturieren | Pending |
| **KW 15 (8.-14. April)** | Phase 3+4 | Migration-Script + Demo-Projekt | Pending |
| **KW 16 (15.-21. April)** | Phase 5 | Dokumentation | Pending |
| **KW 17 (22.-28. April)** | Testing | Validierung, Bugfixes | Pending |
| **KW 18 (29. April - 5. Mai)** | Release | Schema v2.1 Release | Pending |

**Deadline:** **5. Mai 2026** - Schema v2.1 Production Ready

---

## 🚀 **LANGFRISTIGE ROADMAP (Mai - Juni 2026)**

### **Mai 2026: Viewer-MVP**
- 3D-Viewer mit Three.js
- Energiedaten-Overlay
- IFC-Import
- Schema v2.1 Integration

### **Juni 2026: Community & Präsentation**
- GitHub Release
- Dokumentation finalisieren
- Berlin-Präsentation vorbereiten
- Erste externe Contributors

---

## 📊 **ERFOLGSMETRIKEN**

### **Schema v2.1 Vollständigkeit:**
- ✅ Katalog-System: 100%
- ✅ Feldliste: 85-90% (nach Perplexity-Review)
- ⏳ Gebäudeautomation: 0% (fehlt noch)
- ⏳ Primärenergiefaktoren: 0% (fehlt noch)
- ⏳ Sanierungsmaßnahmen: 0% (optional)

**Ziel:** **95-100% Vollständigkeit** bis 5. Mai 2026

### **Norm-Konformität:**
- ✅ DIN 18599 Registries: 100%
- ✅ Katalog-Referenzen: Implementiert
- ⏳ DIN 18599-11 (Automation): Pending
- ⏳ GEG 2024 Anforderungen: Pending

**Ziel:** **Vollständige DIN 18599 Konformität**

---

## 🎯 **NÄCHSTE KONKRETE SCHRITTE**

### **Morgen (30. März):**
1. Kategorie 17 (Gebäudeautomation) hinzufügen
2. Kategorie 18 (Primärenergiefaktoren) hinzufügen
3. Perplexity-Review #3 (finale Prüfung)

### **Diese Woche:**
1. Schema v2.1 Struktur komplett aufbauen
2. Alle 18 Kategorien integrieren
3. Demo-Projekt auf v2.1 migrieren

### **Nächste Woche:**
1. Migration-Script schreiben
2. Dokumentation starten
3. Testing & Validierung

---

## 📚 **REFERENZEN**

### **Brainstorms:**
- [20260329_sidecar_struktur_din18599.md](./brainstorms/20260329_sidecar_struktur_din18599.md)
- [20260329_lod_scope_definition.md](./brainstorms/20260329_lod_scope_definition.md)
- [20260329_dynamisches_datenmodell.md](./brainstorms/20260329_dynamisches_datenmodell.md)

### **Kataloge:**
- [materials.json](../catalog/materials.json) - 52 Materialien
- [constructions.json](../catalog/constructions.json) - 24 Konstruktionen
- [din18599_usage_profiles.json](../catalog/din18599_usage_profiles.json) - 45 Profile

### **Schema:**
- [v2.1-catalog-extensions.json](../schema/v2.1-catalog-extensions.json)
- [usage_profile_enum.json](../schema/usage_profile_enum.json)

### **Demo:**
- [demo-einfamilienhaus-katalog.din18599.json](../examples/demo-einfamilienhaus-katalog.din18599.json)

---

**Erstellt:** 29. März 2026  
**Nächstes Update:** 30. März 2026  
**Verantwortlich:** DWE Beratung GmbH + Cascade AI
