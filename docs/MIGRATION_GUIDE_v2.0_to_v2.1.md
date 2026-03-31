# Migration Guide: v2.0 → v2.1

**Version:** 1.0  
**Stand:** 31. März 2026  
**Status:** Complete

---

## 🎯 Überblick

Dieser Guide beschreibt die Migration von DIN 18599 Sidecar Dateien von **v2.0** zu **v2.1**.

**Wichtig:** v2.1 ist eine **Breaking Change** Version mit strukturellen Änderungen!

---

## 📊 Hauptänderungen

### **1. Snapshot-Modell**

**v2.0:**
```json
{
  "input": {...},
  "output": {
    "final_energy_kwh_a": 23780,
    "primary_energy_kwh_a": 26110
  }
}
```

**v2.1:**
```json
{
  "input": {...},
  "scenarios": [...],
  "output": {
    "base": {
      "meta": {...},
      "useful_energy": {...},
      "final_energy": {...},
      "primary_energy": {...}
    },
    "scenario_xyz": {...}
  }
}
```

---

### **2. Input-Struktur: Hierarchisch**

**v2.0:**
```json
{
  "elements": [
    {"id": "wall_1", "type": "wall_external", "u_value": 1.2},
    {"id": "window_1", "type": "window", "u_value": 2.8}
  ]
}
```

**v2.1:**
```json
{
  "input": {
    "envelope": {
      "opaque_elements": {
        "walls_external": [
          {"id": "wall_1", "u_value": 1.2}
        ]
      },
      "transparent_elements": {
        "windows": [
          {"id": "window_1", "u_value": 2.8}
        ]
      }
    }
  }
}
```

---

### **3. Systems: Detailliert**

**v2.0:**
```json
{
  "heating": {
    "type": "gas_boiler",
    "efficiency": 0.85
  }
}
```

**v2.1:**
```json
{
  "systems": {
    "heating": {
      "generation": {
        "type": "gas_boiler",
        "efficiency": 0.85
      },
      "distribution": {...},
      "emission": {...},
      "control": {...}
    }
  }
}
```

---

### **4. Primärenergiefaktoren verschoben**

**v2.0:**
```json
{
  "output": {
    "primary_energy_factors": {
      "electricity": 1.8
    }
  }
}
```

**v2.1:**
```json
{
  "input": {
    "primary_energy": {
      "source": "GEG_2024",
      "factors": {
        "electricity": 1.8
      }
    }
  }
}
```

---

## 🛠️ Migration-Script

### **Automatische Migration:**

```bash
node scripts/migrate-v2.0-to-v2.1.js input-v2.0.json output-v2.1.json
```

### **Was das Script macht:**

✅ **Automatisch migriert:**
- Meta-Daten (mit Versionshistorie)
- Building-Daten
- Envelope (elements[] → hierarchisch)
- Systems (flach → detailliert)
- Scenarios (Delta-Modell bleibt)
- Primärenergiefaktoren (Output → Input)

❌ **NICHT migriert:**
- Output-Daten (müssen neu berechnet werden)
- Katalog-Referenzen (müssen manuell geprüft werden)

---

## ⚠️ Manuelle Nacharbeit

### **1. Output neu berechnen**

Output-Daten werden **nicht** migriert, da die Struktur komplett anders ist.

**Aktion:** Datei an Berechnungssoftware übergeben und neu berechnen lassen.

---

### **2. Katalog-Referenzen prüfen**

**v2.0:**
```json
{
  "construction_ref": "bundesanzeiger_wall_001"
}
```

**v2.1:**
```json
{
  "construction_ref": "WALL_EXT_BRICK_WDVS_160"
}
```

**Aktion:** Katalog-IDs an neues Katalog-System anpassen.

---

### **3. Usage Profiles prüfen**

**v2.0:**
```json
{
  "usage_profile": "17"  // String
}
```

**v2.1:**
```json
{
  "usage_profile_ref": "PROFILE_RES_EFH"  // Enum
}
```

**Aktion:** Nutzungsprofile an neues Enum anpassen.

---

### **4. IDs prüfen**

**v2.1 erfordert:** Alle Array-Elemente müssen `id` oder `ifc_guid` haben!

```json
// ❌ v2.0: ID optional
{"u_value": 1.2}

// ✅ v2.1: ID required
{"id": "wall_1", "u_value": 1.2}
```

**Aktion:** Fehlende IDs ergänzen.

---

## 📋 Checkliste

### **Nach der Migration:**

- [ ] Datei gegen Schema v2.1 validieren
- [ ] Katalog-Referenzen prüfen und anpassen
- [ ] Usage Profile Referenzen prüfen
- [ ] Fehlende IDs ergänzen
- [ ] Output neu berechnen lassen
- [ ] Ergebnis testen

---

## 🧪 Validierung

### **Schema-Validierung:**

```bash
# Mit ajv-cli
ajv validate -s schema/v2.1-complete.json -d output-v2.1.json

# Mit Python
python scripts/validate.py output-v2.1.json
```

---

## 📚 Referenzen

- **Schema v2.1:** `schema/v2.1-complete.json`
- **Konzept:** `docs/SCHEMA_V2.1_CONCEPT.md`
- **Guide:** `docs/SCHEMA_V2.1_GUIDE.md`
- **Merge-Algorithmus:** `docs/MERGE_ALGORITHM.md`

---

## ❓ FAQ

### **Q: Kann ich v2.0 und v2.1 parallel nutzen?**
A: Ja, aber Software muss beide Versionen unterstützen.

### **Q: Muss ich alle Dateien migrieren?**
A: Nein, v2.0 bleibt gültig. Migration nur bei Bedarf.

### **Q: Was passiert mit meinen alten Berechnungen?**
A: Output muss neu berechnet werden (neue Struktur).

### **Q: Sind Katalog-Referenzen kompatibel?**
A: Nein, neues Katalog-System → IDs müssen angepasst werden.

---

**Erstellt:** 31. März 2026  
**Version:** 1.0  
**Status:** Complete
