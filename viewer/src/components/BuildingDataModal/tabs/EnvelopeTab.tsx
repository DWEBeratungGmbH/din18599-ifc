import { useState } from 'react'
import { useViewerStore } from '../../../store/viewer.store'
import { UValueIndicator } from '../shared/UValueIndicator'
import { StatusBadge } from '../shared/StatusBadge'

export function EnvelopeTab() {
  const project = useViewerStore((state) => state.project)
  const [expandedElements, setExpandedElements] = useState<Set<string>>(new Set())

  if (!project?.input.envelope) return <div className="tab-content">Keine Gebäudehülle vorhanden</div>

  const envelope = project.input.envelope
  const walls = envelope.walls_external || []
  const roofs = envelope.roofs || []
  const floors = envelope.floors || []
  const openings = envelope.openings || []

  const toggleExpand = (id: string) => {
    setExpandedElements(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  const getOpeningsForElement = (elementId: string) => {
    return openings.filter(o => o.parent_element_id === elementId)
  }

  const getOrientationName = (deg: number) => {
    const directions = ['Nord', 'Ost', 'Süd', 'West']
    return directions[Math.round(deg / 90) % 4]
  }

  const getBoundaryBadge = (bc: string) => {
    const map: Record<string, { status: 'good' | 'medium' | 'bad' | 'neutral', label: string }> = {
      'EXTERNAL': { status: 'good', label: 'AUSSEN' },
      'GROUND': { status: 'medium', label: 'ERDREICH' },
      'UNHEATED': { status: 'neutral', label: 'UNBEHEIZT' }
    }
    return map[bc] || { status: 'neutral', label: bc }
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {/* Außenwände */}
      {walls.length > 0 && (
        <div>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: 600 }}>
            🧱 Außenwände ({walls.length})
          </h3>
          <div style={{ 
            border: '1px solid #e5e7eb', 
            borderRadius: '8px',
            overflow: 'hidden'
          }}>
            <table style={{ 
              width: '100%', 
              borderCollapse: 'collapse',
              fontSize: '14px'
            }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e5e7eb' }}>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>Name</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>Orient.</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>Fläche</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>U-Wert</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>ΔU</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>U-eff</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>α</th>
                  <th style={{ padding: '12px', textAlign: 'center', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>Typ</th>
                </tr>
              </thead>
              <tbody>
                {walls.map((wall, idx) => {
                  const uEff = wall.u_value_undisturbed + (wall.thermal_bridge_delta_u || 0)
                  const wallOpenings = getOpeningsForElement(wall.id)
                  const isExpanded = expandedElements.has(wall.id)
                  const hasOpenings = wallOpenings.length > 0
                  
                  return (
                    <>
                      <tr 
                        key={wall.id}
                        style={{ 
                          borderBottom: !isExpanded && idx < walls.length - 1 ? '1px solid #e5e7eb' : 'none',
                          cursor: hasOpenings ? 'pointer' : 'default',
                          background: 'white'
                        }}
                        onClick={() => hasOpenings && toggleExpand(wall.id)}
                        onMouseEnter={(e) => e.currentTarget.style.background = '#f8fafc'}
                        onMouseLeave={(e) => e.currentTarget.style.background = 'white'}
                      >
                        <td style={{ padding: '12px', fontWeight: 500 }}>
                          {hasOpenings && (
                            <span style={{ marginRight: '8px', fontSize: '12px', color: '#64748b' }}>
                              {isExpanded ? '▼' : '▶'}
                            </span>
                          )}
                          {wall.name || wall.id}
                          {hasOpenings && (
                            <span style={{ 
                              marginLeft: '8px', 
                              fontSize: '11px', 
                              color: '#64748b',
                              background: '#f1f5f9',
                              padding: '2px 6px',
                              borderRadius: '4px'
                            }}>
                              {wallOpenings.length} 🪟
                            </span>
                          )}
                        </td>
                        <td style={{ padding: '12px' }}>
                          <span style={{ fontSize: '16px', marginRight: '4px' }}>
                            {wall.orientation === 0 ? '⬆️' : wall.orientation === 90 ? '➡️' : wall.orientation === 180 ? '⬇️' : '⬅️'}
                          </span>
                          {getOrientationName(wall.orientation)} ({wall.orientation}°)
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace' }}>
                          {wall.area.toFixed(1)} m²
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace' }}>
                          {wall.u_value_undisturbed.toFixed(2)}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace', color: '#64748b' }}>
                          +{(wall.thermal_bridge_delta_u || 0).toFixed(2)}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right' }}>
                          <UValueIndicator uValue={uEff} elementType="wall" />
                        </td>
                        <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace' }}>
                          {wall.solar_absorption?.toFixed(2) || '-'}
                        </td>
                        <td style={{ padding: '12px', textAlign: 'center' }}>
                          <span style={{
                            padding: '2px 8px',
                            borderRadius: '4px',
                            background: wall.thermal_bridge_type === 'REDUCED' ? '#dcfce7' : '#f1f5f9',
                            color: wall.thermal_bridge_type === 'REDUCED' ? '#166534' : '#475569',
                            fontSize: '11px',
                            fontWeight: 600
                          }}>
                            {wall.thermal_bridge_type || 'DEFAULT'}
                          </span>
                        </td>
                      </tr>
                      
                      {/* Öffnungen (expandiert) */}
                      {isExpanded && wallOpenings.map((opening, openingIdx) => {
                        const uWindow = opening.u_value_glass || 0
                        return (
                          <tr 
                            key={opening.id}
                            style={{ 
                              background: '#fafbfc',
                              borderBottom: openingIdx === wallOpenings.length - 1 && idx < walls.length - 1 ? '1px solid #e5e7eb' : 'none'
                            }}
                          >
                            <td style={{ padding: '12px 12px 12px 40px', fontSize: '13px', color: '#475569' }}>
                              <span style={{ marginRight: '6px' }}>└─</span>
                              🪟 {opening.name || opening.id}
                            </td>
                            <td style={{ padding: '12px', fontSize: '13px', color: '#64748b' }}>
                              {opening.type === 'WINDOW' ? 'Fenster' : opening.type === 'DOOR' ? 'Tür' : opening.type}
                            </td>
                            <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace', fontSize: '13px' }}>
                              {opening.area.toFixed(1)} m²
                            </td>
                            <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace', fontSize: '13px' }}>
                              Ug: {opening.u_value_glass?.toFixed(2) || '-'}
                            </td>
                            <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace', fontSize: '13px' }}>
                              Uf: {opening.u_value_frame?.toFixed(2) || '-'}
                            </td>
                            <td style={{ padding: '12px', textAlign: 'right' }}>
                              <UValueIndicator uValue={uWindow} elementType="window" />
                            </td>
                            <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace', fontSize: '13px' }}>
                              g: {opening.g_value?.toFixed(2) || '-'}
                            </td>
                            <td style={{ padding: '12px', textAlign: 'center', fontSize: '13px', color: '#64748b' }}>
                              Ψ: {opening.psi_spacer?.toFixed(2) || '-'}
                            </td>
                          </tr>
                        )
                      })}
                    </>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Dächer */}
      {roofs.length > 0 && (
        <div>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: 600 }}>
            🏠 Dächer ({roofs.length})
          </h3>
          <div style={{ 
            border: '1px solid #e5e7eb', 
            borderRadius: '8px',
            overflow: 'hidden'
          }}>
            <table style={{ 
              width: '100%', 
              borderCollapse: 'collapse',
              fontSize: '14px'
            }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e5e7eb' }}>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>Name</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>Neigung</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>Fläche</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>U-Wert</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>ΔU</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>U-eff</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>α</th>
                  <th style={{ padding: '12px', textAlign: 'center', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>Typ</th>
                </tr>
              </thead>
              <tbody>
                {roofs.map((roof, idx) => {
                  const uEff = roof.u_value_undisturbed + (roof.thermal_bridge_delta_u || 0)
                  return (
                    <tr 
                      key={roof.id}
                      style={{ 
                        borderBottom: idx < roofs.length - 1 ? '1px solid #e5e7eb' : 'none',
                        cursor: 'pointer'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = '#f8fafc'}
                      onMouseLeave={(e) => e.currentTarget.style.background = 'white'}
                    >
                      <td style={{ padding: '12px', fontWeight: 500 }}>{roof.name || roof.id}</td>
                      <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace' }}>
                        {roof.inclination}°
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace' }}>
                        {roof.area.toFixed(1)} m²
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace' }}>
                        {roof.u_value_undisturbed.toFixed(2)}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace', color: '#64748b' }}>
                        +{(roof.thermal_bridge_delta_u || 0).toFixed(2)}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right' }}>
                        <UValueIndicator uValue={uEff} elementType="roof" />
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace' }}>
                        {roof.solar_absorption?.toFixed(2) || '-'}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'center' }}>
                        <span style={{
                          padding: '2px 8px',
                          borderRadius: '4px',
                          background: roof.thermal_bridge_type === 'REDUCED' ? '#dcfce7' : '#f1f5f9',
                          color: roof.thermal_bridge_type === 'REDUCED' ? '#166534' : '#475569',
                          fontSize: '11px',
                          fontWeight: 600
                        }}>
                          {roof.thermal_bridge_type || 'DEFAULT'}
                        </span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Böden */}
      {floors.length > 0 && (
        <div>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: 600 }}>
            ⬇️ Böden / Decken ({floors.length})
          </h3>
          <div style={{ 
            border: '1px solid #e5e7eb', 
            borderRadius: '8px',
            overflow: 'hidden'
          }}>
            <table style={{ 
              width: '100%', 
              borderCollapse: 'collapse',
              fontSize: '14px'
            }}>
              <thead>
                <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e5e7eb' }}>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>Name</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>Randbedingung</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>Fläche</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>U-Wert</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>ΔU</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>U-eff</th>
                  <th style={{ padding: '12px', textAlign: 'right', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>B'</th>
                </tr>
              </thead>
              <tbody>
                {floors.map((floor, idx) => {
                  const uEff = floor.u_value_undisturbed + (floor.thermal_bridge_delta_u || 0)
                  const boundary = getBoundaryBadge(floor.boundary_condition)
                  return (
                    <tr 
                      key={floor.id}
                      style={{ 
                        borderBottom: idx < floors.length - 1 ? '1px solid #e5e7eb' : 'none',
                        cursor: 'pointer'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = '#f8fafc'}
                      onMouseLeave={(e) => e.currentTarget.style.background = 'white'}
                    >
                      <td style={{ padding: '12px', fontWeight: 500 }}>{floor.name || floor.id}</td>
                      <td style={{ padding: '12px' }}>
                        <StatusBadge status={boundary.status} label={boundary.label} />
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace' }}>
                        {floor.area.toFixed(1)} m²
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace' }}>
                        {floor.u_value_undisturbed.toFixed(2)}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace', color: '#64748b' }}>
                        +{(floor.thermal_bridge_delta_u || 0).toFixed(2)}
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right' }}>
                        <UValueIndicator uValue={uEff} elementType="floor" />
                      </td>
                      <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace' }}>
                        {floor.characteristic_dimension_b?.toFixed(2) || '-'} m
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
