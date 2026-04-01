# Testing-Anleitung

**Datum:** 1. April 2026  
**Version:** 2.1.0

---

## 🚀 WO LÄUFT DIE APP?

### **Backend (FastAPI)**
```
URL: http://localhost:8000
Status: ✅ Läuft im Python venv
```

### **Frontend (React/Vite)**
```
URL: http://localhost:5173
Status: ⏸️ Muss gestartet werden (siehe unten)
```

---

## ✅ BACKEND TESTEN

### **1. Health Check**
```bash
curl http://localhost:8000/health
```

**Erwartete Ausgabe:**
```json
{"status": "ok"}
```

---

### **2. IFC-Datei parsen**
```bash
curl -X POST http://localhost:8000/parse-ifc \
  -F "ifc_file=@/opt/din18599-ifc/sources/IFC_EVBI/DIN18599TestIFCv2.ifc" \
  -s | jq .
```

**Erwartete Ausgabe:**
```json
{
  "success": true,
  "ifc_data": {
    "project_name": "DIN18599 Test",
    "building_guid": "...",
    "material_layers": [
      {
        "id": "LS-...",
        "name": "Außenwand",
        "layers": [...]
      }
    ],
    "walls": [...],
    "roofs": [...]
  }
}
```

---

### **3. EVEBI-Datei parsen**
```bash
curl -X POST http://localhost:8000/parse-evebi \
  -F "evebi_file=@/opt/din18599-ifc/sources/IFC_EVBI/IST-Zustand.Variante1 40EE WPB.evex" \
  -s | jq .
```

**Erwartete Ausgabe:**
```json
{
  "success": true,
  "evebi_data": {
    "project_name": "IST-Zustand",
    "materials": [...],
    "constructions": [...],
    "elements": [...],
    "zones": [...]
  }
}
```

---

### **4. Sidecar JSON generieren (Vollständiger Workflow)**
```bash
curl -X POST http://localhost:8000/generate-sidecar \
  -F "ifc_file=@/opt/din18599-ifc/sources/IFC_EVBI/DIN18599TestIFCv2.ifc" \
  -F "evebi_file=@/opt/din18599-ifc/sources/IFC_EVBI/IST-Zustand.Variante1 40EE WPB.evex" \
  -s | jq . > /tmp/sidecar_output.json
```

**Erwartete Ausgabe:**
```json
{
  "success": true,
  "sidecar": {
    "schema_info": {
      "version": "2.1.0"
    },
    "input": {
      "materials": [...],
      "layer_structures": [...],
      "elements": [...],
      "zones": [...]
    }
  },
  "stats": {
    "ifc_elements": 48,
    "evebi_elements": 204,
    "match_rate": 81.2
  }
}
```

**Sidecar JSON anschauen:**
```bash
cat /tmp/sidecar_output.json | jq .sidecar.input.layer_structures
```

---

### **5. Material-Layers prüfen**
```bash
curl -X POST http://localhost:8000/generate-sidecar \
  -F "ifc_file=@/opt/din18599-ifc/sources/IFC_EVBI/DIN18599TestIFCv2.ifc" \
  -F "evebi_file=@/opt/din18599-ifc/sources/IFC_EVBI/IST-Zustand.Variante1 40EE WPB.evex" \
  -s | jq '.sidecar.input.layer_structures[] | {name, layers: .layers | length, u_value: .u_value_calculated, source, catalog_ref}'
```

**Erwartete Ausgabe:**
```json
{
  "name": "Außenwand WDVS",
  "layers": 4,
  "u_value": 0.21,
  "source": "ifc_material_layer_set",
  "catalog_ref": null
}
```

---

## 🎨 FRONTEND STARTEN

### **1. Frontend-Server starten**
```bash
cd /opt/din18599-ifc/viewer
npm run dev
```

**Erwartete Ausgabe:**
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

### **2. Browser öffnen**
```
http://localhost:5173
```

### **3. Upload-Wizard testen**
1. **IFC-Datei hochladen:**
   - Wähle: `/opt/din18599-ifc/sources/IFC_EVBI/DIN18599TestIFCv2.ifc`
   - Klick "Upload"
   - ✅ Sollte: "48 Elemente extrahiert" zeigen

2. **EVEBI-Datei hochladen:**
   - Wähle: `/opt/din18599-ifc/sources/IFC_EVBI/IST-Zustand.Variante1 40EE WPB.evex`
   - Klick "Upload"
   - ✅ Sollte: "204 Elemente, 5 Zonen" zeigen

3. **Sidecar generieren:**
   - Klick "Generate Sidecar"
   - ✅ Sollte: Match-Rate 81.2% zeigen
   - ✅ Sollte: Sidecar JSON im Viewer anzeigen

---

## 🧪 ERWEITERTE TESTS

### **Test 1: Material-Layer-Extraktion**
```bash
# Prüfe ob IFC Material-Layers extrahiert werden
curl -X POST http://localhost:8000/parse-ifc \
  -F "ifc_file=@/opt/din18599-ifc/sources/IFC_EVBI/DIN18599TestIFCv2.ifc" \
  -s | jq '.ifc_data.material_layers | length'

# Erwartung: > 0 (wenn IFC Material-Layers hat)
```

### **Test 2: U-Wert-Berechnung**
```bash
# Prüfe ob U-Werte berechnet werden
curl -X POST http://localhost:8000/generate-sidecar \
  -F "ifc_file=@/opt/din18599-ifc/sources/IFC_EVBI/DIN18599TestIFCv2.ifc" \
  -F "evebi_file=@/opt/din18599-ifc/sources/IFC_EVBI/IST-Zustand.Variante1 40EE WPB.evex" \
  -s | jq '.sidecar.input.layer_structures[] | select(.u_value_calculated != null) | {name, u_value: .u_value_calculated}'

# Erwartung: U-Werte zwischen 0.1 und 3.0
```

