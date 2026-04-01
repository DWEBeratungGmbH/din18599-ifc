import { useViewerStore } from '../../store/viewer.store'

export function BuildingDataHeader() {
  const project = useViewerStore((state) => state.project)
  const closeModal = useViewerStore((state) => state.closeBuildingDataModal)

  if (!project) return null

  const zonesCount = project.input.zones?.length || 0
  const wallsCount = (project.input.envelope?.walls_external?.length || 0) + 
                     (project.input.envelope?.walls_internal?.length || 0)
  const roofsCount = project.input.envelope?.roofs?.length || 0
  const floorsCount = project.input.envelope?.floors?.length || 0
  const openingsCount = project.input.envelope?.openings?.length || 0
  const totalElements = wallsCount + roofsCount + floorsCount + openingsCount

  return (
    <div className="building-data-header">
      <div className="building-data-header-left">
        <div className="building-icon">🏢</div>
        <div className="building-data-header-title">
          <h2>Gebäudedaten – {project.meta.project_name}</h2>
          <div className="building-data-header-meta">
            LOD 300 · IFC verknüpft · {zonesCount} Zonen · {totalElements} Bauteile · 
            Stand {new Date().toLocaleDateString('de-DE')}
          </div>
        </div>
      </div>
      
      <div className="building-data-header-actions">
        <button 
          className="header-button"
          onClick={() => {
            navigator.clipboard.writeText(JSON.stringify(project, null, 2))
            alert('JSON in Zwischenablage kopiert!')
          }}
        >
          JSON
        </button>
        <button className="header-button">Export</button>
        <button className="header-button-close" onClick={closeModal}>✕</button>
      </div>
    </div>
  )
}
