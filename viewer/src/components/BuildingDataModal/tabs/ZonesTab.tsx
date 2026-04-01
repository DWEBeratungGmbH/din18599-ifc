import { useViewerStore } from '../../../store/viewer.store'
import { StatusBadge } from '../shared/StatusBadge'

export function ZonesTab() {
  const project = useViewerStore((state) => state.project)

  if (!project?.input.zones) return <div className="tab-content">Keine Zonen vorhanden</div>

  const zones = project.input.zones

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>
        Thermische Zonen ({zones.length})
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
              <th style={{ padding: '12px', textAlign: 'left', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>Nutzung</th>
              <th style={{ padding: '12px', textAlign: 'right', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>A<sub>N</sub></th>
              <th style={{ padding: '12px', textAlign: 'right', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>V</th>
              <th style={{ padding: '12px', textAlign: 'right', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>θ Heizen</th>
              <th style={{ padding: '12px', textAlign: 'right', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>θ Kühlen</th>
              <th style={{ padding: '12px', textAlign: 'center', fontWeight: 600, fontSize: '12px', color: '#64748b', textTransform: 'uppercase' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {zones.map((zone, idx) => (
              <tr 
                key={zone.id}
                style={{ 
                  borderBottom: idx < zones.length - 1 ? '1px solid #e5e7eb' : 'none',
                  cursor: 'pointer',
                  transition: 'background 0.2s'
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = '#f8fafc'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'white'}
              >
                <td style={{ padding: '12px', fontWeight: 500 }}>{zone.name || zone.id}</td>
                <td style={{ padding: '12px' }}>
                  {zone.usage_profile && (
                    <span style={{
                      padding: '2px 8px',
                      borderRadius: '4px',
                      background: '#eff6ff',
                      color: '#1e40af',
                      fontSize: '12px',
                      fontWeight: 500
                    }}>
                      {zone.usage_profile}
                    </span>
                  )}
                </td>
                <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace' }}>
                  {zone.area_an?.toFixed(1)} m²
                </td>
                <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace' }}>
                  {zone.volume?.toFixed(1)} m³
                </td>
                <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace' }}>
                  {zone.set_temp_heating || '-'} °C
                </td>
                <td style={{ padding: '12px', textAlign: 'right', fontFamily: 'monospace' }}>
                  {zone.set_temp_cooling || '-'} °C
                </td>
                <td style={{ padding: '12px', textAlign: 'center' }}>
                  <StatusBadge 
                    status={zone.is_heated ? 'good' : 'neutral'} 
                    label={zone.is_heated ? 'BEHEIZT' : 'UNBEHEIZT'}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Zusammenfassung */}
      <div style={{
        background: '#f8fafc',
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
        padding: '16px',
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '16px'
      }}>
        <div>
          <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Gesamt-Nutzfläche</div>
          <div style={{ fontSize: '20px', fontWeight: 600 }}>
            {zones.reduce((sum, z) => sum + (z.area_an || 0), 0).toFixed(1)} m²
          </div>
        </div>
        <div>
          <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Gesamt-Volumen</div>
          <div style={{ fontSize: '20px', fontWeight: 600 }}>
            {zones.reduce((sum, z) => sum + (z.volume || 0), 0).toFixed(1)} m³
          </div>
        </div>
        <div>
          <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Beheizte Zonen</div>
          <div style={{ fontSize: '20px', fontWeight: 600 }}>
            {zones.filter(z => z.is_heated).length} / {zones.length}
          </div>
        </div>
      </div>
    </div>
  )
}
