# Strategische Entscheidung: Viewer/Editor Basis

**Stand:** 31. März 2026  
**Perplexity-Reviews:** 2x  
**Fokus:** Langfristiger Erfolg, nicht kurzfristiger Aufwand

---

## 🎯 Unser langfristiges Ziel

> Eigenes Open-Source Energieberatungsprogramm:  
> Gebäude modellieren → Energetisch bewerten → Szenarien vergleichen → Berichte erstellen

**Das ist unser Software-neutrales Fundament:** DIN 18599 JSON Sidecar = Input für beliebige Berechnungs-Software.

---

## 📊 Ehrliche Bewertungsmatrix

### Bewertungskriterien (gewichtet nach Wichtigkeit):

| Kriterium | Gewicht | Warum? |
|-----------|---------|--------|
| **DIN 18599 / GEG Eignung** | 30% | Kernziel: Deutsche Energieberatung |
| **Langfristige Maintenance** | 20% | Community, Updates, Zukunftssicherheit |
| **IFC-Integration** | 20% | Zukunft: Gebäudedaten kommen aus BIM |
| **Erweiterbarkeit für SaaS** | 15% | Langfristiges Geschäftsmodell |
| **3D-Visualisierung** | 15% | Demo-Faktor, UX, Differenzierung |

---

## 🔎 Detailbewertung der 4 Optionen

### **Option A: FloorspaceJS (NREL)**

**Was es ist:** 2D-Floorplan-Editor, Vanilla JS, speziell für Building Energy Modeling, von US-Behörde NREL entwickelt, integriert mit OpenStudio/EnergyPlus

| Kriterium | Note | Begründung |
|-----------|------|------------|
| DIN 18599 / GEG | ⭐⭐⭐⭐ | Speziell für BEM entwickelt, EnergyPlus-Kern |
| Langfristige Maintenance | ⭐⭐⭐⭐⭐ | NREL = US-Regierung = sicher finanziert |
| IFC-Integration | ⭐⭐⭐ | Nur via EnergyPlus-Adapter, nicht nativ |
| SaaS-Eignung | ⭐⭐⭐⭐ | NREL-Basis, skalierbar |
| 3D-Visualisierung | ⭐⭐ | **Nur 2D!** Kein echter 3D-Viewer |

**Gewichtetes Ergebnis: 3.7/5**

**⚠️ KRITISCHER PUNKT:** FloorspaceJS ist **2D-focused** und **Vanilla JS**. Es bindet uns an das **EnergyPlus-Ökosystem (US-Standard)**, nicht an DIN 18599 (DE-Standard). Unser JSON-Format ist software-neutral - FloorspaceJS widerspricht dieser Vision!

---

### **Option B: Pascal Editor**

**Was es ist:** React Three Fiber + WebGPU, allgemeiner 3D-Building-Editor, MIT Lizenz, aktive aber kleine Community

| Kriterium | Note | Begründung |
|-----------|------|------------|
| DIN 18599 / GEG | ⭐⭐ | Generisch, keine BEM-Features |
| Langfristige Maintenance | ⭐⭐ | Kleine Community, kein institutionelles Backing |
| IFC-Integration | ⭐⭐ | Nur Custom-Implementierung |
| SaaS-Eignung | ⭐⭐⭐ | Modern, aber wenig BEM-spezifisch |
| 3D-Visualisierung | ⭐⭐⭐⭐⭐ | WebGPU = State-of-the-Art |

**Gewichtetes Ergebnis: 2.6/5**

**⚠️ KRITISCHER PUNKT:** WebGPU ist experimentell. Safari/Firefox = eingeschränkt. Kein DIN 18599-Fokus. Kleine Community = Maintenance-Risiko.

---

### **Option C: xeokit SDK**

**Was es ist:** Professionelles BIM/IFC-Viewer SDK, native IFC-Unterstützung, WebGL, kommerziell + OSS

| Kriterium | Note | Begründung |
|-----------|------|------------|
| DIN 18599 / GEG | ⭐⭐⭐ | BIM-fokussiert, aber kein BEM-Kern |
| Langfristige Maintenance | ⭐⭐⭐⭐ | Professionell, kommerzieller Backing |
| IFC-Integration | ⭐⭐⭐⭐⭐ | **Stärkste IFC-Unterstützung** |
| SaaS-Eignung | ⭐⭐⭐ | OSS + Enterprise (Paywall-Risiko!) |
| 3D-Visualisierung | ⭐⭐⭐⭐ | Professionell, BIM-Qualität |

**Gewichtetes Ergebnis: 3.7/5**

**⚠️ KRITISCHER PUNKT:** xeokit ist **Viewer**, kein Editor. Für unser Ziel (editieren, Szenarien erstellen) ungeeignet als alleinige Basis. Lizenz-Risiko (OSS → kommerziell).

---

### **Option D: Eigener Viewer (React Three Fiber)**

**Was es ist:** Bestehenden Three.js Viewer (900 Zeilen, funktioniert!) auf React Three Fiber migrieren + alle Features selbst bauen

