# DIN 18599 IFC — Entwicklungsregeln

> Offener Datenstandard für energetische Gebäudeakten (Software-neutral)
> Lizenz: Apache 2.0 | Organisation: DWE Beratung GmbH

## Tech Stack

- **Backend/API:** Python 3.12, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend/Viewer:** React 19, TypeScript, Vite, Three.js (3D/Web-IFC)
- **Datenformat:** JSON Schema v2.0 (Draft-07)
- **Standards:** DIN 18599 (Energetische Bewertung von Gebäuden)

## Projektstruktur

```
api/                    # FastAPI Backend
├── main.py             # Endpunkte: /process, /health, /parse-ifc
├── parsers/            # IFC, EVEBI Parser
└── generators/         # Sidecar JSON Generator

viewer/                 # React/Vite Frontend
├── src/components/     # FileUpload, Dashboard, 3D-Viewer
└── vite.config.ts

database/               # PostgreSQL + TypeScript CLI
├── schema.sql
├── migrations/
└── cli.ts

docs/                   # Umfangreiche Dokumentation
├── ARCHITECTURE.md     # 5-Layer Architektur (34 KB)
├── EVEBI_FORMAT.md     # EVEBI Parser Spezifikation
├── LOD_GUIDE.md        # Level of Detail (100-500)
└── PARAMETER_MATRIX.md # DIN 18599 Parameter

catalogs/               # Bundesanzeiger 2020 Katalog
examples/               # LOD 100-400 Beispiel-JSON
tools/                  # CLI Validator (validate.py)
.plans/                 # Implementierungspläne (18 Dateien)
```

## Regeln

### Code-Stil
- **Python:** PEP 8
- **JavaScript/TypeScript:** ESLint + Prettier
- **Versionierung:** Semantic Versioning (MAJOR.MINOR.PATCH)

### Commits
- Conventional Commits: `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`
- Branch-Naming: `feature/`, `fix/`, `docs/`, `refactor/`, `test/`

### Schema-Änderungen
- Abwärtskompatibilität beachten
- Changelog pflegen
- Beispieldateien aktualisieren

## Wichtige Dateien

- **Schema:** `schema/gebaeude.din18599.schema.json`
- **Roadmap:** `ROADMAP.md` (Q2-Q4 2026)
- **Contributing:** `CONTRIBUTING.md`
- **Changelog:** `CHANGELOG.md`
- **Tests:** `TESTING.md`