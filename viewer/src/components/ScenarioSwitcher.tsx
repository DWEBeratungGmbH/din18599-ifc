import { useViewerStore } from '../store/viewer.store'

export function ScenarioSwitcher() {
  const project = useViewerStore((state) => state.project)
  const activeScenario = useViewerStore((state) => state.activeScenario)
  const switchScenario = useViewerStore((state) => state.switchScenario)

  if (!project?.scenarios || project.scenarios.length === 0) {
    return null
  }

  const scenarios = [
    { id: 'base', name: 'Bestand', description: 'Aktueller Zustand' },
    ...project.scenarios.map(s => ({
      id: s.id,
      name: s.name,
      description: s.description || ''
    }))
  ]

  const currentScenario = scenarios.find(s => s.id === activeScenario)

  return (
    <div style={{
      position: 'absolute',
      top: '20px',
      left: '50%',
      transform: 'translateX(-50%)',
      background: 'white',
      borderRadius: '8px',
      boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
      padding: '12px 16px',
      zIndex: 1000,
      minWidth: '300px'
    }}>
      <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '8px' }}>
        Szenario
      </div>
      
      <select
        value={activeScenario}
        onChange={(e) => switchScenario(e.target.value)}
        style={{
          width: '100%',
          padding: '8px 12px',
          fontSize: '14px',
          border: '1px solid #e5e7eb',
          borderRadius: '6px',
          background: 'white',
          cursor: 'pointer',
          outline: 'none'
        }}
      >
        {scenarios.map(scenario => (
          <option key={scenario.id} value={scenario.id}>
            {scenario.name}
          </option>
        ))}
      </select>

      {currentScenario?.description && (
        <div style={{
          marginTop: '8px',
          fontSize: '12px',
          color: '#64748b',
          lineHeight: '1.4'
        }}>
          {currentScenario.description}
        </div>
      )}

      {/* Maßnahmen anzeigen */}
      {activeScenario !== 'base' && (() => {
        const scenario = project.scenarios?.find(s => s.id === activeScenario)
        if (!scenario?.measures || scenario.measures.length === 0) return null

        return (
          <div style={{
            marginTop: '12px',
            paddingTop: '12px',
            borderTop: '1px solid #e5e7eb'
          }}>
            <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: '8px' }}>
              Maßnahmen:
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {scenario.measures.map((measure, idx) => (
                <div key={idx} style={{
                  fontSize: '12px',
                  padding: '6px 8px',
                  background: '#f8fafc',
                  borderRadius: '4px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <span>{measure.name}</span>
                  {measure.cost_estimate && (
                    <span style={{ color: '#64748b', fontSize: '11px' }}>
                      {new Intl.NumberFormat('de-DE', {
                        style: 'currency',
                        currency: 'EUR',
                        maximumFractionDigits: 0
                      }).format(measure.cost_estimate)}
                    </span>
                  )}
                </div>
              ))}
            </div>

            {/* Gesamtkosten */}
            {(() => {
              const totalCost = scenario.measures.reduce(
                (sum, m) => sum + (m.cost_estimate || 0),
                0
              )
              const totalFunding = scenario.measures.reduce(
                (sum, m) => sum + (m.funding_amount || 0),
                0
              )

              if (totalCost === 0) return null

              return (
                <div style={{
                  marginTop: '8px',
                  paddingTop: '8px',
                  borderTop: '1px solid #e5e7eb',
                  fontSize: '12px'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span>Investition:</span>
                    <span style={{ fontWeight: 600 }}>
                      {new Intl.NumberFormat('de-DE', {
                        style: 'currency',
                        currency: 'EUR',
                        maximumFractionDigits: 0
                      }).format(totalCost)}
                    </span>
                  </div>
                  {totalFunding > 0 && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', color: '#10b981' }}>
                      <span>Förderung:</span>
                      <span style={{ fontWeight: 600 }}>
                        {new Intl.NumberFormat('de-DE', {
                          style: 'currency',
                          currency: 'EUR',
                          maximumFractionDigits: 0
                        }).format(totalFunding)}
                      </span>
                    </div>
                  )}
                </div>
              )
            })()}
          </div>
        )
      })()}

      {/* Einsparungen anzeigen */}
      {activeScenario !== 'base' && (() => {
        const scenario = project.scenarios?.find(s => s.id === activeScenario)
        if (!scenario?.output?.savings) return null

        const savings = scenario.output.savings

        return (
          <div style={{
            marginTop: '12px',
            paddingTop: '12px',
            borderTop: '1px solid #e5e7eb'
          }}>
            <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: '8px' }}>
              Einsparungen:
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <div style={{
                fontSize: '12px',
                padding: '6px 8px',
                background: '#f0fdf4',
                borderRadius: '4px',
                display: 'flex',
                justifyContent: 'space-between'
              }}>
                <span>Endenergie:</span>
                <span style={{ fontWeight: 600, color: '#10b981' }}>
                  -{savings.final_energy_percent.toFixed(1)}%
                </span>
              </div>
              <div style={{
                fontSize: '12px',
                padding: '6px 8px',
                background: '#f0fdf4',
                borderRadius: '4px',
                display: 'flex',
                justifyContent: 'space-between'
              }}>
                <span>CO₂:</span>
                <span style={{ fontWeight: 600, color: '#10b981' }}>
                  -{savings.co2_percent.toFixed(1)}%
                </span>
              </div>
              {savings.cost_annual_eur > 0 && (
                <div style={{
                  fontSize: '12px',
                  padding: '6px 8px',
                  background: '#f0fdf4',
                  borderRadius: '4px',
                  display: 'flex',
                  justifyContent: 'space-between'
                }}>
                  <span>Jährlich:</span>
                  <span style={{ fontWeight: 600, color: '#10b981' }}>
                    {new Intl.NumberFormat('de-DE', {
                      style: 'currency',
                      currency: 'EUR',
                      maximumFractionDigits: 0
                    }).format(savings.cost_annual_eur)}
                  </span>
                </div>
              )}
            </div>
          </div>
        )
      })()}
    </div>
  )
}