| Kriterium | Note | Begründung |
|-----------|------|------------|
| DIN 18599 / GEG | ⭐⭐⭐⭐⭐ | **Wir definieren es!** 1:1 nach unserem Schema |
| Langfristige Maintenance | ⭐⭐⭐ | Hängt von uns ab, aber volle Kontrolle |
| IFC-Integration | ⭐⭐⭐ | web-ifc einbindbar, volle Kontrolle |
| SaaS-Eignung | ⭐⭐⭐⭐⭐ | **Maximale Flexibilität** |
| 3D-Visualisierung | ⭐⭐⭐⭐ | R3F = modern, stabil, große Community |

**Gewichtetes Ergebnis: 4.2/5**

---

## 🏆 Ergebnis

| Option | Gewichtetes Ergebnis | Empfehlung |
|--------|---------------------|------------|
| **D: Eigener Viewer (R3F)** | **4.2/5** | ✅ **BESTE LANGFRISTIGE WAHL** |
| **A: FloorspaceJS** | 3.7/5 | ⚠️ Als Inspiration/Referenz |
| **C: xeokit** | 3.7/5 | ⚠️ Für IFC-Viewing-Modul später |
| **B: Pascal** | 2.6/5 | ❌ Nicht empfohlen |

---

## 💡 STRATEGISCHE EMPFEHLUNG

### **Option D: Eigener R3F-Viewer ist die richtige Langfrist-Entscheidung**

**Warum langfristig erfolgreicher:**

### 1. Wir sind das Format
Unser DIN 18599 JSON Sidecar = unsere Vision. FloorspaceJS bindet uns an EnergyPlus (US). Wir wollen **software-neutral** sein. Nur mit eigenem Viewer können wir das 1:1 umsetzen.

### 2. React Three Fiber = Riesige Community
- **R3F hat 27k+ GitHub Stars**
- Aktiv maintained (pmndrs-Community)
- Riesiges Ökosystem (Drei, Leva, Rapier, etc.)
- Langfristig sicherer als FloorspaceJS Vanilla JS

### 3. Wir haben bereits 900 Zeilen Three.js Code
Kein Neustart. Migration Three.js → R3F ist einfach:
```javascript
// Three.js (aktuell)
const geometry = new THREE.BoxGeometry(1, 1, 1)
const mesh = new THREE.Mesh(geometry, material)
scene.add(mesh)

// React Three Fiber (Ziel)
<mesh>
  <boxGeometry args={[1, 1, 1]} />
  <meshStandardMaterial />
</mesh>
```

### 4. Volle Kontrolle = SaaS-fähig
Für ein zukünftiges Energieberatungs-SaaS brauchen wir volle Kontrolle über:
- Datenmodell (unser Schema v2.1)
- UI/UX (DWEapp-Design-System)
- Business-Logik (Szenarien, Berichte)
- Lizenz (kein Paywall-Risiko wie bei xeokit)

### 5. IFC später nachrüsten
`web-ifc` = npm-Paket, easy drop-in. Kein Problem, das later hinzuzufügen.

---

## 🔄 HYBRID-STRATEGIE

**Eigener R3F Viewer PLUS selektive Integration:**

```
┌─────────────────────────────────────────────┐
│         Unser Viewer (React Three Fiber)    │
│                                             │
│  ┌─────────────┐   ┌─────────────────────┐  │
│  │ FloorspaceJS│   │  web-ifc            │  │
│  │ als Inspiration│  │  (IFC-Parser)     │  │
│  │ für BEM-UX  │   │  drop-in           │  │
│  └─────────────┘   └─────────────────────┘  │
│                                             │
│  Unser DIN 18599 JSON Schema v2.1           │
│  (Software-neutral, unser Format)           │
└─────────────────────────────────────────────┘
```

**Konkret:**
- **Von FloorspaceJS lernen:** UX-Patterns für Zonen/Floorplan-Eingabe
- **xeokit als Inspiration:** IFC-Viewing-UI
- **web-ifc einbinden:** IFC-Parsing (npm-Paket)
- **Alles andere:** Selbst bauen (volle Kontrolle)

---

## 📅 Konsequenz für den Implementierungs-Plan

### **Phase 0 (1. April, 1 Tag): Migration Three.js → R3F**

```bash
npm install three @react-three/fiber @react-three/drei
```

Bestehender Code (900 Zeilen Three.js) → R3F-Komponenten migrieren.

### **Phase 1 (Woche 1-2): Core Viewer**
- R3F-Grundgerüst mit bestehendem Code
- Tree-Navigation + Inspector
- DIN 18599 JSON laden

### **Phase 2 (Woche 3-4): Editor**
- Katalog-Integration (unsere 52 Materialien)
- Bauteil-Editor (Dropdown → Delta)
- Szenario-Switcher

### **Phase 3 (Woche 5-6): Demo + Polish**
- Berlin-Demo finalisieren
- Performance-Optimierung
- Testing

---

## ✅ Entscheidung

**→ Eigener React Three Fiber Viewer auf Basis des bestehenden Three.js Codes.**

**Perplexity-Konsistenz:** Perplexity empfahl R3F explizit für Editor-Features (50% weniger Code, deklaratives 3D, besseres State-Management).

**Keine Forks von Drittanbieter-Tools.** Wir lernen von ihnen, aber bauen selbst.

---

**Erstellt:** 31. März 2026  
**Status:** ENTSCHIEDEN ✅
