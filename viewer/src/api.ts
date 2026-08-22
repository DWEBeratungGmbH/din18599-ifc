/**
 * api.ts — Zentrale API-Konfiguration fuer den DIN 18599 Viewer.
 *
 * Vorher standen die Backend-URLs (Port 8000 vs 8001) und Endpunktpfade
 * verstreut in UploadWizard.tsx, FileUpload.tsx und App.tsx — teils mit
 * konkurrierenden Legacy-Pfaden (`/process` existiert im Backend gar nicht).
 *
 * Diese Datei ist die einzige Quelle der Wahrheit fuer API_BASE_URL. In der
 * Entwicklung wird Vite die Requests via Proxy an das Backend weiterleiten
 * (siehe vite.config.ts), sodass der Frontend-Code produktionsfaehig ohne
 * hardcodierte localhost-Ports bleibt. Wer das Backend an einem anderen Ort
 * betreibt, setzt VITE_API_BASE_URL.
 *
 * Produktpfad (Plan Phase 1.3): v4 IFC-only ist primaer. Der Legacy
 * IFC+EVEBI-Flow bleibt erreichbar, ist aber deprecated und wird separat
 * dokumentiert — nicht mehr im UI prominent platziert.
 */

/**
 * Basis-URL des Backends. Prioritaet:
 *   1. VITE_API_BASE_URL (Umgebungsvariable, z.B. https://api.dwe.local)
 *   2. '' (leer) — Requests laufen ueber den Vite-Proxy (vite.config.ts),
 *      der /api/* an das Backend weiterleitet. In Produktion uebernimmt der
 *      Reverse-Proxy dieselbe Rolle.
 *
 * Bewusst KEIN localhost:8001/8000 als Default: diese Ports sind
 * Deployment-Artefakte, die nicht im Frontend-Code verstreut sein sollen.
 */
export const API_BASE_URL: string =
  (import.meta as any).env?.VITE_API_BASE_URL ?? ''

/** Endpunktpfade, zentral verwaltet gegen Contract-Drift zum Backend. */
export const ENDPOINTS = {
  // v4 IFC-only — PRIMAERER Produktpfad (Plan Phase 1.3).
  parseIfcV4: '/parse-ifc-v4',
  // Legacy IFC-Vorschau (nur Geometriezaehler, ohne Sidecar-Erzeugung).
  parseIfc: '/parse-ifc',
  // Legacy EVEBI-Adapter-Import (deprecated, separater Pfad).
  parseEvebi: '/parse-evebi',
  // Legacy IFC+EVEBI-Sidecar-Generierung (deprecated).
  generateSidecar: '/generate-sidecar',
  // QNG/Externer Import (Phase 3.9 Welle 3).
  qngParse: '/qng/parse',
  // Schema-Validierung gegen versioniertes Sidecar-Schema.
  validate: '/validate',
  // Gesundheitsstatus / Vertrag gegenueber DWEapp.
  health: '/health',
} as const

/** Baut eine absolute URL aus Base und Endpunkt. */
export function apiUrl(endpoint: string): string {
  return `${API_BASE_URL}${endpoint}`
}
