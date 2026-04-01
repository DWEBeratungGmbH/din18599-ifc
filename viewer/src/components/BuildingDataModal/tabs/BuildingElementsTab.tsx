import { useViewerStore } from '../../../store/viewer.store'
import { StatusBadge } from '../shared/StatusBadge'

export function BuildingElementsTab() {
  const project = useViewerStore((state) => state.project)

  if (!project?.input.building_elements || project.input.building_elements.length === 0) {
    return (
      <div style={{ 
        textAlign: 'center', 
        padding: '60px 40px', 
        color: '#64748b',
        background: '#f8fafc',
        borderRadius: '8px',
        border: '1px dashed #cbd5e1'
      }}>
        <div style={{ fontSize: '64px', marginBottom: '16px' }}>🏗️</div>
        <div style={{ fontSize: '18px', fontWeight: 600, marginBottom: '8px' }}>LOD 200 - Keine BuildingElements</div>
        <div style={{ fontSize: '14px', lineHeight: '1.6', maxWidth: '500px', margin: '0 auto' }}>
          BuildingElements werden ab LOD 300 verwendet, um fehlende oder fehlerhafte Geometrien zu korrigieren 
          (z.B. Treppen, Durchbrüche, manuelle Anpassungen).
        </div>
      </div>
    )
  }

  const elements = project.input.building_elements

  const getElementTypeLabel = (type: string) => {
    const map: Record<string, string> = {
      'STAIR': 'Treppe',
      'OPENING': 'Durchbruch',
      'CORRECTION': 'Korrektur',
      'MANUAL': 'Manuell'
    }
    return map[type] || type
  }

  const getElementIcon = (type: string) => {
    const map: Record<string, string> = {
      'STAIR': '🪜',
      'OPENING': '⬜',
      'CORRECTION': '✏️',
      'MANUAL': '✋'
    }
    return map[type] || '🏗️'
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Info Banner */}
      <div style={{
        background: '#eff6ff',
        border: '1px solid #bfdbfe',
        borderRadius: '8px',
        padding: '16px',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px'
      }}>
        <span style={{ fontSize: '24px' }}>ℹ️</span>
        <div>
          <div style={{ fontSize: '14px', fontWeight: 600, color: '#1e40af', marginBottom: '4px' }}>
            LOD 300 - Correction Layer
          </div>
          <div style={{ fontSize: '13px', color: '#1e40af', lineHeight: '1.5' }}>
            Diese Elemente korrigieren Flächen und Volumen, ohne die Original-IFC-Geometrie zu verändern. 
            Sie werden für präzise Berechnungen (iSFP, KfW-Sanierung) benötigt.
          </div>
        </div>
      </div>

      {/* Elements List */}
      {elements.map((element) => (
        <div 
          key={element.id}
          style={{
            background: '#f8fafc',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            padding: '20px',
            transition: 'all 0.2s'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = '#cbd5e1'
            e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.05)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = '#e5e7eb'
            e.currentTarget.style.boxShadow = 'none'
          }}
        >
          {/* Header */}
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <span style={{ fontSize: '32px' }}>{getElementIcon(element.type)}</span>
              <div>
                <h4 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>{element.name || element.id}</h4>
                <div style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
                  {getElementTypeLabel(element.type)}
                </div>
              </div>
            </div>
            <StatusBadge status="neutral" label={element.source || 'CORRECTION'} />
          </div>

          {/* Geometry */}
          {element.geometry?.dimensions && (
            <div style={{
              background: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              padding: '12px',
              marginBottom: '12px'
            }}>
              <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748b', marginBottom: '8px', textTransform: 'uppercase' }}>
                Geometrie
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(100px, 1fr))', gap: '12px' }}>
                {element.geometry.dimensions.area && (
                  <div>
                    <div style={{ fontSize: '11px', color: '#94a3b8' }}>Fläche</div>
                    <div style={{ fontSize: '14px', fontWeight: 600, fontFamily: 'monospace' }}>
                      {element.geometry.dimensions.area.toFixed(1)} m²
                    </div>
                  </div>
                )}
                {element.geometry.dimensions.volume && (
                  <div>
                    <div style={{ fontSize: '11px', color: '#94a3b8' }}>Volumen</div>
                    <div style={{ fontSize: '14px', fontWeight: 600, fontFamily: 'monospace' }}>
                      {element.geometry.dimensions.volume.toFixed(1)} m³
                    </div>
                  </div>
                )}
                {element.geometry.dimensions.width && (
                  <div>
                    <div style={{ fontSize: '11px', color: '#94a3b8' }}>Breite</div>
                    <div style={{ fontSize: '14px', fontWeight: 600, fontFamily: 'monospace' }}>
                      {element.geometry.dimensions.width.toFixed(2)} m
                    </div>
                  </div>
                )}
                {element.geometry.dimensions.height && (
                  <div>
                    <div style={{ fontSize: '11px', color: '#94a3b8' }}>Höhe</div>
                    <div style={{ fontSize: '14px', fontWeight: 600, fontFamily: 'monospace' }}>
                      {element.geometry.dimensions.height.toFixed(2)} m
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Affects Zones */}
          {element.affects_zones && element.affects_zones.length > 0 && (
            <div style={{
              background: '#fef3c7',
              border: '1px solid #fde047',
              borderRadius: '6px',
              padding: '12px',
              marginBottom: '12px'
            }}>
              <div style={{ fontSize: '12px', fontWeight: 600, color: '#854d0e', marginBottom: '8px' }}>
                ⚠️ Betroffene Zonen ({element.affects_zones.length})
              </div>
              {element.affects_zones.map((zone, idx) => (
                <div key={idx} style={{ fontSize: '13px', color: '#854d0e', marginBottom: '4px' }}>
                  <span style={{ fontFamily: 'monospace', fontWeight: 600 }}>{zone.zone_id}</span>
                  {zone.area_delta && (
                    <span style={{ marginLeft: '8px' }}>
                      A: {zone.area_delta > 0 ? '+' : ''}{zone.area_delta.toFixed(1)} m²
                    </span>
                  )}
                  {zone.volume_delta && (
                    <span style={{ marginLeft: '8px' }}>
                      V: {zone.volume_delta > 0 ? '+' : ''}{zone.volume_delta.toFixed(1)} m³
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Affects Elements */}
          {element.affects_elements && element.affects_elements.length > 0 && (
            <div style={{
              background: '#fef3c7',
              border: '1px solid #fde047',
              borderRadius: '6px',
              padding: '12px',
              marginBottom: '12px'
            }}>
              <div style={{ fontSize: '12px', fontWeight: 600, color: '#854d0e', marginBottom: '8px' }}>
                ⚠️ Betroffene Bauteile ({element.affects_elements.length})
              </div>
              {element.affects_elements.map((elem, idx) => (
                <div key={idx} style={{ fontSize: '13px', color: '#854d0e', marginBottom: '4px' }}>
                  <span style={{ fontFamily: 'monospace', fontWeight: 600 }}>{elem.element_id}</span>
                  {elem.area_delta && (
                    <span style={{ marginLeft: '8px' }}>
                      A: {elem.area_delta > 0 ? '+' : ''}{elem.area_delta.toFixed(1)} m²
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Description */}
          {element.description && (
            <div style={{
              background: 'white',
              border: '1px solid #e5e7eb',
              borderRadius: '6px',
              padding: '12px',
              marginBottom: '12px'
            }}>
              <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748b', marginBottom: '6px' }}>
                Beschreibung
              </div>
              <div style={{ fontSize: '13px', color: '#475569', lineHeight: '1.5' }}>
                {element.description}
              </div>
            </div>
          )}

          {/* Reason */}
          {element.reason && (
            <div style={{
              background: '#f1f5f9',
              borderLeft: '3px solid #64748b',
              padding: '10px 12px',
              fontSize: '12px',
              color: '#475569',
              fontStyle: 'italic',
              lineHeight: '1.5'
            }}>
              <strong>Grund:</strong> {element.reason}
            </div>
          )}

          {/* ID Footer */}
          <div style={{ 
            marginTop: '12px', 
            paddingTop: '12px', 
            borderTop: '1px solid #e5e7eb',
            fontSize: '11px',
            color: '#94a3b8',
            fontFamily: 'monospace'
          }}>
            ID: {element.id}
          </div>
        </div>
      ))}
    </div>
  )
}
