#!/bin/bash
#
# Test-Skript für DIN18599 Upload-Wizard
# Testet den kompletten Upload-Flow mit IFC + EVEBI Dateien
#

set -e

# Farben für Output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}DIN18599 Upload-Wizard Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Backend URL
BACKEND_URL="http://localhost:8001"

# Testdateien
IFC_FILE="/opt/din18599-ifc/sources/IFC_EVBI/DIN18599TestIFCv2.ifc"
EVEBI_FILE="/opt/din18599-ifc/sources/IFC_EVBI/DIN18599Test_260401.evea"

# Prüfe ob Dateien existieren
if [ ! -f "$IFC_FILE" ]; then
    echo -e "${RED}❌ IFC-Datei nicht gefunden: $IFC_FILE${NC}"
    exit 1
fi

if [ ! -f "$EVEBI_FILE" ]; then
    echo -e "${RED}❌ EVEBI-Datei nicht gefunden: $EVEBI_FILE${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Testdateien gefunden${NC}"
echo -e "   IFC:   $(basename $IFC_FILE) ($(du -h $IFC_FILE | cut -f1))"
echo -e "   EVEBI: $(basename $EVEBI_FILE) ($(du -h $EVEBI_FILE | cut -f1))"
echo ""

# Prüfe Backend Health
echo -e "${BLUE}🔍 Prüfe Backend...${NC}"
if ! curl -s -f "$BACKEND_URL/health" > /dev/null; then
    echo -e "${RED}❌ Backend nicht erreichbar auf $BACKEND_URL${NC}"
    echo -e "${RED}   Starte Backend mit: cd /opt/din18599-ifc/api && ./venv/bin/python -m uvicorn main:app --host 0.0.0.0 --port 8001${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Backend läuft${NC}"
echo ""

# Upload IFC + EVEBI und generiere Sidecar
echo -e "${BLUE}📤 Sende Upload-Request...${NC}"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BACKEND_URL/generate-sidecar" \
  -F "ifc_file=@$IFC_FILE" \
  -F "evebi_file=@$EVEBI_FILE")

# Extrahiere HTTP Status Code (letzte Zeile)
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
# Extrahiere Response Body (alles außer letzte Zeile)
BODY=$(echo "$RESPONSE" | head -n-1)

echo ""
echo -e "${BLUE}📊 Response:${NC}"
echo -e "   HTTP Status: $HTTP_CODE"
echo ""

if [ "$HTTP_CODE" != "200" ]; then
    echo -e "${RED}❌ Upload fehlgeschlagen!${NC}"
    echo ""
    echo -e "${RED}Response Body:${NC}"
    echo "$BODY" | jq '.' 2>/dev/null || echo "$BODY"
    echo ""
    echo -e "${RED}Backend-Logs:${NC}"
    tail -50 /tmp/din18599_backend.log | grep -A 20 "ERROR\|Exception\|Traceback" || tail -30 /tmp/din18599_backend.log
    exit 1
fi

echo -e "${GREEN}✅ Upload erfolgreich!${NC}"
echo ""

# Parse JSON Response
echo -e "${BLUE}📋 Sidecar Stats:${NC}"
echo "$BODY" | jq -r '
  "   IFC Elemente:     \(.stats.ifc_elements // 0)",
  "   EVEBI Elemente:   \(.stats.evebi_elements // 0)",
  "   EVEBI Zonen:      \(.stats.evebi_zones // 0)",
  "   ",
  "   Sidecar Wände:    \(.stats.sidecar_walls // 0)",
  "   Sidecar Dächer:   \(.stats.sidecar_roofs // 0)",
  "   Sidecar Böden:    \(.stats.sidecar_floors // 0)",
  "   Sidecar Fenster:  \(.stats.sidecar_windows // 0)",
  "   Sidecar Zonen:    \(.stats.sidecar_zones // 0)",
  "   ",
  "   Match-Rate:       \(.stats.match_rate // 0)%"
'

# Prüfe Warnings
WARNINGS=$(echo "$BODY" | jq -r '.warnings // [] | length')
if [ "$WARNINGS" -gt 0 ]; then
    echo ""
    echo -e "${RED}⚠️  Warnings:${NC}"
    echo "$BODY" | jq -r '.warnings[] | "   - \(.)"'
fi

echo ""

# Prüfe Parent-Child-Beziehungen
echo -e "${BLUE}🔗 Prüfe Parent-Child-Beziehungen...${NC}"
OPENINGS_WITH_PARENT=$(echo "$BODY" | jq -r '[.sidecar.input.envelope.openings[] | select(.parent_element_id != null)] | length')
TOTAL_OPENINGS=$(echo "$BODY" | jq -r '.sidecar.input.envelope.openings | length')

echo -e "   Fenster mit Parent: $OPENINGS_WITH_PARENT / $TOTAL_OPENINGS"

if [ "$OPENINGS_WITH_PARENT" -gt 0 ]; then
    echo -e "${GREEN}   ✅ Parent-Child-Beziehungen gefunden!${NC}"
    echo ""
    echo -e "${BLUE}   Beispiel:${NC}"
    echo "$BODY" | jq -r '.sidecar.input.envelope.openings[0] | "      ID: \(.id)\n      Name: \(.name)\n      Parent: \(.parent_element_id)\n      Orientation: \(.orientation)°\n      Area: \(.area) m²"'
else
    echo -e "${RED}   ⚠️  Keine Parent-Child-Beziehungen gefunden${NC}"
fi

echo ""

# Prüfe Orientierung
echo -e "${BLUE}🧭 Prüfe Orientierung...${NC}"
WALLS_WITH_ORIENTATION=$(echo "$BODY" | jq -r '[.sidecar.input.envelope.walls_external[] | select(.orientation != null and .orientation != 0)] | length')
TOTAL_WALLS=$(echo "$BODY" | jq -r '.sidecar.input.envelope.walls_external | length')

echo -e "   Wände mit Orientierung: $WALLS_WITH_ORIENTATION / $TOTAL_WALLS"

if [ "$WALLS_WITH_ORIENTATION" -gt 0 ]; then
    echo -e "${GREEN}   ✅ Orientierungen gefunden!${NC}"
    echo ""
    echo -e "${BLUE}   Beispiel:${NC}"
    echo "$BODY" | jq -r '.sidecar.input.envelope.walls_external[0] | "      ID: \(.id)\n      Name: \(.name)\n      Orientation: \(.orientation)°\n      Inclination: \(.inclination)°\n      Area: \(.area) m²"'
else
    echo -e "${RED}   ⚠️  Keine Orientierungen gefunden${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Test erfolgreich abgeschlossen!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}💡 Nächste Schritte:${NC}"
echo -e "   1. Öffne http://localhost:3003 im Browser"
echo -e "   2. Lade die gleichen Dateien hoch"
echo -e "   3. Prüfe Gebäudehülle-Tab im Viewer"
echo -e "   4. Fenster sollten unter Wänden erscheinen (expandierbar)"
echo ""
