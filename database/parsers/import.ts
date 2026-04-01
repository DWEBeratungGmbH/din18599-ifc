/**
 * DIN 18599 Sidecar - Import Parser
 * Konvertiert JSON → PostgreSQL JSONB
 */

import { Pool } from 'pg'
import crypto from 'crypto'
import type { DIN18599Data } from '../../viewer/src/types/din18599'

export interface ImportOptions {
  versionName?: string
  setCurrent?: boolean
  userId?: string
  skipValidation?: boolean
}

export interface ImportResult {
  success: boolean
  sidecarId?: string
  errors?: string[]
  warnings?: string[]
}

/**
 * Importiert ein DIN 18599 Sidecar JSON in die Datenbank
 */
export async function importSidecar(
  pool: Pool,
  projectId: string,
  jsonData: DIN18599Data,
  options: ImportOptions = {}
): Promise<ImportResult> {
  const client = await pool.connect()
  
  try {
    await client.query('BEGIN')
    
    // 1. Validierung (optional)
    if (!options.skipValidation) {
      const validationErrors = validateSidecarStructure(jsonData)
      if (validationErrors.length > 0) {
        return {
          success: false,
          errors: validationErrors
        }
      }
    }
    
    // 2. Hash berechnen
    const dataHash = crypto
      .createHash('sha256')
      .update(JSON.stringify(jsonData))
      .digest('hex')
    
    // 3. Nächste Version ermitteln
    const versionResult = await client.query(
      `SELECT COALESCE(MAX(version), 0) + 1 AS next_version
       FROM din18599.sidecars
       WHERE project_id = $1`,
      [projectId]
    )
    const nextVersion = versionResult.rows[0].next_version
    
    // 4. Sidecar einfügen
    const insertResult = await client.query(
      `INSERT INTO din18599.sidecars (
        project_id,
        version,
        version_name,
        is_current,
        lod,
        mode,
        data,
        data_hash,
        schema_version,
        created_by
      ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
      RETURNING id`,
      [
        projectId,
        nextVersion,
        options.versionName || `Version ${nextVersion}`,
        options.setCurrent ?? true,
        jsonData.meta.lod || '200',
        jsonData.meta.mode || 'STANDALONE',
        JSON.stringify(jsonData),
        dataHash,
        jsonData.meta.schema_version,
        options.userId || null
      ]
    )
    
    const sidecarId = insertResult.rows[0].id
    
    // 5. Audit Log
    await client.query(
      `INSERT INTO din18599.audit_log (
        project_id,
        sidecar_id,
        action,
        entity_type,
        changes,
        user_id
      ) VALUES ($1, $2, 'IMPORT', 'SIDECAR', $3, $4)`,
      [
        projectId,
        sidecarId,
        JSON.stringify({
          version: nextVersion,
          schema_version: jsonData.meta.schema_version,
          lod: jsonData.meta.lod,
          zones: jsonData.input.zones?.length || 0,
          building_elements: jsonData.input.building_elements?.length || 0,
          scenarios: jsonData.scenarios?.length || 0
        }),
        options.userId || null
      ]
    )
    
    await client.query('COMMIT')
    
    return {
      success: true,
      sidecarId
    }
    
  } catch (error) {
    await client.query('ROLLBACK')
    
    return {
      success: false,
      errors: [error instanceof Error ? error.message : String(error)]
    }
  } finally {
    client.release()
  }
}

/**
 * Validiert die Basis-Struktur des Sidecar JSON
 */
function validateSidecarStructure(data: DIN18599Data): string[] {
  const errors: string[] = []
  
  // Meta validieren
  if (!data.meta) {
    errors.push('Missing meta section')
    return errors
  }
  
  if (!data.meta.schema_version) {
    errors.push('Missing meta.schema_version')
  }
  
  if (!['2.0', '2.1', '2.2'].includes(data.meta.schema_version)) {
    errors.push(`Invalid schema_version: ${data.meta.schema_version}. Allowed: 2.0, 2.1, 2.2`)
  }
  
  if (!data.meta.project_name) {
    errors.push('Missing meta.project_name')
  }
  
  // Input validieren
  if (!data.input) {
    errors.push('Missing input section')
    return errors
  }
  
  if (!data.input.building) {
    errors.push('Missing input.building')
  }
  
  // Zones validieren (optional für LOD 100)
  if (data.input.zones) {
    data.input.zones.forEach((zone, idx) => {
      if (!zone.id) {
        errors.push(`input.zones[${idx}]: Missing id`)
      }
      if (!zone.area_an || zone.area_an <= 0) {
        errors.push(`input.zones[${idx}]: Invalid area_an (must be > 0)`)
      }
    })
  }
  
  // BuildingElements validieren (LOD 300+)
  if (data.input.building_elements) {
    data.input.building_elements.forEach((elem, idx) => {
      if (!elem.id) {
        errors.push(`input.building_elements[${idx}]: Missing id`)
      }
      if (!elem.type) {
        errors.push(`input.building_elements[${idx}]: Missing type`)
      }
    })
  }
  
  return errors
}

/**
 * Erstellt ein neues Projekt mit initialem Sidecar
 */
export async function createProjectWithSidecar(
  pool: Pool,
  projectData: {
    name: string
    description?: string
    ifcFilePath?: string
    ifcGuidBuilding?: string
  },
  sidecarData: DIN18599Data,
  options: ImportOptions = {}
): Promise<ImportResult> {
  const client = await pool.connect()
  
  try {
    await client.query('BEGIN')
    
    // 1. Projekt erstellen
    const projectResult = await client.query(
      `INSERT INTO din18599.projects (
        name,
        description,
        ifc_file_path,
        ifc_guid_building,
        created_by
      ) VALUES ($1, $2, $3, $4, $5)
      RETURNING id`,
      [
        projectData.name,
        projectData.description || null,
        projectData.ifcFilePath || null,
        projectData.ifcGuidBuilding || null,
        options.userId || null
      ]
    )
    
    const projectId = projectResult.rows[0].id
    
    await client.query('COMMIT')
    
    // 2. Sidecar importieren
    return await importSidecar(pool, projectId, sidecarData, {
      ...options,
      versionName: options.versionName || 'Initial Version'
    })
    
  } catch (error) {
    await client.query('ROLLBACK')
    
    return {
      success: false,
      errors: [error instanceof Error ? error.message : String(error)]
    }
  } finally {
    client.release()
  }
}
