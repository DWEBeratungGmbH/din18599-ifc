import { useViewerStore } from '../../../store/viewer.store'
import { MetricCard } from '../shared/MetricCard'
import { StatusBadge } from '../shared/StatusBadge'

export function OverviewTab() {
  const project = useViewerStore((state) => state.project)

  if (!project) return null

  const output = project.output
  const building = project.input.building
  const zones = project.input.zones || []

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* KPI Cards */}
      {output?.energy_balance && (
        <div>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: 600 }}>
            Energiekennwerte
          </h3>
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '16px'
          }}>
            <MetricCard
              icon="⚡"
              label="Endenergie"
              value={Math.round(output.energy_balance.final_energy_kwh_a)}
              unit="kWh/a"
              trend={output.energy_balance.final_energy_kwh_a < 100000 ? 'good' : 'medium'}
            />
            <MetricCard
              icon="🔋"
              label="Primärenergie"
              value={Math.round(output.energy_balance.primary_energy_kwh_a)}
              unit="kWh/a"
              trend={output.energy_balance.primary_energy_kwh_a < 120000 ? 'good' : 'medium'}
            />
            <MetricCard
              icon="🌍"
              label="CO₂-Emissionen"
              value={Math.round(output.energy_balance.co2_emissions_kg_a)}
              unit="kg/a"
              trend={output.energy_balance.co2_emissions_kg_a < 30000 ? 'good' : 'bad'}
            />
            {output.indicators?.efficiency_class && (
              <MetricCard
                icon="📊"
                label="Effizienzklasse"
                value={output.indicators.efficiency_class}
                trend={
                  ['A+', 'A'].includes(output.indicators.efficiency_class) ? 'good' :
                  ['B', 'C', 'D'].includes(output.indicators.efficiency_class) ? 'medium' : 'bad'
                }
              />
            )}
          </div>
        </div>
      )}

      {/* 2-Spalten Layout: Meta + Klima */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* Projekt-Metadaten */}
        <div style={{
          background: '#f8fafc',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          padding: '20px'
        }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: 600 }}>
            Projekt-Metadaten
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '14px' }}>
            <div>
              <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Projektname</div>
              <div style={{ fontWeight: 600 }}>{project.meta.project_name}</div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Gebäudetyp</div>
              <div style={{ fontWeight: 600 }}>{building?.building_type || 'Wohngebäude'}</div>
            </div>
            {building?.year_construction && (
              <div>
                <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Baujahr</div>
                <div style={{ fontWeight: 600 }}>{building.year_construction}</div>
              </div>
            )}
            <div>
              <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Energiebezugsfläche</div>
              <div style={{ fontWeight: 600 }}>
                {zones.reduce((sum, z) => sum + (z.area_an || 0), 0).toFixed(1)} m²
              </div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Schema-Version</div>
              <div style={{ fontWeight: 600 }}>{project.meta.schema_version}</div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Erstellt von</div>
              <div style={{ fontWeight: 600 }}>{project.meta.created_by}</div>
            </div>
          </div>
        </div>

        {/* Klimadaten & Norm */}
        <div style={{
          background: '#f8fafc',
          border: '1px solid #e5e7eb',
          borderRadius: '8px',
          padding: '20px'
        }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: 600 }}>
            Klimadaten & Norm
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', fontSize: '14px' }}>
            {building?.location && typeof building.location === 'object' && 'climate_zone' in building.location && (
              <div>
                <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Klimazone</div>
                <div style={{ fontWeight: 600 }}>{building.location.climate_zone}</div>
              </div>
            )}
            {building?.location && typeof building.location === 'object' && 'latitude' in building.location && (
              <div>
                <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Koordinaten</div>
                <div style={{ fontWeight: 600 }}>
                  {building.location.latitude.toFixed(2)}°N, {building.location.longitude.toFixed(2)}°E
                </div>
              </div>
            )}
            <div>
              <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Norm</div>
              <div style={{ fontWeight: 600 }}>DIN V 18599</div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>IFC-Verknüpfung</div>
              <div>
                <StatusBadge status="good" label="VERKNÜPFT" />
              </div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Letzte Validierung</div>
              <div style={{ fontWeight: 600 }}>Vor 2 Min</div>
            </div>
          </div>
        </div>
      </div>

      {/* LOD Panel */}
      <div style={{
        background: '#f8fafc',
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
        padding: '20px'
      }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: 600 }}>
          Level of Detail (LOD)
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Geometry */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '14px', fontWeight: 500 }}>Geometry</span>
              <span style={{ fontSize: '14px', fontWeight: 600, color: '#22c55e' }}>LOD 300</span>
            </div>
            <div style={{ 
              height: '8px', 
              background: '#e5e7eb', 
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div style={{ 
                width: '100%', 
                height: '100%', 
                background: '#22c55e'
              }} />
            </div>
          </div>

          {/* Envelope */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '14px', fontWeight: 500 }}>Envelope</span>
              <span style={{ fontSize: '14px', fontWeight: 600, color: '#22c55e' }}>LOD 300</span>
            </div>
            <div style={{ 
              height: '8px', 
              background: '#e5e7eb', 
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div style={{ 
                width: '100%', 
                height: '100%', 
                background: '#22c55e'
              }} />
            </div>
          </div>

          {/* Systems */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span style={{ fontSize: '14px', fontWeight: 500 }}>Systems</span>
              <span style={{ fontSize: '14px', fontWeight: 600, color: '#f59e0b' }}>LOD 200</span>
            </div>
            <div style={{ 
              height: '8px', 
              background: '#e5e7eb', 
              borderRadius: '4px',
              overflow: 'hidden'
            }}>
              <div style={{ 
                width: '66%', 
                height: '100%', 
                background: '#f59e0b'
              }} />
            </div>
          </div>

          {/* Overall */}
          <div style={{
            marginTop: '8px',
            paddingTop: '16px',
            borderTop: '1px solid #e5e7eb'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '14px', fontWeight: 600 }}>Overall LOD</span>
              <span style={{ fontSize: '16px', fontWeight: 700, color: '#22c55e' }}>300</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
