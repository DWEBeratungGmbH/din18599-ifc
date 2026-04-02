#!/bin/bash
#
# Test-Skript für DIN18599 Upload-Wizard
# Testet den kompletten Upload-Flow mit IFC + EVEBI Dateien
#

# Farben für Output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
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

# Test 1: IFC-Parser
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📋 Test 1: IFC-Parser${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

IFC_RESPONSE=$(curl -s -X POST "$BACKEND_URL/parse-ifc" -F "file=@$IFC_FILE")
IFC_WALLS=$(echo "$IFC_RESPONSE" | jq -r '.walls | length')
IFC_ROOFS=$(echo "$IFC_RESPONSE" | jq -r '.roofs | length')
IFC_FLOORS=$(echo "$IFC_RESPONSE" | jq -r '.floors | length')
IFC_WINDOWS=$(echo "$IFC_RESPONSE" | jq -r '.windows | length')

echo -e "${BLUE}IFC Elemente:${NC}"
echo -e "   Wände:   $IFC_WALLS"
echo -e "   Dächer:  $IFC_ROOFS"
echo -e "   Böden:   $IFC_FLOORS"
echo -e "   Fenster: $IFC_WINDOWS"
echo ""

# Prüfe erste Wand aus IFC
if [ "$IFC_WALLS" -gt 0 ]; then
    echo -e "${BLUE}Erste Wand (IFC-Parser):${NC}"
    echo "$IFC_RESPONSE" | jq -r '.walls[0] | "   GUID: \(.guid)\n   Name: \(.name)\n   Area: \(.area) m²\n   Orientation: \(.properties.Orientation // "null")°\n   Inclination: \(.properties.Inclination // "null")°"'
    echo ""
fi

# Prüfe erstes Fenster aus IFC
if [ "$IFC_WINDOWS" -gt 0 ]; then
    echo -e "${BLUE}Erstes Fenster (IFC-Parser):${NC}"
    echo "$IFC_RESPONSE" | jq -r '.windows[0] | "   GUID: \(.guid)\n   Name: \(.name)\n   Area: \(.area) m²"'
    echo ""
fi

# Test 2: EVEBI-Parser
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📋 Test 2: EVEBI-Parser${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

EVEBI_RESPONSE=$(curl -s -X POST "$BACKEND_URL/parse-evebi" -F "file=@$EVEBI_FILE")
EVEBI_ELEMENTS=$(echo "$EVEBI_RESPONSE" | jq -r '.elements_count // 0')
EVEBI_ZONES=$(echo "$EVEBI_RESPONSE" | jq -r '.zones_count // 0')
EVEBI_CONSTRUCTIONS=$(echo "$EVEBI_RESPONSE" | jq -r '.constructions_count // 0')

echo -e "${BLUE}EVEBI Daten:${NC}"
echo -e "   Elemente:       $EVEBI_ELEMENTS"
echo -e "   Zonen:          $EVEBI_ZONES"
echo -e "   Konstruktionen: $EVEBI_CONSTRUCTIONS"
echo ""

# Test 3: Sidecar Generator
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📋 Test 3: Sidecar Generator${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

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
    echo -e "${RED}Backend-Logs (letzte 50 Zeilen):${NC}"
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
    echo -e "${YELLOW}⚠️  Warnings:${NC}"
    echo "$BODY" | jq -r '.warnings[] | "   - \(.)"'
fi

echo ""

# Test 4: Parent-Child-Beziehungen
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔗 Test 4: Parent-Child-Beziehungen${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

OPENINGS_WITH_PARENT=$(echo "$BODY" | jq -r '[.sidecar.input.envelope.openings[] | select(.parent_element_id != null)] | length')
TOTAL_OPENINGS=$(echo "$BODY" | jq -r '.sidecar.input.envelope.openings | length')

echo -e "   Fenster mit Parent: ${GREEN}$OPENINGS_WITH_PARENT${NC} / $TOTAL_OPENINGS"

if [ "$OPENINGS_WITH_PARENT" -gt 0 ]; then
    echo -e "${GREEN}   ✅ Parent-Child-Beziehungen gefunden!${NC}"
    echo ""
    echo -e "${BLUE}   Beispiele:${NC}"
    echo "$BODY" | jq -r '.sidecar.input.envelope.openings[0:3] | .[] | "      • \(.name) → Parent: \(.parent_element_id // "null") (Orientation: \(.orientation // "null")°)"'
else
    echo -e "${RED}   ⚠️  Keine Parent-Child-Beziehungen gefunden${NC}"
fi

echo ""

# Test 5: Orientierung & Neigung
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🧭 Test 5: Orientierung & Neigung${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

WALLS_WITH_ORIENTATION=$(echo "$BODY" | jq -r '[.sidecar.input.envelope.walls_external[] | select(.orientation != null and .orientation != 0)] | length')
TOTAL_WALLS=$(echo "$BODY" | jq -r '.sidecar.input.envelope.walls_external | length')

echo -e "   Wände mit Orientierung: ${GREEN}$WALLS_WITH_ORIENTATION${NC} / $TOTAL_WALLS"

if [ "$WALLS_WITH_ORIENTATION" -gt 0 ]; then
    echo -e "${GREEN}   ✅ Orientierungen gefunden!${NC}"
    echo ""
    echo -e "${BLUE}   Beispiele:${NC}"
    echo "$BODY" | jq -r '.sidecar.input.envelope.walls_external[0:3] | .[] | select(.orientation != null) | "      • \(.name): \(.orientation)° (Neigung: \(.inclination)°)"'
else
    echo -e "${YELLOW}   ⚠️  Keine Orientierungen gefunden${NC}"
    echo ""
    echo -e "${BLUE}   Erste Wand im Sidecar:${NC}"
    echo "$BODY" | jq -r '.sidecar.input.envelope.walls_external[0] | "      ID: \(.id)\n      Name: \(.name)\n      Orientation: \(.orientation // "null")\n      Inclination: \(.inclination // "null")\n      Area: \(.area) m²"'
fi

echo ""

# Test 6: U-Werte
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🌡️  Test 6: U-Werte${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

WALLS_WITH_UVALUE=$(echo "$BODY" | jq -r '[.sidecar.input.envelope.walls_external[] | select(.u_value_undisturbed > 0)] | length')
WINDOWS_WITH_UVALUE=$(echo "$BODY" | jq -r '[.sidecar.input.envelope.openings[] | select(.u_value_glass > 0)] | length')

echo -e "   Wände mit U-Wert:   ${GREEN}$WALLS_WITH_UVALUE${NC} / $TOTAL_WALLS"
echo -e "   Fenster mit U-Wert: ${GREEN}$WINDOWS_WITH_UVALUE${NC} / $TOTAL_OPENINGS"

if [ "$WALLS_WITH_UVALUE" -gt 0 ]; then
    echo ""
    echo -e "${BLUE}   Beispiel Wand:${NC}"
    echo "$BODY" | jq -r '[.sidecar.input.envelope.walls_external[] | select(.u_value_undisturbed > 0)][0] | "      • \(.name): U=\(.u_value_undisturbed) W/(m²K)"'
fi

if [ "$WINDOWS_WITH_UVALUE" -gt 0 ]; then
    echo ""
    echo -e "${BLUE}   Beispiel Fenster:${NC}"
    echo "$BODY" | jq -r '[.sidecar.input.envelope.openings[] | select(.u_value_glass > 0)][0] | "      • \(.name): U_glass=\(.u_value_glass) W/(m²K)"'
fi

echo ""

# Zusammenfassung
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ Test erfolgreich abgeschlossen!${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Bewertung
SCORE=0
MAX_SCORE=6

[ "$HTTP_CODE" == "200" ] && ((SCORE++))
[ "$OPENINGS_WITH_PARENT" -gt 0 ] && ((SCORE++))
[ "$WALLS_WITH_UVALUE" -gt 0 ] && ((SCORE++))
[ "$WINDOWS_WITH_UVALUE" -gt 0 ] && ((SCORE++))
[ "$WALLS_WITH_ORIENTATION" -gt 0 ] && ((SCORE++))
[ "$WARNINGS" -eq 0 ] && ((SCORE++))

echo -e "${BLUE}📊 Bewertung: ${GREEN}$SCORE${NC}/${MAX_SCORE} Tests bestanden${NC}"
echo ""

if [ "$SCORE" -eq "$MAX_SCORE" ]; then
    echo -e "${GREEN}🎉 Perfekt! Alle Tests bestanden!${NC}"
elif [ "$SCORE" -ge 4 ]; then
    echo -e "${YELLOW}⚠️  Gut, aber es gibt noch Verbesserungspotenzial${NC}"
else
    echo -e "${RED}❌ Mehrere Tests fehlgeschlagen - bitte prüfen!${NC}"
fi

echo ""
echo -e "${BLUE}💡 Nächste Schritte:${NC}"
echo -e "   1. Öffne ${CYAN}http://localhost:3003${NC} im Browser"
echo -e "   2. Lade die gleichen Dateien hoch"
echo -e "   3. Prüfe Gebäudehülle-Tab im Viewer"
echo -e "   4. Fenster sollten unter Wänden erscheinen (expandierbar)"
echo ""

# Speichere Sidecar JSON für Debugging
SIDECAR_FILE="/tmp/sidecar-test-$(date +%Y%m%d-%H%M%S).json"
echo "$BODY" | jq '.sidecar' > "$SIDECAR_FILE"
echo -e "${BLUE}💾 Sidecar JSON gespeichert: ${CYAN}$SIDECAR_FILE${NC}"
echo ""
