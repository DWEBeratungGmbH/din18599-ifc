# DIN18599 IFC - Quickstart Guide

**Ziel:** In 10 Minuten von IFC + EVEBI zu Sidecar JSON

---

## 🚀 Setup (5 Minuten)

### 1. Repository klonen

```bash
git clone https://github.com/DWEBeratungGmbH/din18599-ifc.git
cd din18599-ifc
```

### 2. Backend Setup

```bash
# Python venv erstellen
cd api
python3 -m venv venv
source venv/bin/activate

# Dependencies installieren
pip install -r requirements.txt
```

**Hinweis:** Falls `python3-venv` fehlt:
```bash
sudo apt install python3.12-venv
```

### 3. Viewer Setup

```bash
# In neuem Terminal
cd viewer
npm install
```

---

## 🎬 Start (1 Minute)

### Backend starten

```bash
cd api
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

**✓ Backend läuft:** http://localhost:8000

### Viewer starten

```bash
cd viewer
npm run dev
```

**✓ Viewer läuft:** http://localhost:3002

---

## 📤 Upload & Processing (2 Minuten)

### 1. Viewer öffnen

Browser: http://localhost:3002

### 2. Dateien hochladen

1. Klick auf **"Neue Dateien"**
2. **IFC-Datei** auswählen (z.B. `sources/IFC_EVBI/DIN18599TestIFCv2.ifc`)
3. **EVEBI .evea** auswählen (z.B. `sources/IFC_EVBI/DIN18599Test_260401.evea`)
4. Klick auf **"Sidecar generieren"**

### 3. Ergebnis

**Processing:** ~5-10 Sekunden

**Anzeige:**
- ✓ Mapping Statistics
- ✓ Match-Rate (z.B. 89%)
- ✓ Unmatched Elements

**3D-Viewer:** Gebäude wird angezeigt

---

## 💾 Download (1 Minute)

### Sidecar JSON downloaden

1. Klick auf **"JSON Download"**
2. Datei wird gespeichert: `{project_name}.din18599.json`

### Datei öffnen

```bash
# Pretty-print
cat sidecar.din18599.json | jq .

# In Editor öffnen
code sidecar.din18599.json
```

---

## 🔍 Sidecar JSON Struktur

```json
{
  "$schema": "https://din18599-ifc.de/schema/v2.1/complete",
  "meta": {
    "project_name": "DIN18599Test",
    "ifc_file_ref": "DIN18599TestIFCv2.ifc",
    "energy_data_source": {
      "type": "EVEBI",
      "file": "DIN18599Test_260401.evea"
    },
    "mapping_stats": {
      "total_ifc": 45,
      "matched": 40,
      "match_rate": 0.89
    }
  },
  "input": {
    "building": { ... },
    "zones": [ ... ],
    "envelope": {
      "walls_external": [
        {
          "id": "wall_001",
          "ifc_guid": "1ybs9cI0P0uhJtYtcGuM9Q",
          "evebi_guid": "{2819422A-...}",
          "posno": "001",
          "area": 15.49,
          "orientation": 270,
          "u_value_undisturbed": 1.2,
          "construction": {
            "name": "Außenwand",
            "layers": [
              {
                "material": "Putz",
                "thickness": 0.015,
                "lambda": 0.87
              },
              ...
            ]
          }
        }
      ]
    }
  }
}
```

---

## 🧪 Testing (1 Minute)

### Beispiel-Dateien verwenden

```bash
# IFC-Datei
sources/IFC_EVBI/DIN18599TestIFCv2.ifc

# EVEBI-Archiv
sources/IFC_EVBI/DIN18599Test_260401.evea
```

### cURL Test

```bash
curl -X POST http://localhost:8000/process \
  -F "ifc_file=@sources/IFC_EVBI/DIN18599TestIFCv2.ifc" \
  -F "evebi_file=@sources/IFC_EVBI/DIN18599Test_260401.evea" \
  | jq .
```

---

## 📊 Mapping-Qualität prüfen

### Gute Mapping-Rate (>80%)

**Ursache:** PosNo in IFC und EVEBI vorhanden

**Beispiel:**
```json
{
  "stats": {
    "match_rate": 0.95,
    "matched": 38,
    "total_ifc": 40
  }
}
```

### Niedrige Mapping-Rate (<50%)

**Ursache:** Keine PosNo, nur Geometrie-Matching

**Lösung:**
1. In CASCADOS: Positionsnummern vergeben
2. In EVEBI: Beim Import PosNo übernehmen
3. Neu exportieren

---

## 🐛 Troubleshooting

### Backend startet nicht

**Fehler:** `ModuleNotFoundError: No module named 'ifcopenshell'`

**Lösung:**
```bash
pip install ifcopenshell==0.7.0
```

### Viewer zeigt "Connection refused"

**Ursache:** Backend läuft nicht

**Lösung:**
```bash
# Backend starten
cd api
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

### Upload schlägt fehl

**Fehler:** `IFC-Datei muss .ifc Extension haben`

**Lösung:** Datei-Extension prüfen (`.ifc`, `.evea`)

---

## 📚 Nächste Schritte

### Dokumentation

- **API-Dokumentation:** `api/README.md`
- **Mapping-Strategien:** `docs/MAPPING_STRATEGIES.md`
- **EVEBI Format:** `docs/EVEBI_FORMAT.md`

### Weitere Features

- **3D-Viewer:** IFC.js Integration (geplant)
- **Daten-Editor:** Inline-Editing (geplant)
- **Export:** IFC-Export mit Sidecar-Daten (geplant)

---

## 🤝 Support

- **GitHub Issues:** https://github.com/DWEBeratungGmbH/din18599-ifc/issues
- **Discussions:** https://github.com/DWEBeratungGmbH/din18599-ifc/discussions

---

**Viel Erfolg!** 🎉
