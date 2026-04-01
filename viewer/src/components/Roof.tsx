import { useRef } from 'react'
import { Mesh } from 'three'
import { useViewerStore } from '../store/viewer.store'

interface RoofProps {
  id: string
  name: string
  orientation: number
  inclination: number // Dachneigung in Grad
  area: number
  uValue: number
}

export function Roof({ id, orientation, inclination, area, uValue }: RoofProps) {
  const meshRef = useRef<Mesh>(null)
  const { selectedId, hoveredId, selectElement, setHoveredId } = useViewerStore()

  // Berechne Dimensionen aus Fläche (vereinfacht)
  const width = Math.sqrt(area)
  const depth = area / width

  // Position: Oben auf dem Gebäude
  const position: [number, number, number] = [0, 4.5, 0]

  // Rotation basierend auf Neigung
  const rotation: [number, number, number] = [
    (inclination * Math.PI) / 180, // X-Rotation = Neigung
    0,
    0
  ]

  // Farbe basierend auf U-Wert und State
  const getColor = () => {
    if (selectedId === id) return '#3b82f6' // Blau = Selected
    if (hoveredId === id) return '#60a5fa' // Hellblau = Hover
    
    // U-Wert Farbcodierung
    if (uValue > 0.8) return '#ef4444' // Rot = schlecht
    if (uValue > 0.4) return '#f59e0b' // Orange = mittel
    return '#22c55e' // Grün = gut
  }

  return (
    <mesh
      ref={meshRef}
      position={position}
      rotation={rotation}
      onClick={() => selectElement(id)}
      onPointerOver={() => setHoveredId(id)}
      onPointerOut={() => setHoveredId(null)}
    >
      <planeGeometry args={[width, depth]} />
      <meshStandardMaterial 
        color={getColor()} 
        opacity={0.9}
        transparent
        side={2} // DoubleSide
      />
    </mesh>
  )
}
