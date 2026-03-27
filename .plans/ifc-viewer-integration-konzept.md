# IFC-Viewer Integration Konzept

**Status:** Konzeptphase  
**Ziel:** Integrierte Visualisierung von IFC-Geometrie + DIN 18599 Energiedaten mit Editierfunktion

---

## 1. Vision

**"Ein Viewer, der Geometrie und Physik vereint"**

- **Links:** 3D-IFC-Viewer (Gebäudemodell)
- **Rechts:** DIN 18599 Daten-Panel (Energiedaten)
- **Interaktion:** Click auf Bauteil → Zeigt U-Wert, Schichtaufbau, Wärmebrücken
- **Editieren:** Inline-Editing von U-Werten, Materialien, Systemen

---

## 2. Architektur-Optionen

### Option A: Embedded IFC-Viewer (xeokit)

```
┌─────────────────────────────────────────────────────┐
│  DIN 18599 Viewer (HTML/JS)                         │
├──────────────────────┬──────────────────────────────┤
│  IFC 3D Viewer       │  Data Panel                  │
│  (xeokit)            │  - Bauteilliste              │
│                      │  - U-Werte                   │
│  [3D Model]          │  - Schichtaufbauten          │
│                      │  - Systeme                   │
│  Click → Highlight   │  - Inline Editing            │
└──────────────────────┴──────────────────────────────┘
```

**Vorteile:**
- ✅ Alles in einem Tool
- ✅ Direkte Verknüpfung IFC GUID ↔ DIN 18599 Element
- ✅ Click-to-inspect Workflow

**Nachteile:**
- ❌ IFC→XKT Konvertierung nötig (serverseitig)
- ❌ Komplexere Implementierung
- ❌ Bundle Size steigt (~2-3 MB)

**Tech Stack:**
- xeokit-sdk (IFC-Viewer)
- XKTLoaderPlugin (für konvertierte IFC-Dateien)
- Custom Data Panel (Vue/React oder Vanilla JS)

---

### Option B: Split-Screen mit externem IFC-Viewer

```
┌─────────────────────────────────────────────────────┐
│  DIN 18599 Viewer (HTML/JS)                         │
├──────────────────────┬──────────────────────────────┤
│  IFC Viewer (iframe) │  Data Panel                  │
│  - BIMcollab Zoom    │  - Bauteilliste              │
│  - Autodesk Viewer   │  - U-Werte (editierbar)      │
│  - Solibri Anywhere  │  - Schichtaufbauten          │
│                      │  - Systeme                   │
│  PostMessage API     │  - Export JSON               │
└──────────────────────┴──────────────────────────────┘
```

**Vorteile:**
- ✅ Keine IFC-Konvertierung nötig
- ✅ Nutzt existierende Viewer (BIMcollab, Autodesk)
- ✅ Leichtgewichtig

**Nachteile:**
- ❌ Abhängigkeit von externen Diensten
- ❌ PostMessage-Integration komplex
- ❌ Keine direkte GUID-Verknüpfung

---

### Option C: Hybrid (Empfohlen für MVP)

```
┌─────────────────────────────────────────────────────┐
│  DIN 18599 Viewer (HTML/JS)                         │
├─────────────────────────────────────────────────────┤
│  📂 IFC-Datei: musterhaus.ifc                       │
│  [Open in BIMcollab] [Open in Solibri]             │
├─────────────────────────────────────────────────────┤
│  Data Panel (editierbar)                            │
│  - Bauteilliste mit IFC GUIDs                       │
│  - U-Werte (inline edit)                            │
│  - Schichtaufbauten (modal edit)                    │
│  - Systeme (form edit)                              │
│  [💾 Save Changes] [📥 Export JSON]                 │
└─────────────────────────────────────────────────────┘
```

**Vorteile:**
- ✅ Schnell umsetzbar (kein IFC-Viewer nötig)
- ✅ Fokus auf Daten-Editing
- ✅ Links zu externen Viewern für 3D-Ansicht
- ✅ Leichtgewichtig

