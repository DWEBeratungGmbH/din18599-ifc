import { Canvas } from '@react-three/fiber'
import { OrbitControls, Grid } from '@react-three/drei'
import { useViewerStore } from './store/viewer.store'
import { Wall } from './components/Wall'
import { Roof } from './components/Roof'
import { Floor } from './components/Floor'
import { Window } from './components/Window'
import { ScenarioSwitcher } from './components/ScenarioSwitcher'

function App() {
  const { project, loadProject, selectedId, selectElement } = useViewerStore()

  // Berechne Netto-Wandflächen (Brutto - Fenster)
  const getNetWallArea = (wall: any) => {
    if (!project?.input.envelope?.windows) return wall.area
    
    // Summiere alle Fensterflächen in gleicher Orientierung
    const windowAreaInWall = project.input.envelope.windows
      .filter((w: any) => w.orientation === wall.orientation)
      .reduce((sum: number, w: any) => sum + w.area, 0)
    
    return Math.max(0, wall.area - windowAreaInWall)
  }

  const handleLoadDemo = async () => {
    try {
      const response = await fetch('/demo/efh-demo.din18599.json')
      if (!response.ok) throw new Error('Fehler beim Laden')
      const data = await response.json()
      loadProject(data)
    } catch (error) {
      console.error('Fehler beim Laden:', error)
      alert('Demo konnte nicht geladen werden')
    }
  }

  return (
    <div style={{ width: '100vw', height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* TopBar */}
      <div style={{ 
        height: '60px', 
        background: '#1e293b', 
        color: 'white', 
        display: 'flex', 
        alignItems: 'center', 
        padding: '0 20px',
        borderBottom: '1px solid #334155'
      }}>
        <h1 style={{ margin: 0, fontSize: '20px', fontWeight: 600 }}>
          🏢 DIN 18599 Viewer
        </h1>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: '10px' }}>
          <button 
            onClick={handleLoadDemo}
            style={{
              padding: '8px 16px',
              background: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px'
            }}
          >
            Demo laden
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, display: 'flex' }}>
        {/* Sidebar */}
        <div style={{
          width: '300px',
          background: '#f8fafc',
          borderRight: '1px solid #e2e8f0',
          padding: '20px',
          overflowY: 'auto'
        }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: 600 }}>
            📦 Gebäude-Struktur
          </h3>
          {!project ? (
            <div style={{ fontSize: '14px', color: '#64748b' }}>
              Noch keine Datei geladen...
            </div>
          ) : (
            <div style={{ fontSize: '14px' }}>
              <div style={{ marginBottom: '16px', padding: '12px', background: 'white', borderRadius: '6px' }}>
                <div style={{ fontWeight: 600, marginBottom: '8px' }}>{project.meta.project_name}</div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>
                  Baujahr: {project.input.building?.year_built || '-'}
                </div>
                <div style={{ fontSize: '12px', color: '#64748b' }}>
                  Fläche: {project.input.building?.net_floor_area || '-'} m²
                </div>
              </div>

              {/* Zones */}
              {project.input.zones && project.input.zones.length > 0 && (
                <div style={{ marginBottom: '12px' }}>
                  <div style={{ fontWeight: 600, marginBottom: '8px' }}>🏠 Zonen ({project.input.zones.length})</div>
                  {project.input.zones.map((zone: any) => (
                    <div key={zone.id} style={{ 
                      padding: '8px', 
                      background: 'white', 
                      borderRadius: '4px', 
                      marginBottom: '4px',
                      cursor: 'pointer',
                      fontSize: '13px'
                    }}>
                      {zone.name}
                    </div>
                  ))}
                </div>
              )}

              {/* Envelope */}
              {project.input.envelope && (
                <div style={{ marginBottom: '12px' }}>
                  <div style={{ fontWeight: 600, marginBottom: '8px' }}>🧱 Gebäudehülle</div>
                  
                  {project.input.envelope.walls_external && project.input.envelope.walls_external.length > 0 && (
                    <div style={{ marginBottom: '8px' }}>
                      <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>
                        Außenwände ({project.input.envelope.walls_external.length})
                      </div>
                      {project.input.envelope.walls_external.map((wall: any) => {
                        const netArea = getNetWallArea(wall)
                        const windowsInWall = project.input.envelope.windows?.filter(
                          (w: any) => w.orientation === wall.orientation
                        ) || []
                        
                        return (
                          <div key={wall.id} style={{ marginBottom: '4px' }}>
                            {/* Wand */}
                            <div 
                              style={{ 
                                padding: '6px 8px', 
                                background: selectedId === wall.id ? '#dbeafe' : '#f9fafb',
                                borderRadius: '4px', 
                                cursor: 'pointer',
                                fontSize: '12px',
                                borderLeft: selectedId === wall.id ? '3px solid #3b82f6' : '3px solid transparent',
                                fontWeight: 600
                              }}
                              onClick={() => selectElement(wall.id)}
                            >
                              <div>{wall.name}</div>
                              <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 400 }}>
                                Netto: {netArea.toFixed(1)} m² • U={wall.u_value_undisturbed} W/(m²K)
                              </div>
                            </div>
                            
                            {/* Fenster/Türen als Kinder */}
                            {windowsInWall.length > 0 && (
                              <div style={{ marginLeft: '16px', marginTop: '2px' }}>
                                {windowsInWall.map((window: any) => (
                                  <div 
                                    key={window.id}
                                    style={{ 
                                      padding: '4px 8px', 
                                      background: selectedId === window.id ? '#dbeafe' : 'white',
                                      borderRadius: '4px', 
                                      marginBottom: '2px',
                                      cursor: 'pointer',
                                      fontSize: '11px',
                                      borderLeft: selectedId === window.id ? '2px solid #3b82f6' : '2px solid #e5e7eb',
                                      display: 'flex',
                                      alignItems: 'center',
                                      gap: '4px'
                                    }}
                                    onClick={() => selectElement(window.id)}
                                  >
                                    <span>└─</span>
                                    <span>{window.name}</span>
                                    <span style={{ color: '#64748b' }}>({window.area.toFixed(1)} m²)</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )
                      })}
                    </div>
                  )}

                  {project.input.envelope.roofs && project.input.envelope.roofs.length > 0 && (
                    <div style={{ marginBottom: '8px' }}>
                      <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>
                        Dächer ({project.input.envelope.roofs.length})
                      </div>
                      {project.input.envelope.roofs.map((roof: any) => (
                        <div key={roof.id} style={{ 
                          padding: '6px 8px', 
                          background: 'white',
                          borderRadius: '4px', 
                          marginBottom: '2px',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}>
                          {roof.name}
                        </div>
                      ))}
                    </div>
                  )}

                  {project.input.envelope.windows && project.input.envelope.windows.length > 0 && (
                    <div>
                      <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>
                        Fenster ({project.input.envelope.windows.length})
                      </div>
                      {project.input.envelope.windows.map((window: any) => (
                        <div key={window.id} style={{ 
                          padding: '6px 8px', 
                          background: 'white',
                          borderRadius: '4px', 
                          marginBottom: '2px',
                          cursor: 'pointer',
                          fontSize: '12px'
                        }}>
                          {window.name}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* 3D Canvas */}
        <div style={{ flex: 1, position: 'relative' }}>
          <Canvas
            camera={{ position: [10, 10, 10], fov: 50 }}
            style={{ background: '#0f172a' }}
          >
            {/* Lighting */}
            <ambientLight intensity={0.5} />
            <directionalLight position={[10, 10, 5]} intensity={1} />
            
            {/* Grid Helper */}
            <Grid 
              args={[20, 20]} 
              cellColor="#334155" 
              sectionColor="#475569"
              fadeDistance={30}
            />
            
            {/* Gebäude-Geometrie */}
            
            {/* Wände */}
            {project?.input.envelope?.walls_external?.map((wall: any) => (
              <Wall
                key={wall.id}
                id={wall.id}
                name={wall.name}
                orientation={wall.orientation}
                area={wall.area}
                uValue={wall.u_value_undisturbed}
              />
            ))}

            {/* Dächer */}
            {project?.input.envelope?.roofs?.map((roof: any) => (
              <Roof
                key={roof.id}
                id={roof.id}
                name={roof.name}
                orientation={roof.orientation}
                inclination={roof.inclination}
                area={roof.area}
                uValue={roof.u_value_undisturbed}
              />
            ))}

            {/* Böden */}
            {project?.input.envelope?.floors?.map((floor: any) => (
              <Floor
                key={floor.id}
                id={floor.id}
                name={floor.name}
                area={floor.area}
                uValue={floor.u_value_undisturbed}
                boundaryCondition={floor.boundary_condition}
              />
            ))}

            {/* Fenster */}
            {project?.input.envelope?.windows?.map((window: any) => (
              <Window
                key={window.id}
                id={window.id}
                name={window.name}
                orientation={window.orientation}
                area={window.area}
                uValueGlass={window.u_value_glass}
                gValue={window.g_value}
              />
            ))}
            
            {/* Camera Controls */}
            <OrbitControls makeDefault />
          </Canvas>

          {/* Szenario-Switcher (oben mittig) */}
          <ScenarioSwitcher />

          {/* Inspector Panel (rechts) */}
          <div style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            width: '320px',
            background: 'white',
            borderRadius: '8px',
            boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
            padding: '20px',
            maxHeight: 'calc(100vh - 160px)',
            overflowY: 'auto'
          }}>
            <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: 600 }}>
              🔍 Inspector
            </h3>
            {!selectedId ? (
              <div style={{ fontSize: '14px', color: '#64748b' }}>
                Kein Bauteil ausgewählt
              </div>
            ) : (() => {
              // Suche in allen Bauteil-Typen
              const selectedWall = project?.input.envelope?.walls_external?.find((w: any) => w.id === selectedId)
              const selectedRoof = project?.input.envelope?.roofs?.find((r: any) => r.id === selectedId)
              const selectedFloor = project?.input.envelope?.floors?.find((f: any) => f.id === selectedId)
              const selectedWindow = project?.input.envelope?.windows?.find((w: any) => w.id === selectedId)
              
              const selectedElement = selectedWall || selectedRoof || selectedFloor || selectedWindow
              if (!selectedElement) return <div style={{ fontSize: '14px', color: '#64748b' }}>Bauteil nicht gefunden</div>
              
              const uEff = selectedWindow 
                ? selectedWindow.u_value_glass 
                : selectedElement.u_value_undisturbed + (selectedElement.thermal_bridge_delta_u || 0)
              const orientationName = selectedElement.orientation !== undefined 
                ? ['Nord', 'Ost', 'Süd', 'West'][Math.round(selectedElement.orientation / 90) % 4]
                : '-'
              const elementType = selectedWall ? 'Wand' : selectedRoof ? 'Dach' : selectedFloor ? 'Boden' : 'Fenster'
              
              return (
                <div style={{ fontSize: '14px' }}>
                  <div style={{ marginBottom: '16px', paddingBottom: '16px', borderBottom: '1px solid #e5e7eb' }}>
                    <div style={{ fontWeight: 600, fontSize: '16px', marginBottom: '8px' }}>
                      {selectedElement.name}
                    </div>
                    <div style={{ fontSize: '12px', color: '#64748b' }}>
                      {elementType} • ID: {selectedElement.id}
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {selectedElement.orientation !== undefined && (
                      <div>
                        <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Orientierung</div>
                        <div style={{ fontWeight: 600 }}>{orientationName} ({selectedElement.orientation}°)</div>
                      </div>
                    )}

                    {selectedRoof && selectedRoof.inclination !== undefined && (
                      <div>
                        <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Dachneigung</div>
                        <div style={{ fontWeight: 600 }}>{selectedRoof.inclination}°</div>
                      </div>
                    )}

                    {selectedWall ? (
                      <>
                        <div>
                          <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Fläche (Brutto)</div>
                          <div style={{ fontWeight: 600 }}>{selectedWall.area} m²</div>
                        </div>
                        <div>
                          <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Fläche (Netto)</div>
                          <div style={{ fontWeight: 600, color: '#3b82f6' }}>
                            {getNetWallArea(selectedWall).toFixed(2)} m²
                          </div>
                          <div style={{ fontSize: '11px', color: '#64748b', marginTop: '2px' }}>
                            ⚠️ Thermische Hüllfläche (ohne Fenster)
                          </div>
                        </div>
                      </>
                    ) : (
                      <div>
                        <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Fläche</div>
                        <div style={{ fontWeight: 600 }}>{selectedElement.area} m²</div>
                      </div>
                    )}

                    {selectedWindow ? (
                      <>
                        <div>
                          <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>U-Wert Glas (Ug)</div>
                          <div style={{ 
                            fontWeight: 600,
                            color: selectedWindow.u_value_glass > 2.0 ? '#ef4444' : selectedWindow.u_value_glass > 1.3 ? '#f59e0b' : '#22c55e'
                          }}>
                            {selectedWindow.u_value_glass.toFixed(2)} W/(m²K)
                          </div>
                        </div>

                        <div>
                          <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>U-Wert Rahmen (Uf)</div>
                          <div style={{ fontWeight: 600 }}>
                            {selectedWindow.u_value_frame.toFixed(2)} W/(m²K)
                          </div>
                        </div>

                        <div>
                          <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>g-Wert (Energiedurchlass)</div>
                          <div style={{ fontWeight: 600 }}>
                            {selectedWindow.g_value.toFixed(2)}
                          </div>
                        </div>

                        <div>
                          <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Rahmenanteil</div>
                          <div style={{ fontWeight: 600 }}>
                            {(selectedWindow.frame_fraction * 100).toFixed(0)}%
                          </div>
                        </div>
                      </>
                    ) : (
                      <>
                        <div>
                          <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>U-Wert (ungestört)</div>
                          <div style={{ 
                            fontWeight: 600,
                            color: selectedElement.u_value_undisturbed > 1.0 ? '#ef4444' : selectedElement.u_value_undisturbed > 0.5 ? '#f59e0b' : '#22c55e'
                          }}>
                            {selectedElement.u_value_undisturbed.toFixed(3)} W/(m²K)
                          </div>
                        </div>

                        <div>
                          <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Wärmebrücken ΔU</div>
                          <div style={{ fontWeight: 600 }}>
                            {(selectedElement.thermal_bridge_delta_u || 0).toFixed(3)} W/(m²K)
                          </div>
                        </div>
                      </>
                    )}

                    <div style={{ 
                      padding: '12px', 
                      background: '#f9fafb', 
                      borderRadius: '6px',
                      border: '1px solid #e5e7eb'
                    }}>
                      <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>U-Wert (effektiv)</div>
                      <div style={{ 
                        fontWeight: 700,
                        fontSize: '18px',
                        color: uEff > 1.0 ? '#ef4444' : uEff > 0.5 ? '#f59e0b' : '#22c55e'
                      }}>
                        {uEff.toFixed(3)} W/(m²K)
                      </div>
                    </div>

                    {selectedElement.construction_catalog_ref && (
                      <div>
                        <div style={{ fontSize: '12px', color: '#64748b', marginBottom: '4px' }}>Konstruktion</div>
                        <div style={{ 
                          fontSize: '12px',
                          padding: '8px',
                          background: '#f9fafb',
                          borderRadius: '4px'
                        }}>
                          {selectedElement.construction_catalog_ref}
                        </div>
                      </div>
                    )}

                    <div style={{ 
                      marginTop: '8px',
                      padding: '8px',
                      background: uEff > 0.5 ? '#fef3c7' : '#d1fae5',
                      borderRadius: '4px',
                      fontSize: '12px'
                    }}>
                      {uEff > 1.0 && '⚠️ Sehr schlechte Dämmung - dringend sanierungsbedürftig'}
                      {uEff > 0.5 && uEff <= 1.0 && '⚠️ Verbesserungspotential vorhanden'}
                      {uEff <= 0.5 && '✅ Gute Dämmqualität'}
                    </div>
                  </div>
                </div>
              )
            })()}
          </div>
        </div>
      </div>

      {/* BottomBar */}
      <div style={{
        height: '50px',
        background: '#f8fafc',
        borderTop: '1px solid #e2e8f0',
        display: 'flex',
        alignItems: 'center',
        padding: '0 20px',
        fontSize: '14px',
        color: '#64748b',
        gap: '24px'
      }}>
        {!project || !project.output ? (
          <div>⚡ Energiekennwerte: Noch keine Berechnung</div>
        ) : (
          <>
            <div>
              <span style={{ fontWeight: 600, color: '#1e293b' }}>Endenergie:</span>{' '}
              {Math.round(project.output.energy_balance?.final_energy_kwh_a || 0).toLocaleString()} kWh/a
            </div>
            <div>
              <span style={{ fontWeight: 600, color: '#1e293b' }}>Primärenergie:</span>{' '}
              {Math.round(project.output.energy_balance?.primary_energy_kwh_a || 0).toLocaleString()} kWh/a
            </div>
            <div>
              <span style={{ fontWeight: 600, color: '#1e293b' }}>CO₂:</span>{' '}
              {Math.round(project.output.energy_balance?.co2_emissions_kg_a || 0).toLocaleString()} kg/a
            </div>
            {project.output.indicators && (
              <div>
                <span style={{ fontWeight: 600, color: '#1e293b' }}>Effizienzklasse:</span>{' '}
                <span style={{
                  padding: '2px 8px',
                  borderRadius: '4px',
                  background: project.output.indicators.efficiency_class === 'F' ? '#f97316' : '#22c55e',
                  color: 'white',
                  fontWeight: 600,
                  fontSize: '12px'
                }}>
                  {project.output.indicators.efficiency_class}
                </span>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default App