### **Test 3: Katalog-Referenzen**
```bash
# Prüfe ob catalog_ref Feld vorhanden ist
curl -X POST http://localhost:8000/generate-sidecar \
  -F "ifc_file=@/opt/din18599-ifc/sources/IFC_EVBI/DIN18599TestIFCv2.ifc" \
  -F "evebi_file=@/opt/din18599-ifc/sources/IFC_EVBI/IST-Zustand.Variante1 40EE WPB.evex" \
  -s | jq '.sidecar.input.layer_structures[0] | has("catalog_ref")'

# Erwartung: true
```

### **Test 4: Daten-Provenienz**
```bash
# Prüfe source-Felder
curl -X POST http://localhost:8000/generate-sidecar \
  -F "ifc_file=@/opt/din18599-ifc/sources/IFC_EVBI/DIN18599TestIFCv2.ifc" \
  -F "evebi_file=@/opt/din18599-ifc/sources/IFC_EVBI/IST-Zustand.Variante1 40EE WPB.evex" \
  -s | jq '.sidecar.input.layer_structures[] | .source' | sort | uniq -c

# Erwartung: Verschiedene Sources (ifc_material_layer_set, ifc_material_single, etc.)
```

---

## 📊 PERFORMANCE-TEST

```bash
# Zeit messen
time curl -X POST http://localhost:8000/generate-sidecar \
  -F "ifc_file=@/opt/din18599-ifc/sources/IFC_EVBI/DIN18599TestIFCv2.ifc" \
  -F "evebi_file=@/opt/din18599-ifc/sources/IFC_EVBI/IST-Zustand.Variante1 40EE WPB.evex" \
  -s > /dev/null

# Erwartung: < 5 Sekunden
```

---

## 🐛 DEBUGGING

### **Backend-Logs anschauen**
```bash
# Wenn Backend im Hintergrund läuft
tail -f /tmp/din18599_api.log

# Oder direkt im Terminal (wenn im Vordergrund)
cd /opt/din18599-ifc/api
./venv/bin/uvicorn main:app --reload
```

### **Frontend-Logs**
```bash
# Im Browser: F12 → Console
# Oder im Terminal wo npm run dev läuft
```

### **Häufige Fehler**

**1. Backend nicht erreichbar**
```bash
# Prüfen ob Backend läuft
curl http://localhost:8000/health

# Falls nicht, starten:
cd /opt/din18599-ifc/api
./venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
```

**2. ModuleNotFoundError: ifcopenshell**
```bash
# ifcopenshell installieren
cd /opt/din18599-ifc/api
./venv/bin/pip install ifcopenshell
```

**3. CORS-Fehler im Frontend**
```bash
# Backend mit CORS starten (bereits konfiguriert)
# Prüfe main.py: app.add_middleware(CORSMiddleware, ...)
```

---

## 📁 TEST-DATEIEN

```
/opt/din18599-ifc/sources/IFC_EVBI/
├── DIN18599TestIFCv2.ifc          # IFC-Datei (48 Elemente)
├── DIN18599Test_260401.evea       # EVEBI-Datei (74 Elemente, 4 Zonen)
├── IST-Zustand.Variante1 40EE WPB.evex  # EVEBI-Datei (204 Elemente, 5 Zonen)
└── Breuer.evex                    # EVEBI-Datei (193 Elemente)
```

---

## ✅ SUCCESS CRITERIA

**Backend:**
- ✅ Health Check: 200 OK
- ✅ IFC-Parser: Material-Layers extrahiert
- ✅ EVEBI-Parser: Konstruktionen extrahiert
- ✅ Sidecar-Generator: Match-Rate > 80%
- ✅ U-Wert-Berechnung: Plausible Werte (0.1-3.0)

**Frontend:**
- ✅ Upload-Wizard: Dateien hochladen
- ✅ Sidecar-Generierung: Erfolgreich
- ✅ Viewer: JSON anzeigen

**Schema:**
- ✅ `catalog_ref` Feld vorhanden
- ✅ `source` Feld vorhanden
- ✅ `layers` vollständig aufgelöst
- ✅ `u_value_calculated` vorhanden (wenn möglich)

---

## 🚀 QUICK START

```bash
# 1. Backend starten (falls nicht läuft)
cd /opt/din18599-ifc/api
./venv/bin/uvicorn main:app --reload

# 2. In neuem Terminal: Frontend starten
cd /opt/din18599-ifc/viewer
npm run dev

# 3. In neuem Terminal: Test durchführen
curl -X POST http://localhost:8000/generate-sidecar \
  -F "ifc_file=@/opt/din18599-ifc/sources/IFC_EVBI/DIN18599TestIFCv2.ifc" \
  -F "evebi_file=@/opt/din18599-ifc/sources/IFC_EVBI/IST-Zustand.Variante1 40EE WPB.evex" \
  -s | jq .stats

# 4. Browser öffnen
# http://localhost:5173
```

---

## 📞 SUPPORT

**Logs:**
- Backend: `/tmp/din18599_api.log`
- Frontend: Browser Console (F12)

**Dokumentation:**
- Schema: `/opt/din18599-ifc/docs/SIDECAR_SCHEMA_v2.1.md`
- Layer-Strategy: `/opt/din18599-ifc/docs/LAYER_RESOLUTION_STRATEGY.md`
- Gap-Analysis: `/opt/din18599-ifc/docs/IFC_EVEBI_GAP_ANALYSIS.md`

**GitHub:**
- https://github.com/DWEBeratungGmbH/din18599-ifc