**Nachteile:**
- ❌ Keine integrierte 3D-Ansicht
- ❌ Nutzer muss zwischen Tools wechseln

---

## 3. Editier-Funktionen (Priorität)

### Phase 1: Read-Only Viewer (✅ DONE)
- [x] Projektinfo anzeigen
- [x] Energiebilanz
- [x] Bauteilliste mit U-Werten
- [x] Wärmebrücken-Analyse
- [x] Systeme, Zonen, Sektoren

### Phase 2: Inline Editing (MVP)
- [ ] **U-Wert Override:** Click auf Bauteil → Input-Feld → Save
- [ ] **Material-Auswahl:** Dropdown für Materialien aus Katalog
- [ ] **Schichtaufbau-Editor:** Modal mit Layer-Liste (drag-to-reorder)
- [ ] **System-Parameter:** Form für Wärmeerzeuger (COP, Baujahr, etc.)
- [ ] **Export:** Geänderte Daten als JSON speichern

### Phase 3: Advanced Editing
- [ ] **Katalog-Integration:** Bundesanzeiger-Werte per Dropdown zuweisen
- [ ] **Validation:** Live-Validierung gegen Schema
- [ ] **Undo/Redo:** History-Stack für Änderungen
- [ ] **Diff-View:** Zeigt Änderungen zu Original

---

## 4. Datenfluss

```
┌─────────────────┐
│  IFC-Datei      │  (Geometrie, GUIDs)
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  DIN 18599 JSON │  (Energiedaten, verknüpft via IFC GUID)
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Viewer         │  (Anzeige + Editing)
│  - Read JSON    │
│  - Display Data │
│  - Edit Values  │
│  - Validate     │
│  - Export JSON  │
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  Updated JSON   │  (Gespeichert, versioniert)
└─────────────────┘
```

**Wichtig:** IFC-Datei bleibt **Read-Only** (Geometrie wird nicht geändert).  
Nur DIN 18599 JSON wird editiert.

---

## 5. UI-Konzept für Editing

### Bauteilliste mit Inline-Edit

```
┌────────────────────────────────────────────────────────────┐
│ 🧱 Bauteile (Opake Hülle)                    [+ Neu]       │
├────────────────────────────────────────────────────────────┤
│ IFC GUID     │ Typ  │ U-Wert  │ ΔU_WB │ Schichtaufbau │ ⚙️ │
├────────────────────────────────────────────────────────────┤
│ 1Eu7Wz4H...  │ AW   │ [0.10]  │ 0.02  │ LS-WALL-KfW40 │ ✏️ │
│ 2Fv8Xz5I...  │ DA   │ [0.098] │ 0.01  │ LS-ROOF-KfW40 │ ✏️ │
│ 3Gw9Yz6J...  │ BP   │ [0.157] │ 0.01  │ LS-FLOOR-...  │ ✏️ │
└────────────────────────────────────────────────────────────┘
```

**Click auf U-Wert:** → Input-Feld erscheint → Enter speichert  
**Click auf ✏️:** → Modal mit Schichtaufbau-Editor

### Schichtaufbau-Editor (Modal)

```
┌──────────────────────────────────────────────────────────┐
│ Schichtaufbau bearbeiten: LS-WALL-EXT-KfW40              │
├──────────────────────────────────────────────────────────┤
│ Position │ Material              │ Dicke (mm) │ ⬆️⬇️ 🗑️ │
├──────────────────────────────────────────────────────────┤
│    1     │ Außenputz mineralisch │    8       │  ⬆️⬇️ 🗑️ │
│    2     │ EPS-Dämmung WLG 032   │   300      │  ⬆️⬇️ 🗑️ │
│    3     │ Stahlbeton C30/37     │   200      │  ⬆️⬇️ 🗑️ │
│    4     │ Gipskartonplatte      │   12.5     │  ⬆️⬇️ 🗑️ │
├──────────────────────────────────────────────────────────┤
│ [+ Schicht hinzufügen]                                   │
├──────────────────────────────────────────────────────────┤
│ Berechnete Werte:                                        │
│ R_total: 9.63 m²K/W                                      │
│ U-Wert:  0.104 W/(m²K)                                   │
│ sd_total: 14.2 m                                         │
├──────────────────────────────────────────────────────────┤
│                              [Abbrechen] [Speichern]     │
└──────────────────────────────────────────────────────────┘
```

