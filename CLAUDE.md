# DIN 18599 IFC — Entwicklungsregeln

> Offener Datenstandard für energetische Gebäudeakten (Software-neutral)
> Lizenz: Apache 2.0 | Organisation: DWE Beratung GmbH

## Tech Stack

- **Backend/API:** Python 3.12, FastAPI, SQLAlchemy, PostgreSQL
- **Frontend/Viewer:** React 19, TypeScript, Vite, Three.js (3D/Web-IFC)
- **Datenformat:** JSON Schema (Draft-07). Produktiv: v3.1. In Entwicklung: v4.0 als .dwe-Container (Greenfield, kein Diff auf v3.x)
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

catalog/                # Kern-Kataloge (Struktur, öffentlich)
catalog-private/        # Normwerte (gitignored, DIN/Beuth-Urheberrecht)
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
- **Schema-First-Workflow:** JSON Schema in `schema/` ist die Single Source of Truth — DB, TS-Typen und Doku werden daraus abgeleitet.
- Abwärtskompatibilität beachten, SemVer-Bump + CHANGELOG-Eintrag pflegen.
- Bei jedem Release auch `database/schema.sql` mitziehen und Migration-Dokument (`schema/MIGRATION_vX.Y_to_vX.Z.md`) schreiben.
- DWEapp (`/opt/weclapp-manager`) ist primärer Konsument — nach Schema-Änderungen dort `npm run schema:check` ausführen.
- Details: siehe [CONTRIBUTING.md](CONTRIBUTING.md).

## Wichtige Dateien

- **Schema v4.0 (in Entwicklung, Greenfield):** `schema/v4.0/sidecar.schema.json` + `schema/v4.0/manifest.schema.json`
- **Schema v3.1 (produktiv eingefroren):** `schema/v3.1-complete.json`
- **Schema v3.0 (Basis der DWEapp-TS-Typen):** `schema/v3.0-complete.json`
- **Altstände v2.x:** `archive/schema-legacy/` (v3.2 verworfen, siehe CHANGELOG)
- **Datenbank-Schema:** `database/schema.sql` (v3.0 mit Helper-Funktionen)
- **Roadmap:** `ROADMAP.md`
- **Contributing:** `CONTRIBUTING.md`
- **Changelog:** `CHANGELOG.md`
- **Tests:** `TESTING.md`