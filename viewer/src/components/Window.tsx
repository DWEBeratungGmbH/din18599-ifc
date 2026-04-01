import { useRef } from 'react'
import { Mesh } from 'three'
import { useViewerStore } from '../store/viewer.store'

interface WindowProps {
  id: string
  name: string
  orientation: number // 0=Nord, 90=Ost, 180=Süd, 270=West
  area: number
  uValueGlass: number
  gValue: number
}

export function Window({ id, orientation, area, uValueGlass, gValue }: WindowProps) {
  const meshRef = useRef<Mesh>(null)
  const { selectedId, hoveredId, selectElement, setHoveredId } = useViewerStore()

  // Berechne Dimensionen aus Fläche (Fenster sind meist rechteckig)
  const height = 1.5 // Standard-Fensterhöhe
  const width = area / height

  // Berechne Position basierend auf Orientierung (vor der Wand)
  const getPosition = (): [number, number, number] => {
    const wallDistance = 5.0 // Wand-Position
    const windowOffset = 0.5 // Fenster VOR der Wand
    const distance = wallDistance + windowOffset
    const heightPos = 2.0 // Höhe in der Wand
    switch (orientation) {
      case 0: // Nord
        return [0, heightPos, -distance]
      case 90: // Ost
        return [distance, heightPos, 0]
      case 180: // Süd
        return [0, heightPos, distance]
      case 270: // West
        return [-distance, heightPos, 0]
      default:
        return [0, heightPos, 0]
    }
  }

  // Berechne Rotation basierend auf Orientierung
  const getRotation = (): [number, number, number] => {
    switch (orientation) {
      case 0: // Nord
        return [0, 0, 0]
      case 90: // Ost
        return [0, Math.PI / 2, 0]
      case 180: // Süd
        return [0, Math.PI, 0]
      case 270: // West
        return [0, -Math.PI / 2, 0]
      default:
        return [0, 0, 0]
    }
  }

  // Farbe basierend auf U-Wert und State
  const getColor = () => {
    if (selectedId === id) return '#3b82f6' // Blau = Selected
    if (hoveredId === id) return '#60a5fa' // Hellblau = Hover
    
    // U-Wert Farbcodierung (Fenster haben andere Grenzwerte)
    if (uValueGlass > 2.0) return '#ef4444' // Rot = schlecht (alte Fenster)
    if (uValueGlass > 1.3) return '#f59e0b' // Orange = mittel
    return '#22c55e' // Grün = gut (Dreifachverglasung)
  }

  return (
    <mesh
      ref={meshRef}
      position={getPosition()}
      rotation={getRotation()}
      onClick={(e) => {
        e.stopPropagation() // Verhindert, dass Click an Wand weitergegeben wird
        selectElement(id)
      }}
      onPointerOver={(e) => {
        e.stopPropagation()
        setHoveredId(id)
      }}
      onPointerOut={() => setHoveredId(null)}
      renderOrder={10} // Fenster werden nach Wänden gerendert
    >
      <planeGeometry args={[width, height]} />
      <meshStandardMaterial 
        color={getColor()} 
        opacity={0.85}
        transparent
        side={2} // DoubleSide - von beiden Seiten sichtbar
        emissive={getColor()}
        emissiveIntensity={0.3}
        depthTest={true}
        depthWrite={true}
      />
    </mesh>
  )
}
