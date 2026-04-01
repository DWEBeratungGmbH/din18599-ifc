import { useViewerStore } from '../../../store/viewer.store'
import { StatusBadge } from '../shared/StatusBadge'

export function SystemsTab() {
  const project = useViewerStore((state) => state.project)

  if (!project?.input.systems) return <div className="tab-content">Keine Anlagentechnik vorhanden</div>

  const systems = project.input.systems

  // Systems ist ein Objekt mit heating, cooling, ventilation, dhw, etc.
  const heating = systems.heating || []
  const ventilation = systems.ventilation || []
  const dhw = systems.dhw || []
  const cooling = systems.cooling || []

  const getSystemTypeLabel = (type: string) => {
    const map: Record<string, string> = {
      'gas_boiler': 'Gaskessel',
      'oil_boiler': 'Ölkessel',
      'heat_pump': 'Wärmepumpe',
      'district_heating': 'Fernwärme',
      'ventilation': 'Lüftungsanlage',
      'heat_recovery': 'Wärmerückgewinnung',
      'dhw_storage': 'Warmwasserspeicher',
      'dhw_circulation': 'Zirkulation',
      'cooling': 'Kühlung',
      'chiller': 'Kältemaschine'
    }
    return map[type] || type
  }

  const getSystemIcon = (type: string) => {
    if (['gas_boiler', 'oil_boiler', 'heat_pump', 'district_heating'].includes(type)) return '🔥'
    if (['ventilation', 'heat_recovery'].includes(type)) return '💨'
    if (['dhw_storage', 'dhw_circulation'].includes(type)) return '💧'
    if (['cooling', 'chiller'].includes(type)) return '❄️'
    return '🔧'
  }

  const SystemCard = ({ system }: { system: any }) => (
    <div style={{
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
          <span style={{ fontSize: '32px' }}>{getSystemIcon(system.type)}</span>
          <div>
            <h4 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>{system.name || system.id}</h4>
            <div style={{ fontSize: '13px', color: '#64748b', marginTop: '4px' }}>
              {getSystemTypeLabel(system.type)}
            </div>
          </div>
        </div>
        {system.year_built && (
          <StatusBadge 
            status={new Date().getFullYear() - system.year_built > 20 ? 'bad' : new Date().getFullYear() - system.year_built > 10 ? 'medium' : 'good'} 
            label={`BJ ${system.year_built}`}
          />
        )}
      </div>

      {/* Details Grid */}
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
        gap: '12px',
        marginTop: '16px',
        paddingTop: '16px',
        borderTop: '1px solid #e5e7eb'
      }}>
        {system.nominal_power && (
          <div>
            <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '4px', textTransform: 'uppercase' }}>Nennleistung</div>
            <div style={{ fontSize: '16px', fontWeight: 600 }}>{system.nominal_power.toFixed(1)} kW</div>
          </div>
        )}
        {system.efficiency_nominal && (
          <div>
            <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '4px', textTransform: 'uppercase' }}>Wirkungsgrad</div>
            <div style={{ fontSize: '16px', fontWeight: 600 }}>
              {(system.efficiency_nominal * 100).toFixed(0)}%
              {system.efficiency_nominal < 0.8 && <span style={{ marginLeft: '6px', fontSize: '14px' }}>⚠️</span>}
            </div>
          </div>
        )}
        {system.cop && (
          <div>
            <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '4px', textTransform: 'uppercase' }}>COP</div>
            <div style={{ fontSize: '16px', fontWeight: 600 }}>{system.cop.toFixed(1)}</div>
          </div>
        )}
        {system.volume && (
          <div>
            <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '4px', textTransform: 'uppercase' }}>Volumen</div>
            <div style={{ fontSize: '16px', fontWeight: 600 }}>{system.volume} L</div>
          </div>
        )}
        {system.air_flow_rate && (
          <div>
            <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '4px', textTransform: 'uppercase' }}>Luftmenge</div>
            <div style={{ fontSize: '16px', fontWeight: 600 }}>{system.air_flow_rate} m³/h</div>
          </div>
        )}
        {system.heat_recovery_efficiency && (
          <div>
            <div style={{ fontSize: '11px', color: '#64748b', marginBottom: '4px', textTransform: 'uppercase' }}>WRG-Grad</div>
            <div style={{ fontSize: '16px', fontWeight: 600 }}>{(system.heat_recovery_efficiency * 100).toFixed(0)}%</div>
          </div>
        )}
      </div>

      {/* ID Footer */}
      <div style={{ 
        marginTop: '12px', 
        paddingTop: '12px', 
        borderTop: '1px solid #e5e7eb',
        fontSize: '11px',
        color: '#94a3b8',
        fontFamily: 'monospace'
      }}>
        ID: {system.id}
      </div>
    </div>
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      {/* Heizung */}
      {heating.length > 0 && (
        <div>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: 600 }}>
            🔥 Heizung ({heating.length})
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
            {heating.map(system => <SystemCard key={system.id} system={system} />)}
          </div>
        </div>
      )}

      {/* Lüftung */}
      {ventilation.length > 0 && (
        <div>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: 600 }}>
            💨 Lüftung ({ventilation.length})
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
            {ventilation.map(system => <SystemCard key={system.id} system={system} />)}
          </div>
        </div>
      )}

      {/* Warmwasser */}
      {dhw.length > 0 && (
        <div>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: 600 }}>
            💧 Warmwasser ({dhw.length})
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
            {dhw.map(system => <SystemCard key={system.id} system={system} />)}
          </div>
        </div>
      )}

      {/* Kühlung */}
      {cooling.length > 0 && (
        <div>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: 600 }}>
            ❄️ Kühlung ({cooling.length})
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
            {cooling.map(system => <SystemCard key={system.id} system={system} />)}
          </div>
        </div>
      )}

      {/* Keine Systeme */}
      {heating.length === 0 && ventilation.length === 0 && dhw.length === 0 && cooling.length === 0 && (
        <div style={{ 
          textAlign: 'center', 
          padding: '40px', 
          color: '#64748b',
          background: '#f8fafc',
          borderRadius: '8px',
          border: '1px dashed #cbd5e1'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '16px' }}>🔧</div>
          <div style={{ fontSize: '16px', fontWeight: 500 }}>Keine Anlagentechnik definiert</div>
          <div style={{ fontSize: '14px', marginTop: '8px' }}>
            Fügen Sie Heizung, Lüftung oder Warmwassersysteme hinzu
          </div>
        </div>
      )}
    </div>
  )
}
