import { useEffect, useState } from 'react'
import { useViewerStore } from '../../store/viewer.store'
import { BuildingDataHeader } from './BuildingDataHeader'
import { BuildingDataTabs } from './BuildingDataTabs'
import { OverviewTab } from './tabs/OverviewTab'
import { ZonesTab } from './tabs/ZonesTab'
import { EnvelopeTab } from './tabs/EnvelopeTab'
import { OpeningsTab } from './tabs/OpeningsTab'
import { SystemsTab } from './tabs/SystemsTab'
import { BuildingElementsTab } from './tabs/BuildingElementsTab'
import './BuildingDataModal.css'

export type TabId = 'overview' | 'zones' | 'envelope' | 'openings' | 'systems' | 'building-elements'

export function BuildingDataModal() {
  const isOpen = useViewerStore((state) => state.buildingDataModalOpen)
  const closeModal = useViewerStore((state) => state.closeBuildingDataModal)
  const project = useViewerStore((state) => state.project)
  
  const [activeTab, setActiveTab] = useState<TabId>('overview')

  // ESC-Key Handler
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        closeModal()
      }
    }
    
    window.addEventListener('keydown', handleEsc)
    return () => window.removeEventListener('keydown', handleEsc)
  }, [isOpen, closeModal])

  // Reset Tab beim Öffnen
  useEffect(() => {
    if (isOpen) {
      setActiveTab('overview')
    }
  }, [isOpen])

  if (!isOpen || !project) return null

  return (
    <div className="building-data-modal-backdrop" onClick={closeModal}>
      <div 
        className="building-data-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <BuildingDataHeader />
        
        <BuildingDataTabs 
          activeTab={activeTab}
          onTabChange={setActiveTab}
        />
        
        <div className="building-data-modal-content">
          {activeTab === 'overview' && <OverviewTab />}
          {activeTab === 'zones' && <ZonesTab />}
          {activeTab === 'envelope' && <EnvelopeTab />}
          {activeTab === 'openings' && <OpeningsTab />}
          {activeTab === 'systems' && <SystemsTab />}
          {activeTab === 'building-elements' && <BuildingElementsTab />}
        </div>
      </div>
    </div>
  )
}
