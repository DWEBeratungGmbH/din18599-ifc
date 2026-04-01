# DIN18599 IFC Parser-System

**Version:** 1.0.0  
**Datum:** 1. April 2026  
**Status:** Production Ready

---

## 🎯 Überblick

Das Parser-System konvertiert **IFC-Dateien** (Geometrie) und **EVEBI-Archive** (Energetische Daten) in ein standardisiertes **DIN18599 Sidecar JSON**.

### Workflow

```
IFC-Datei (.ifc) + EVEBI-Archiv (.evea)
            ↓
    Parser-System (Python)
            ↓
DIN18599 Sidecar JSON (v2.1)
```

---

## 📦 Komponenten

### 1. EVEBI Parser (`parsers/evebi_parser.py`)

**Funktion:** Parst EVEBI `.evea` Archiv-Dateien

**Input:** `.evea` Datei (ZIP-Archiv mit `projekt.xml`)

**Output:** `EVEBIData` Objekt mit:
- Materialien (λ-Werte, Dichte, spez. Wärmekapazität)
- Konstruktionen (Schichtaufbauten, U-Werte)
- Bauteile (Wände, Dächer, Böden, Fenster)
- Zonen (Fläche, Volumen, Solltemperaturen)

**Beispiel:**
```python
from parsers import parse_evea

evebi_data = parse_evea('building.evea')

print(f"Projekt: {evebi_data.project_name}")
print(f"Materialien: {len(evebi_data.materials)}")
print(f"Bauteile: {len(evebi_data.elements)}")
```

### 2. IFC Parser (`parsers/ifc_parser.py`)

**Funktion:** Parst IFC-Dateien und extrahiert Geometrie

**Input:** `.ifc` Datei (IFC2x3 oder IFC4)

**Output:** `IFCGeometry` Objekt mit:
- Wände (IFC-GUID, Fläche, Orientierung, PosNo)
- Dächer (IFC-GUID, Fläche, Neigung)
- Böden (IFC-GUID, Fläche)
- Fenster & Türen

**Beispiel:**
```python
from parsers import parse_ifc

ifc_geometry = parse_ifc('building.ifc')

print(f"Projekt: {ifc_geometry.project_name}")
print(f"Wände: {len(ifc_geometry.walls)}")
print(f"Dächer: {len(ifc_geometry.roofs)}")
```

### 3. Mapping Engine (`parsers/mapper.py`)

**Funktion:** Verknüpft IFC-Geometrie mit EVEBI-Daten

**Strategien:**
1. **PosNo-basiert** (höchste Priorität)
   - Matching via Positionsnummer (Tag)
   - Confidence: 1.0 (100%)

2. **Name-basiert** (Fallback)
   - Similarity-Score (Levenshtein-ähnlich)
   - Confidence: 0.7 - 1.0

3. **Geometrie-basiert** (letzter Fallback)
   - Fläche + Orientierung + Neigung
   - Confidence: 0.7 - 1.0

**Beispiel:**
```python
from parsers import map_ifc_to_evebi

mapping_result = map_ifc_to_evebi(
    ifc_geometry=ifc_geometry,
    evebi_data=evebi_data,
    strategy='auto'  # oder 'posno', 'name', 'geometry'
)

print(f"Matches: {len(mapping_result.matches)}")
print(f"Match-Rate: {mapping_result.stats['match_rate']:.1%}")
print(f"Unmatched IFC: {len(mapping_result.unmatched_ifc)}")
```

### 4. Sidecar Generator (`parsers/sidecar_generator.py`)

**Funktion:** Generiert DIN18599 Sidecar JSON v2.1

**Input:**
- IFC-Geometrie
- EVEBI-Daten
- Mapping-Ergebnis

**Output:** DIN18599 Sidecar JSON

**Beispiel:**
```python
from parsers import generate_sidecar

sidecar = generate_sidecar(
    ifc_geometry=ifc_geometry,
    evebi_data=evebi_data,
    mapping_result=mapping_result,
    ifc_filename='building.ifc',
    evebi_filename='building.evea'
)

# Sidecar speichern
import json
with open('building.din18599.json', 'w') as f:
    json.dump(sidecar, f, indent=2)
```

---

## 🚀 Installation

### Voraussetzungen

- Python 3.12+
- pip

### Dependencies installieren

```bash
# 1. Virtual Environment erstellen
python3 -m venv venv

# 2. Aktivieren
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate  # Windows

# 3. Dependencies installieren
pip install -r requirements.txt
```

### Dependencies

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
jsonschema==4.20.0
python-multipart==0.0.9
ifcopenshell==0.7.0
```

**Hinweis:** `ifcopenshell` kann komplex zu installieren sein (C++ Dependencies). Bei Problemen siehe [ifcopenshell Installation Guide](https://ifcopenshell.org/docs/installation.html).

---

## 🔧 API Endpoints

### POST /process

**Beschreibung:** Verarbeitet IFC + EVEBI Dateien und generiert Sidecar JSON

**Request:**
```http
POST /process
Content-Type: multipart/form-data

ifc_file: building.ifc
evebi_file: building.evea
```

**Response (Success):**
```json
{
  "success": true,
  "sidecar": {
    "$schema": "https://din18599-ifc.de/schema/v2.1/complete",
    "meta": { ... },
    "input": { ... }
  },
  "stats": {
    "total_ifc": 45,
    "total_evebi": 42,
    "matched": 40,
    "unmatched_ifc": 5,
    "unmatched_evebi": 2,
    "match_rate": 0.89
  },
  "warnings": [
    "5 IFC-Elemente nicht gemappt",
    "2 EVEBI-Elemente nicht gemappt"
  ]
}
```

**Response (Error):**
```json
{
  "detail": "IFC-Datei muss .ifc Extension haben"
}
```

**Status Codes:**
- `200` - Success
- `400` - Bad Request (falsche Datei-Extension)
- `500` - Internal Server Error (Parser-Fehler)

### GET /health

**Beschreibung:** Health Check

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0.0"
}
```

