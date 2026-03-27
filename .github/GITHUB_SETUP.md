# GitHub Repository Setup

**Anleitung zur Konfiguration des GitHub Repositories**

---

## 1. Repository Settings

### About Section

**Gehe zu:** Repository → About (Zahnrad-Icon rechts oben)

**Description:**
```
Offenes Austauschformat für die energetische Gebäudeakte (IFC + DIN 18599 Sidecar)
```

**Website:**
```
https://din18599-ifc.de
```
*(Optional - wenn Domain vorhanden)*

**Topics:**
```
ifc
din18599
bim
energy-consulting
building-energy
json-schema
germany
geg
beg
open-source
apache-2
energy-efficiency
building-performance
thermal-simulation
```

---

## 2. Repository Features

**Gehe zu:** Settings → General → Features

**Aktivieren:**
- ✅ Wikis (für erweiterte Dokumentation)
- ✅ Issues (für Bug-Reports und Feature-Requests)
- ✅ Discussions (für Community-Austausch)
- ✅ Projects (für Roadmap)

**Deaktivieren:**
- ❌ Sponsorships (vorerst)

---

## 3. Branch Protection

**Gehe zu:** Settings → Branches → Add rule

**Branch name pattern:** `main` oder `master`

**Regeln:**
- ✅ Require a pull request before merging
- ✅ Require approvals (1)
- ✅ Dismiss stale pull request approvals when new commits are pushed
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging
- ❌ Require conversation resolution before merging (optional)
- ❌ Require signed commits (optional)

---

## 4. GitHub Actions (CI/CD)

**Erstelle:** `.github/workflows/validate.yml`

```yaml
name: Validate Schema & Examples

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  validate:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        pip install jsonschema
    
    - name: Validate Schema
      run: |
        python3 -m json.tool gebaeude.din18599.schema.json > /dev/null
    
    - name: Validate Examples
      run: |
        for file in examples/*.din18599.json; do
          echo "Validating $file"
          python3 tools/validate.py "$file" || exit 1
        done
```

---

## 5. Issue Templates

**Erstelle:** `.github/ISSUE_TEMPLATE/bug_report.md`

```markdown
---
name: Bug Report
about: Melde einen Fehler
title: '[BUG] '
labels: bug
assignees: ''
---

**Beschreibung**
Kurze Beschreibung des Fehlers.

**Reproduktion**
Schritte zur Reproduktion:
1. ...
2. ...

**Erwartetes Verhalten**
Was sollte passieren?

**Aktuelles Verhalten**
Was passiert stattdessen?

**Beispiel-Datei**
```json
{
  "schema_info": {...}
}
```

**Umgebung**
- OS: [z.B. Windows 10]
- Browser: [z.B. Chrome 120]
- Version: [z.B. v2.0.0]
```

**Erstelle:** `.github/ISSUE_TEMPLATE/feature_request.md`

```markdown
---
name: Feature Request
about: Schlage ein neues Feature vor
title: '[FEATURE] '
labels: enhancement
assignees: ''
---

**Problem**
Welches Problem löst dieses Feature?

**Lösung**
Wie sollte das Feature funktionieren?

**Alternativen**
Welche Alternativen hast du erwogen?

**Zusätzlicher Kontext**
Screenshots, Mockups, etc.
```

---

## 6. Pull Request Template

**Erstelle:** `.github/PULL_REQUEST_TEMPLATE.md`

```markdown
## Beschreibung

Kurze Beschreibung der Änderungen.

## Art der Änderung

- [ ] Bugfix (non-breaking change)
- [ ] Neues Feature (non-breaking change)
- [ ] Breaking Change (fix oder feature, das bestehende Funktionalität ändert)
- [ ] Dokumentation

## Checklist

- [ ] Code folgt den Style Guidelines
- [ ] Self-Review durchgeführt
- [ ] Kommentare hinzugefügt (bei komplexem Code)
- [ ] Dokumentation aktualisiert
- [ ] Keine neuen Warnings
- [ ] Tests hinzugefügt (falls zutreffend)
- [ ] Alle Tests bestehen
- [ ] Beispiele aktualisiert (falls zutreffend)

## Tests

Beschreibe die durchgeführten Tests.

## Screenshots (falls zutreffend)

Füge Screenshots hinzu.
```

---

## 7. GitHub Discussions

**Kategorien erstellen:**

