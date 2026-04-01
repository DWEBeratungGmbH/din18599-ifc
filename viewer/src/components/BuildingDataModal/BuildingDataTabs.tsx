import type { TabId } from './BuildingDataModal'
import { useViewerStore } from '../../store/viewer.store'

interface Tab {
  id: TabId
  label: string
  icon: string
  count?: number
}

interface BuildingDataTabsProps {
  activeTab: TabId
  onTabChange: (tab: TabId) => void
}

export function BuildingDataTabs({ activeTab, onTabChange }: BuildingDataTabsProps) {
  const project = useViewerStore((state) => state.project)

  if (!project) return null

  const tabs: Tab[] = [
    { id: 'overview', label: 'Übersicht', icon: '📊' },
    { id: 'zones', label: 'Zonen', icon: '🏠', count: project.input.zones?.length },
    { id: 'envelope', label: 'Gebäudehülle', icon: '🧱', count: 
      (project.input.envelope?.walls_external?.length || 0) + 
      (project.input.envelope?.roofs?.length || 0) + 
      (project.input.envelope?.floors?.length || 0)
    },
    { id: 'openings', label: 'Öffnungen', icon: '🪟', count: project.input.envelope?.openings?.length },
    { id: 'systems', label: 'Anlagentechnik', icon: '🔧' },
    { id: 'building-elements', label: 'BuildingElements', icon: '🏗️', count: project.input.building_elements?.length }
  ]

  return (
    <div className="building-data-tabs">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          className={`building-data-tab ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => onTabChange(tab.id)}
        >
          <span className="tab-icon">{tab.icon}</span>
          <span className="tab-label">{tab.label}</span>
          {tab.count !== undefined && tab.count > 0 && (
            <span className="tab-badge">{tab.count}</span>
          )}
        </button>
      ))}
    </div>
  )
}
