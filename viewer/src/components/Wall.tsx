import { useRef } from 'react'
import { Mesh } from 'three'
import { useViewerStore } from '../store/viewer.store'

interface WallProps {
  id: string
  name: string
  orientation: number // 0=Nord, 90=Ost, 180=Süd, 270=West
  area: number
  uValue: number
  position?: [number, number, number]
}

export function Wall({ id, orientation, area, uValue, position = [0, 0, 0] }: WallProps) {
  const meshRef = useRef<Mesh>(null)
  const { selectedId, hoveredId, selectElement, setHoveredId } = useViewerStore()

  // Berechne Dimensionen aus Fläche (vereinfacht: Höhe = 3m)
  const height = 3
  const width = area / height

  // Berechne Position basierend auf Orientierung
  const getPosition = (): [number, number, number] => {
    const distance = 5 // Abstand vom Zentrum
    switch (orientation) {
      case 0: // Nord
        return [0, height / 2, -distance]
      case 90: // Ost
        return [distance, height / 2, 0]
      case 180: // Süd
        return [0, height / 2, distance]
      case 270: // West
        return [-distance, height / 2, 0]
      default:
        return position
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
    
    // U-Wert Farbcodierung
    if (uValue > 1.0) return '#ef4444' // Rot = schlecht (> 1.0)
    if (uValue > 0.5) return '#f59e0b' // Orange = mittel (0.5-1.0)
    return '#22c55e' // Grün = gut (< 0.5)
  }

  return (
    <mesh
      ref={meshRef}
      position={getPosition()}
      rotation={getRotation()}
      onClick={() => selectElement(id)}
      onPointerOver={() => setHoveredId(id)}
      onPointerOut={() => setHoveredId(null)}
      renderOrder={1} // Wände werden zuerst gerendert
    >
      <planeGeometry args={[width, height]} />
      <meshStandardMaterial 
        color={getColor()} 
        opacity={0.9}
        transparent
        side={2} // DoubleSide - von beiden Seiten sichtbar
      />
    </mesh>
  )
}
