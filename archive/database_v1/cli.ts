#!/usr/bin/env node
/**
 * DIN 18599 Sidecar - CLI Tool
 * Import/Export von JSON ↔ PostgreSQL
 */

import { Pool } from 'pg'
import { importSidecar, createProjectWithSidecar } from './parsers/import'
import { exportSidecar, exportCurrentSidecar, exportSidecarToFile } from './parsers/export'
import { readFile } from 'fs/promises'

// PostgreSQL Connection
const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: parseInt(process.env.DB_PORT || '5432'),
  database: process.env.DB_NAME || 'din18599',
  user: process.env.DB_USER || 'postgres',
  password: process.env.DB_PASSWORD,
  schema: 'din18599'
})

// CLI Commands
const commands = {
  import: importCommand,
  export: exportCommand,
  create: createCommand,
  list: listCommand,
  help: helpCommand
}

async function main() {
  const args = process.argv.slice(2)
  const command = args[0]
  
  if (!command || command === 'help' || command === '--help') {
    helpCommand()
    process.exit(0)
  }
  
  const handler = commands[command as keyof typeof commands]
  
  if (!handler) {
    console.error(`❌ Unknown command: ${command}`)
    console.error('Run "din18599 help" for usage information')
    process.exit(1)
  }
  
  try {
    await handler(args.slice(1))
    await pool.end()
    process.exit(0)
  } catch (error) {
    console.error('❌ Error:', error instanceof Error ? error.message : String(error))
    await pool.end()
    process.exit(1)
  }
}

/**
 * Import JSON file into database
 * Usage: din18599 import <project-id> <json-file> [--version-name "Name"]
 */
async function importCommand(args: string[]) {
  if (args.length < 2) {
    console.error('Usage: din18599 import <project-id> <json-file> [--version-name "Name"]')
    process.exit(1)
  }
  
  const projectId = args[0]
  const jsonFile = args[1]
  const versionNameIdx = args.indexOf('--version-name')
  const versionName = versionNameIdx >= 0 ? args[versionNameIdx + 1] : undefined
  
  console.log(`📥 Importing ${jsonFile} into project ${projectId}...`)
  
  // Read JSON file
  const jsonContent = await readFile(jsonFile, 'utf-8')
  const jsonData = JSON.parse(jsonContent)
  
  // Import
  const result = await importSidecar(pool, projectId, jsonData, {
    versionName,
    setCurrent: true
  })
  
  if (!result.success) {
    console.error('❌ Import failed:')
    result.errors?.forEach(err => console.error(`  - ${err}`))
    process.exit(1)
  }
  
  console.log(`✅ Import successful!`)
  console.log(`   Sidecar ID: ${result.sidecarId}`)
  console.log(`   Schema Version: ${jsonData.meta.schema_version}`)
  console.log(`   LOD: ${jsonData.meta.lod || 'N/A'}`)
}

/**
 * Export sidecar to JSON file
 * Usage: din18599 export <sidecar-id> <output-file>
 *        din18599 export --current <project-id> <output-file>
 */
async function exportCommand(args: string[]) {
  if (args.length < 2) {
    console.error('Usage: din18599 export <sidecar-id> <output-file>')
    console.error('       din18599 export --current <project-id> <output-file>')
    process.exit(1)
  }
  
  const isCurrent = args[0] === '--current'
  const id = isCurrent ? args[1] : args[0]
  const outputFile = isCurrent ? args[2] : args[1]
  
  console.log(`📤 Exporting to ${outputFile}...`)
  
  let result
  if (isCurrent) {
    result = await exportCurrentSidecar(pool, id)
  } else {
    result = await exportSidecar(pool, id)
  }
  
  if (!result.success || !result.data) {
    console.error(`❌ Export failed: ${result.error}`)
    process.exit(1)
  }
  
  // Write to file
  const fs = await import('fs/promises')
  await fs.writeFile(outputFile, JSON.stringify(result.data, null, 2), 'utf-8')
  
  console.log(`✅ Export successful!`)
  console.log(`   File: ${outputFile}`)
  console.log(`   Schema Version: ${result.data.meta.schema_version}`)
  console.log(`   Zones: ${result.data.input.zones?.length || 0}`)
  console.log(`   BuildingElements: ${result.data.input.building_elements?.length || 0}`)
}