---

## 🏃 Server starten

### Development

```bash
cd /opt/din18599-ifc/api
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Server läuft auf:** http://localhost:8000

**API-Dokumentation:** http://localhost:8000/docs (Swagger UI)

### Production

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 📝 Beispiel-Workflow

### Python Script

```python
#!/usr/bin/env python3
"""
Beispiel: IFC + EVEBI → Sidecar JSON
"""

from parsers import (
    parse_ifc,
    parse_evea,
    map_ifc_to_evebi,
    generate_sidecar
)
import json

# 1. IFC parsen
print("Parsing IFC...")
ifc_geometry = parse_ifc('examples/building.ifc')
print(f"✓ {len(ifc_geometry.all_elements)} IFC-Elemente gefunden")

# 2. EVEBI parsen
print("Parsing EVEBI...")
evebi_data = parse_evea('examples/building.evea')
print(f"✓ {len(evebi_data.elements)} EVEBI-Elemente gefunden")

# 3. Mapping
print("Mapping IFC ↔ EVEBI...")
mapping_result = map_ifc_to_evebi(ifc_geometry, evebi_data)
print(f"✓ {len(mapping_result.matches)} Matches ({mapping_result.stats['match_rate']:.1%})")

# 4. Sidecar generieren
print("Generating Sidecar...")
sidecar = generate_sidecar(
    ifc_geometry=ifc_geometry,
    evebi_data=evebi_data,
    mapping_result=mapping_result,
    ifc_filename='building.ifc',
    evebi_filename='building.evea'
)

# 5. Speichern
output_file = 'building.din18599.json'
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(sidecar, f, indent=2, ensure_ascii=False)

print(f"✓ Sidecar gespeichert: {output_file}")
```

### cURL

```bash
# Upload IFC + EVEBI
curl -X POST http://localhost:8000/process \
  -F "ifc_file=@building.ifc" \
  -F "evebi_file=@building.evea" \
  -o sidecar.json

# Pretty-print
cat sidecar.json | jq .
```

---

## 🧪 Testing

### Unit Tests

```bash
# Alle Tests
pytest

# Einzelner Test
pytest tests/test_evebi_parser.py

# Mit Coverage
pytest --cov=parsers tests/
```

### Integration Test

```bash
# End-to-End Test mit Real-World Daten
python tests/integration_test.py
```

**Test-Dateien:**
- `sources/IFC_EVBI/DIN18599TestIFCv2.ifc`
- `sources/IFC_EVBI/DIN18599Test_260401.evea`

---

## 📊 Datenmodell

### EVEBIData

```python
@dataclass
class EVEBIData:
    project_guid: str
    project_name: str
    materials: List[EVEBIMaterial]
    constructions: List[EVEBIConstruction]
    elements: List[EVEBIElement]
    zones: List[EVEBIZone]
```

### IFCGeometry

```python
@dataclass
class IFCGeometry:
    project_name: str
    site_name: Optional[str]
    building_name: Optional[str]
    walls: List[IFCElement]
    roofs: List[IFCElement]
    slabs: List[IFCElement]
    windows: List[IFCElement]
    doors: List[IFCElement]
    all_elements: List[IFCElement]
```

### MappingResult

```python
@dataclass
class MappingResult:
    matches: List[ElementMatch]
    unmatched_ifc: List[IFCElement]
    unmatched_evebi: List[EVEBIElement]
    stats: Dict[str, int]
```

---

## 🔍 Troubleshooting

### Problem: ifcopenshell Installation schlägt fehl

**Lösung 1:** Conda verwenden
```bash
conda install -c conda-forge ifcopenshell
```

**Lösung 2:** Docker verwenden
```bash
docker build -t din18599-parser .
docker run -p 8000:8000 din18599-parser
```

### Problem: EVEBI XML nicht gefunden

**Fehler:** `KeyError: 'projekt.xml'`

**Ursache:** `.evea` Datei ist kein ZIP oder enthält keine `projekt.xml`

**Lösung:** Prüfen, ob Datei korrekt ist:
```bash
unzip -l building.evea | grep projekt.xml
```

### Problem: Mapping-Rate zu niedrig

**Ursache:** Keine PosNo in IFC oder EVEBI

**Lösung:**
1. In CASCADOS: Positionsnummern vergeben (Tag-Feld)
2. In EVEBI: Beim Import darauf achten, dass PosNo übernommen wird
3. Fallback: Name-basiertes Matching verwenden

---

## 📚 Weitere Dokumentation

- **API-Dokumentation:** `docs/API.md`
- **Mapping-Strategien:** `docs/MAPPING_STRATEGIES.md`
- **EVEBI Format:** `docs/EVEBI_FORMAT.md`
- **Quickstart:** `docs/QUICKSTART.md`

---

## 🤝 Contributing

Contributions sind willkommen! Siehe [CONTRIBUTING.md](../CONTRIBUTING.md)

---

## 📄 Lizenz

Apache License 2.0 - Siehe [LICENSE](../LICENSE)

---

**Letzte Aktualisierung:** 1. April 2026  
**Version:** 1.0.0
