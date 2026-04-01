import { useRef } from 'react'
import { Mesh } from 'three'
import { useViewerStore } from '../store/viewer.store'

interface FloorProps {
  id: string
  name: string
  area: number
  uValue: number
  boundaryCondition: string // GROUND, EXTERNAL, etc.
}

export function Floor({ id, area, uValue, boundaryCondition }: FloorProps) {
  const meshRef = useRef<Mesh>(null)
  const { selectedId, hoveredId, selectElement, setHoveredId } = useViewerStore()

  // Berechne Dimensionen aus Fläche
  const width = Math.sqrt(area)
  const depth = area / width

  // Position: Am Boden (y=0)
  const position: [number, number, number] = [0, 0, 0]

  // Farbe basierend auf U-Wert und State
  const getColor = () => {
    if (selectedId === id) return '#3b82f6' // Blau = Selected
    if (hoveredId === id) return '#60a5fa' // Hellblau = Hover
    
    // U-Wert Farbcodierung
    if (uValue > 1.0) return '#ef4444' // Rot = schlecht
    if (uValue > 0.5) return '#f59e0b' // Orange = mittel
    return '#22c55e' // Grün = gut
  }

  return (
    <mesh
      ref={meshRef}
      position={position}
      rotation={[-Math.PI / 2, 0, 0]} // Horizontal (Boden)
      onClick={() => selectElement(id)}
      onPointerOver={() => setHoveredId(id)}
      onPointerOut={() => setHoveredId(null)}
    >
      <planeGeometry args={[width, depth]} />
      <meshStandardMaterial 
        color={getColor()} 
        opacity={0.6}
        transparent
        side={2} // DoubleSide
      />
    </mesh>
  )
}