1. **💡 Ideas** - Feature-Vorschläge
2. **🙏 Q&A** - Fragen & Antworten
3. **📣 Announcements** - Ankündigungen
4. **🎓 Show and Tell** - Praxisbeispiele
5. **🐛 Bugs** - Bug-Diskussionen

---

## 8. GitHub Projects

**Projekt erstellen:** "Roadmap v2.x"

**Spalten:**
- 📋 Backlog
- 🔜 Next Up
- 🚧 In Progress
- ✅ Done

**Karten:**
- Viewer-Erweiterung (Layer Structures, Materials, LOD-Badge)
- Editing MVP (Inline-Edit U-Werte, Save/Export)
- Schichtaufbau-Editor (Modal, Drag-to-Reorder)
- IFC-Viewer Integration (xeokit)
- Validator-Erweiterung (GUID-Checks, LOD-Validierung)

---

## 9. Release erstellen

**Gehe zu:** Releases → Create a new release

**Tag:** `v2.0.0`

**Release title:** `v2.0.0 - Production Ready`

**Description:** (aus CHANGELOG.md kopieren)

```markdown
## 🎉 Major Release - Production Ready

Vollständige Überarbeitung des Schemas und der Dokumentation.

### ✨ Highlights

- **LOD-Konzept** (Level of Detail 100-500)
- **Varianten-Management** (Delta-Modell)
- **Layer Structures** (Schichtaufbauten)
- **Bundesanzeiger 2020** Katalog (97 U-Werte)
- **Vollständige Dokumentation** (8 Dateien)

### 📚 Dokumentation

- [README.md](README.md)
- [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [LOD_GUIDE.md](docs/LOD_GUIDE.md)
- [KATALOG_VERWENDUNG.md](docs/KATALOG_VERWENDUNG.md)

### 🔗 Links

- **Repository:** https://github.com/DWEBeratungGmbH/din18599-ifc
- **Issues:** https://github.com/DWEBeratungGmbH/din18599-ifc/issues
- **Discussions:** https://github.com/DWEBeratungGmbH/din18599-ifc/discussions

Siehe [CHANGELOG.md](CHANGELOG.md) für Details.
```

**Assets:** Keine (alles im Repo)

---

## 10. Social Preview

**Gehe zu:** Settings → General → Social preview

**Erstelle ein Bild (1280x640px):**
- Logo: IFC + DIN 18599
- Titel: "IFC + DIN 18599 Sidecar"
- Untertitel: "Offenes Austauschformat für die energetische Gebäudeakte"
- Hintergrund: Blau/Grün (Energie-Farben)

**Tool:** Canva, Figma, oder https://socialify.git.ci/

---

## 11. README Badges

**Bereits vorhanden:**
```markdown
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-2.0.0-green.svg)](CHANGELOG.md)
[![Schema](https://img.shields.io/badge/Schema-JSON%20Draft--07-orange.svg)](gebaeude.din18599.schema.json)
```

**Optional hinzufügen:**
```markdown
[![GitHub stars](https://img.shields.io/github/stars/DWEBeratungGmbH/din18599-ifc?style=social)](https://github.com/DWEBeratungGmbH/din18599-ifc/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/DWEBeratungGmbH/din18599-ifc?style=social)](https://github.com/DWEBeratungGmbH/din18599-ifc/network/members)
[![GitHub issues](https://img.shields.io/github/issues/DWEBeratungGmbH/din18599-ifc)](https://github.com/DWEBeratungGmbH/din18599-ifc/issues)
[![CI](https://github.com/DWEBeratungGmbH/din18599-ifc/workflows/Validate%20Schema%20%26%20Examples/badge.svg)](https://github.com/DWEBeratungGmbH/din18599-ifc/actions)
```

---

## ✅ Checklist

- [ ] About Section konfiguriert
- [ ] Topics hinzugefügt
- [ ] Features aktiviert (Issues, Discussions, Wikis)
- [ ] Branch Protection aktiviert
- [ ] GitHub Actions erstellt
- [ ] Issue Templates erstellt
- [ ] PR Template erstellt
- [ ] Discussions-Kategorien erstellt
- [ ] GitHub Project erstellt
- [ ] Release v2.0.0 erstellt
- [ ] Social Preview hochgeladen
- [ ] README Badges aktualisiert

---

**Status:** Bereit für Community-Launch! 🚀
