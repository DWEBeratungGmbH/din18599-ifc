/**
 * DIN 18599 Sidecar - Export Parser
 * Konvertiert PostgreSQL JSONB → JSON
 */

import { Pool } from 'pg'
import type { DIN18599Data } from '../../viewer/src/types/din18599'

export interface ExportOptions {
  includeMetadata?: boolean
  pretty?: boolean
}

export interface ExportResult {
  success: boolean
  data?: DIN18599Data
  metadata?: {
    sidecarId: string
    projectId: string
    version: number
    versionName: string
    schemaVersion: string
    createdAt: Date
    dataHash: string
  }
  error?: string
}

/**
 * Exportiert ein Sidecar aus der Datenbank als JSON
 */
export async function exportSidecar(
  pool: Pool,
  sidecarId: string,
  options: ExportOptions = {}
): Promise<ExportResult> {
  try {
    const result = await pool.query(
      `SELECT 
        id,
        project_id,
        version,
        version_name,
        schema_version,
        data,
        data_hash,
        created_at
       FROM din18599.sidecars
       WHERE id = $1 AND deleted_at IS NULL`,
      [sidecarId]
    )
    
    if (result.rows.length === 0) {
      return {
        success: false,
        error: `Sidecar ${sidecarId} not found`
      }
    }
    
    const row = result.rows[0]
    
    const exportResult: ExportResult = {
      success: true,
      data: row.data as DIN18599Data
    }
    
    if (options.includeMetadata) {
      exportResult.metadata = {
        sidecarId: row.id,
        projectId: row.project_id,
        version: row.version,
        versionName: row.version_name,
        schemaVersion: row.schema_version,
        createdAt: row.created_at,
        dataHash: row.data_hash
      }
    }
    
    return exportResult
    
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error)
    }
  }
}

/**
 * Exportiert das aktuelle Sidecar eines Projekts
 */
export async function exportCurrentSidecar(
  pool: Pool,
  projectId: string,
  options: ExportOptions = {}
): Promise<ExportResult> {
  try {
    const result = await pool.query(
      `SELECT 
        id,
        project_id,
        version,
        version_name,
        schema_version,
        data,
        data_hash,
        created_at
       FROM din18599.sidecars
       WHERE project_id = $1 
         AND is_current = true 
         AND deleted_at IS NULL`,
      [projectId]
    )
    
    if (result.rows.length === 0) {
      return {
        success: false,
        error: `No current sidecar found for project ${projectId}`
      }
    }
    
    const row = result.rows[0]
    
    const exportResult: ExportResult = {
      success: true,
      data: row.data as DIN18599Data
    }
    
    if (options.includeMetadata) {
      exportResult.metadata = {
        sidecarId: row.id,
        projectId: row.project_id,
        version: row.version,
        versionName: row.version_name,
        schemaVersion: row.schema_version,
        createdAt: row.created_at,
        dataHash: row.data_hash
      }
    }
    
    return exportResult
    
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error)
    }
  }
}

/**
 * Exportiert alle Versionen eines Projekts
 */
export async function exportAllVersions(
  pool: Pool,
  projectId: string
): Promise<{
  success: boolean
  versions?: Array<{
    sidecarId: string
    version: number
    versionName: string
    isCurrent: boolean
    schemaVersion: string
    createdAt: Date
    data: DIN18599Data
  }>
  error?: string
}> {
  try {
    const result = await pool.query(
      `SELECT 
        id,
        version,
        version_name,
        is_current,
        schema_version,
        data,
        created_at
       FROM din18599.sidecars
       WHERE project_id = $1 AND deleted_at IS NULL
       ORDER BY version ASC`,
      [projectId]
    )
    
    return {
      success: true,
      versions: result.rows.map(row => ({
        sidecarId: row.id,
        version: row.version,
        versionName: row.version_name,
        isCurrent: row.is_current,
        schemaVersion: row.schema_version,
        createdAt: row.created_at,
        data: row.data as DIN18599Data
      }))
    }
    
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error)
    }
  }
}

/**
 * Exportiert Sidecar als JSON-Datei (für Download)
 */
export async function exportSidecarToFile(
  pool: Pool,
  sidecarId: string,
  filePath: string
): Promise<{ success: boolean; error?: string }> {
  const fs = await import('fs/promises')
  
  try {
    const result = await exportSidecar(pool, sidecarId)
    
    if (!result.success || !result.data) {
      return {
        success: false,
        error: result.error || 'Export failed'
      }
    }
    
    // Pretty-print JSON
    const jsonString = JSON.stringify(result.data, null, 2)
    
    await fs.writeFile(filePath, jsonString, 'utf-8')
    
    return { success: true }
    
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error)
    }
  }
}