/**
 * Create new project with initial sidecar
 * Usage: din18599 create <project-name> <json-file> [--description "..."]
 */
async function createCommand(args: string[]) {
  if (args.length < 2) {
    console.error('Usage: din18599 create <project-name> <json-file> [--description "..."]')
    process.exit(1)
  }
  
  const projectName = args[0]
  const jsonFile = args[1]
  const descIdx = args.indexOf('--description')
  const description = descIdx >= 0 ? args[descIdx + 1] : undefined
  
  console.log(`🆕 Creating project "${projectName}"...`)
  
  // Read JSON file
  const jsonContent = await readFile(jsonFile, 'utf-8')
  const jsonData = JSON.parse(jsonContent)
  
  // Create project + import sidecar
  const result = await createProjectWithSidecar(
    pool,
    { name: projectName, description },
    jsonData
  )
  
  if (!result.success) {
    console.error('❌ Creation failed:')
    result.errors?.forEach(err => console.error(`  - ${err}`))
    process.exit(1)
  }
  
  console.log(`✅ Project created!`)
  console.log(`   Sidecar ID: ${result.sidecarId}`)
}

/**
 * List all projects
 * Usage: din18599 list
 */
async function listCommand() {
  console.log('📋 Projects:\n')
  
  const result = await pool.query(`
    SELECT * FROM din18599.v_projects_overview
    ORDER BY project_updated_at DESC
    LIMIT 20
  `)
  
  if (result.rows.length === 0) {
    console.log('  No projects found.')
    return
  }
  
  result.rows.forEach(row => {
    console.log(`  ${row.project_name}`)
    console.log(`    ID: ${row.project_id}`)
    console.log(`    Sidecar: v${row.sidecar_version} (${row.schema_version}, LOD ${row.lod})`)
    console.log(`    Zones: ${row.zone_count}, BuildingElements: ${row.building_element_count}, Scenarios: ${row.scenario_count}`)
    console.log(`    Updated: ${new Date(row.project_updated_at).toLocaleString('de-DE')}`)
    console.log('')
  })
}

/**
 * Show help
 */
function helpCommand() {
  console.log(`
DIN 18599 Sidecar - CLI Tool
============================

USAGE:
  din18599 <command> [options]

COMMANDS:
  import <project-id> <json-file> [--version-name "Name"]
      Import a JSON file into an existing project
      
  export <sidecar-id> <output-file>
      Export a specific sidecar version to JSON file
      
  export --current <project-id> <output-file>
      Export the current sidecar of a project
      
  create <project-name> <json-file> [--description "..."]
      Create a new project with initial sidecar
      
  list
      List all projects with their current sidecars
      
  help
      Show this help message

ENVIRONMENT VARIABLES:
  DB_HOST       PostgreSQL host (default: localhost)
  DB_PORT       PostgreSQL port (default: 5432)
  DB_NAME       Database name (default: din18599)
  DB_USER       Database user (default: postgres)
  DB_PASSWORD   Database password

EXAMPLES:
  # Import demo file
  din18599 import abc-123 ./demo/efh-demo.din18599.json --version-name "Initial"
  
  # Export current sidecar
  din18599 export --current abc-123 ./output.json
  
  # Create new project
  din18599 create "EFH Musterhausen" ./demo/efh-demo.din18599.json
  
  # List all projects
  din18599 list

For more information, visit:
https://github.com/DWEBeratungGmbH/din18599-ifc
`)
}

// Run CLI
if (require.main === module) {
  main()
}

export { pool, commands }
