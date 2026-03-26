# IFC + DIN 18599 Sidecar
**Ein offenes Austauschformat für Energieberatungsprojekte in Deutschland**

> **Status:** Konzept / Draft 0.1  
> **Ziel:** Software-unabhängiger Datenaustausch zwischen BIM-Software, Energieberater-Software und Förderstellen.

## Überblick

Das Konzept kombiniert zwei Komponenten zu einem vollständigen Energieberatungs-Projektpaket:

1. **`gebaeude.ifc`** – Geometrie und Baustruktur im Standard-IFC4-Format
2. **`gebaeude.din18599.json`** – DIN 18599-Datenpunkte, Varianten, Timeline und SLA-Parameter als JSON-Sidecar

Der entscheidende Vorteil gegenüber reinen IFC Property Sets: Der Sidecar kann **Zeitdimensionen, Szenarien und Varianten** abbilden – Dinge, die IFC strukturell nicht unterstützt.

## Dateistruktur

```
projekt_musterstrasse1/
├── gebaeude.ifc                  ← Geometrie (IFC4, Standard)
├── gebaeude.din18599.json        ← DIN 18599 Sidecar
├── gebaeude.ifc.pset             ← Optional: minimale Psets für BIM-Workflows
└── assets/
    ├── fotos/
    └── dokumente/
```

Beide Dateien sind über **IFC GUIDs** verknüpft – jedes IFC-Objekt hat eine unveränderliche GUID, auf die der Sidecar referenziert.

## Features

- **Portabilität**: Ein Projekt = zwei offene Dateien, lesbar in jedem Texteditor
- **Kollaboration**: Berater, Architekt und Planer teilen dieselbe Datenbasis
- **Zukunftssicherheit**: IFC5 wird rückwärtskompatibel sein; JSON-Sidecar ist versionsunabhängig
- **Automatisierung**: Direkte API-Anbindung an ERPNext (SLA-Kalkulation), BAFA-Portale, Förderdatenbanken
- **Versionierung**: Vollständig git-kompatibel – Projekthistorie ohne zusätzliche Werkzeuge

## JSON Schema

Das Schema für `gebaeude.din18599.json` befindet sich in diesem Repository unter `gebaeude.din18599.schema.json`.

## Lizenz

MIT
