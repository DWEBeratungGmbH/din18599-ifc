#!/bin/bash
# ============================================================================
# DIN 18599 IFC Sidecar - Database Setup
# ============================================================================
# Beschreibung: Initialisiert PostgreSQL-Datenbank mit Schema und Seed-Daten
# Usage: ./database/setup.sh [--drop]
# ============================================================================

set -e

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Konfiguration
DB_NAME="${DB_NAME:-din18599}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}DIN 18599 IFC Sidecar - Database Setup${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Database: $DB_NAME"
echo "User: $DB_USER"
echo "Host: $DB_HOST:$DB_PORT"
echo ""

# Prüfe ob PostgreSQL läuft
if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" > /dev/null 2>&1; then
    echo -e "${RED}ERROR: PostgreSQL ist nicht erreichbar!${NC}"
    echo "Bitte starte PostgreSQL: sudo systemctl start postgresql"
    exit 1
fi

# Drop Database (optional)
if [ "$1" == "--drop" ]; then
    echo -e "${YELLOW}>>> Dropping existing database...${NC}"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "DROP DATABASE IF EXISTS $DB_NAME;" postgres
    echo -e "${GREEN}✓ Database dropped${NC}"
fi

# Create Database
echo -e "${YELLOW}>>> Creating database...${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;" postgres 2>/dev/null || echo "Database already exists"
echo -e "${GREEN}✓ Database created${NC}"

# Run Migrations
echo ""
echo -e "${YELLOW}>>> Running migrations...${NC}"
for migration in database/migrations/*.sql; do
    echo "  - $(basename $migration)"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$migration"
done
echo -e "${GREEN}✓ Migrations completed${NC}"

# Run Seeds
echo ""
echo -e "${YELLOW}>>> Running seeds...${NC}"
for seed in database/seeds/*.sql; do
    echo "  - $(basename $seed)"
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$seed" 2>&1 | grep -v "pg_read_file" || true
done
echo -e "${GREEN}✓ Seeds completed${NC}"

# Verify
echo ""
echo -e "${YELLOW}>>> Verifying setup...${NC}"
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'din18599'
ORDER BY tablename;
"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✓ Database setup completed!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Start API: cd api && uvicorn main:app --reload"
echo "  2. Open Viewer: http://localhost:8000/viewer/index.html"
echo "  3. Test API: curl http://localhost:8000/health"
echo ""