---

## 6. Technische Umsetzung

### Frontend (Vanilla JS oder Vue.js)

```javascript
// Inline-Edit für U-Wert
function makeEditable(elementId, field) {
  const cell = document.getElementById(`${elementId}-${field}`);
  
  cell.addEventListener('click', () => {
    const currentValue = cell.textContent;
    const input = document.createElement('input');
    input.value = currentValue;
    input.type = 'number';
    input.step = '0.001';
    
    input.addEventListener('blur', () => {
      const newValue = parseFloat(input.value);
      updateElement(elementId, field, newValue);
      cell.textContent = newValue.toFixed(3);
    });
    
    cell.innerHTML = '';
    cell.appendChild(input);
    input.focus();
  });
}

// Speichern
function saveChanges() {
  const updatedData = getCurrentData();
  
  // Validierung
  if (!validateSchema(updatedData)) {
    alert('Validierungsfehler!');
    return;
  }
  
  // Download als JSON
  const blob = new Blob([JSON.stringify(updatedData, null, 2)], 
                        {type: 'application/json'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'updated-building.din18599.json';
  a.click();
}
```

### Validation (jsonschema.js)

```javascript
import Ajv from 'ajv';

const ajv = new Ajv();
const schema = await fetch('../gebaeude.din18599.schema.json').then(r => r.json());
const validate = ajv.compile(schema);

function validateSchema(data) {
  const valid = validate(data);
  if (!valid) {
    console.error('Validation errors:', validate.errors);
    return false;
  }
  return true;
}
```

---

## 7. Roadmap

### Sprint 1: Viewer-Basis (✅ DONE)
- [x] Beispiel-Dropdown
- [x] Bauteilliste mit U-Werten
- [x] Wärmebrücken-Analyse

### Sprint 2: Editing MVP (2-3 Tage)
- [ ] Inline-Edit für U-Werte
- [ ] Material-Dropdown (aus JSON)
- [ ] Save/Export-Funktion
- [ ] Client-side Validation

### Sprint 3: Advanced Editing (3-5 Tage)
- [ ] Schichtaufbau-Editor (Modal)
- [ ] Layer drag-to-reorder
- [ ] Live U-Wert-Berechnung
- [ ] Undo/Redo

### Sprint 4: IFC-Viewer Integration (5-7 Tage)
- [ ] xeokit einbinden
- [ ] IFC→XKT Konverter (CLI)
- [ ] GUID-Verknüpfung
- [ ] Click-to-inspect

---

## 8. Offene Fragen

1. **IFC-Konvertierung:** Wer/Was konvertiert IFC→XKT? (CLI-Tool, Backend-Service?)
2. **Speicherung:** Wo werden editierte JSONs gespeichert? (Local Download, Backend-API, Git?)
3. **Versionierung:** Wie tracken wir Änderungen? (Git, Audit-Log, Snapshots?)
4. **Multi-User:** Sollen mehrere Nutzer gleichzeitig editieren können? (später)
5. **Katalog-Integration:** Wie werden Bundesanzeiger-Werte zugewiesen? (Dropdown, Auto-Match?)

---

## 9. Entscheidung

**Empfehlung für MVP:**

→ **Option C (Hybrid)** mit **Sprint 2 (Editing MVP)**

**Begründung:**
- ✅ Schnell umsetzbar (2-3 Tage)
- ✅ Fokus auf Daten-Qualität (Editing wichtiger als 3D-Viewer)
- ✅ Leichtgewichtig (kein IFC-Viewer nötig)
- ✅ Links zu externen Viewern für 3D-Ansicht
- ✅ IFC-Viewer kann später nachgerüstet werden (Sprint 4)

**Nächster Schritt:**
- Inline-Edit für U-Werte implementieren
- Save/Export-Funktion
- Dann: Schichtaufbau-Editor (Modal)
