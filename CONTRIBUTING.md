# Contributing Guide

Vielen Dank für dein Interesse, zu diesem Projekt beizutragen! 🎉

---

## 🎯 Wie kann ich beitragen?

### 1. Feedback & Diskussion

- 💬 **Issues:** [GitHub Issues](https://github.com/DWEBeratungGmbH/din18599-ifc/issues)
- 💡 **Discussions:** [GitHub Discussions](https://github.com/DWEBeratungGmbH/din18599-ifc/discussions)
- 📧 **E-Mail:** opensource@dwe-beratung.de

**Themen:**
- Verbesserungsvorschläge
- Praxiserfahrungen
- Anwendungsfälle
- Fragen zur Implementierung

### 2. Dokumentation verbessern

- 📝 README, Parameter-Matrix, Schema
- 🌍 Übersetzungen (Englisch, Französisch, etc.)
- 📚 Tutorials, Guides, Best Practices
- 🎓 Beispiele aus der Praxis

### 3. Code & Tools

- 🔧 Validator, Viewer, API verbessern
- 🆕 Neue Tools entwickeln (IFC→Sidecar Converter)
- 🧪 Test-Cases und Beispieldateien
- 🐛 Bugs fixen

---

## 📋 Contribution Workflow

### 1. Fork & Clone

```bash
# Fork auf GitHub erstellen
# Dann klonen:
git clone https://github.com/DEIN_USERNAME/din18599-ifc.git
cd din18599-ifc
```

### 2. Branch erstellen

```bash
git checkout -b feature/mein-feature
# oder
git checkout -b fix/bug-beschreibung
```

**Branch-Naming:**
- `feature/` - Neue Features
- `fix/` - Bugfixes
- `docs/` - Dokumentation
- `refactor/` - Code-Refactoring
- `test/` - Tests

### 3. Änderungen committen

```bash
git add .
git commit -m "feat: Neue Feature-Beschreibung"
```

**Commit-Message-Format:**
```
<type>: <subject>

<body (optional)>

<footer (optional)>
```

**Types:**
- `feat:` - Neues Feature
- `fix:` - Bugfix
- `docs:` - Dokumentation
- `style:` - Formatierung
- `refactor:` - Code-Refactoring
- `test:` - Tests
- `chore:` - Build, CI/CD

**Beispiele:**
```
feat: Layer Structures Visualisierung im Viewer

- Schichtaufbau-Tabelle hinzugefügt
- Materials-Liste mit Air Layers
- LOD-Badge anzeigen

Closes #42
```

### 4. Tests ausführen

```bash
# Python Validator
python3 tools/validate.py examples/*.din18599.json

# Schema-Validierung
python3 -m json.tool gebaeude.din18599.schema.json > /dev/null
```

### 5. Pull Request öffnen

```bash
git push origin feature/mein-feature
```

Dann auf GitHub:
1. **Pull Request** gegen `main` öffnen
2. **Beschreibung** ausfüllen (Was, Warum, Wie)
3. **Review** abwarten
4. **Anpassungen** vornehmen (falls nötig)

---

## 🎨 Code-Qualitätsstandards

### Python

**Style Guide:** PEP 8

```python
# ✅ Gut
def validate_file(json_path: str, schema: dict) -> bool:
    """Validiert JSON-Datei gegen Schema."""
    try:
        with open(json_path, 'r') as f:
            data = json.load(f)
        validate(instance=data, schema=schema)
        return True
    except ValidationError as e:
        print(f"Validierung fehlgeschlagen: {e.message}")
        return False

# ❌ Schlecht
def val(p,s):
    f=open(p);d=json.load(f);validate(d,s);return True
```

**Tools:**
```bash
# Linting
pylint tools/validate.py

# Formatting
black tools/validate.py
```

### JavaScript

**Style Guide:** ESLint + Prettier

```javascript
// ✅ Gut
function renderDashboard(data) {
  if (!data.input || !data.meta) {
    showError("Fehlendes 'input' oder 'meta' Objekt.");
    return;
  }
  
  const zones = data.input.zones || [];
  zones.forEach(zone => {
    renderZone(zone);
  });
}

// ❌ Schlecht
function r(d){if(!d.input)return;d.input.zones.forEach(z=>rZ(z))}
```

**Tools:**
```bash
# Linting
eslint viewer/*.js

# Formatting
prettier --write viewer/*.js
```

### JSON

**Formatierung:** 2 Spaces, sortierte Keys

```json
{
  "id": "ZONE-01",
  "name": "Wohnbereich",
  "area_an": 85.5
}
```

**Tools:**
```bash
# Formatierung
python3 -m json.tool input.json > output.json
```

---

## 📐 Schema-Änderungen

### Workflow

1. **Issue öffnen** - Diskussion über Änderung
2. **Schema anpassen** - `gebaeude.din18599.schema.json`
3. **Parameter-Matrix aktualisieren** - `docs/PARAMETER_MATRIX.md`
4. **Beispiele anpassen** - `examples/*.din18599.json`
5. **Tests anpassen** - Validierung prüfen
6. **Dokumentation** - README, LOD_GUIDE, etc.

### Abwärtskompatibilität

**Breaking Changes vermeiden:**
- ❌ Felder umbenennen
- ❌ Felder löschen
- ❌ Typen ändern
- ❌ Required-Felder hinzufügen

**Erlaubt:**
- ✅ Neue optionale Felder
- ✅ Neue Enum-Werte
- ✅ Neue Definitionen
- ✅ Beschreibungen verbessern

**Versionierung:**
- **Major:** Breaking Changes (v1.0 → v2.0)
- **Minor:** Neue Features (v1.0 → v1.1)
- **Patch:** Bugfixes (v1.0.0 → v1.0.1)

---

## 🧪 Testing

### Validator-Tests

```bash
# Alle Beispiele validieren
for file in examples/*.din18599.json; do
  python3 tools/validate.py "$file" || exit 1
done
```

### Schema-Tests

```bash
# Schema ist valides JSON
python3 -m json.tool gebaeude.din18599.schema.json > /dev/null

# Schema-Validierung mit Ajv
npm install -g ajv-cli
ajv compile -s gebaeude.din18599.schema.json
```

### Viewer-Tests

```bash
# Lokalen Server starten
python3 -m http.server 8000

# Manuell testen:
# 1. http://localhost:8000/viewer/index.html öffnen
# 2. Beispiele per Dropdown laden
# 3. Drag & Drop testen
```

---

## 📚 Dokumentation

### Struktur

```
docs/
├── ARCHITECTURE.md          # Architektur, DB-Schema
├── IFC_SIDECAR_LINK.md      # GUID-Mapping, Datenfluss
├── PARAMETER_MATRIX.md      # Alle Parameter
├── LOD_GUIDE.md             # LOD-Definitionen
└── KATALOG_VERWENDUNG.md    # Katalog-Integration
```

### Markdown-Stil

- **Überschriften:** `#`, `##`, `###`
- **Listen:** `-` (nicht `*`)
- **Code-Blöcke:** ` ```json ` (mit Sprache)
- **Tabellen:** Markdown-Tabellen
- **Links:** `[Text](URL)`

### Beispiele

```markdown
## Überschrift

**Fett** und *kursiv*

- Liste Item 1
- Liste Item 2

```json
{
  "example": "code"
}
```

| Spalte 1 | Spalte 2 |
|----------|----------|
| Wert 1   | Wert 2   |
```

---

## 🔍 Review-Prozess

### Was wird geprüft?

1. **Funktionalität** - Funktioniert der Code?
2. **Tests** - Sind Tests vorhanden und bestehen sie?
3. **Dokumentation** - Ist die Änderung dokumentiert?
4. **Code-Qualität** - Ist der Code sauber und lesbar?
5. **Abwärtskompatibilität** - Keine Breaking Changes?

### Review-Feedback

- 💬 **Kommentare** - Verbesserungsvorschläge
- ✅ **Approve** - Änderung ist gut
- ❌ **Request Changes** - Änderungen erforderlich

### Merge

- **Squash Merge** - Alle Commits werden zusammengefasst
- **Merge Message** - Beschreibung der Änderung
- **Delete Branch** - Branch wird nach Merge gelöscht

---

## 🏆 Contributor-Anerkennung

Alle Contributors werden in der [Contributors-Liste](https://github.com/DWEBeratungGmbH/din18599-ifc/graphs/contributors) aufgeführt.

**Besondere Beiträge:**
- 🌟 **Major Features** - Erwähnung im CHANGELOG
- 📚 **Dokumentation** - Erwähnung in der Dokumentation
- 🐛 **Bugfixes** - Erwähnung im CHANGELOG

---

## 📞 Kontakt

- **Issues:** [GitHub Issues](https://github.com/DWEBeratungGmbH/din18599-ifc/issues)
- **Discussions:** [GitHub Discussions](https://github.com/DWEBeratungGmbH/din18599-ifc/discussions)
- **E-Mail:** opensource@dwe-beratung.de

---

## 📄 Lizenz

Durch deine Beiträge stimmst du zu, dass deine Arbeit unter der **Apache License 2.0** lizenziert wird.

Siehe [LICENSE](LICENSE) für Details.

---

**Vielen Dank für deine Unterstützung! 🙏**
