interface UValueIndicatorProps {
  uValue: number
  elementType: 'wall' | 'roof' | 'floor' | 'window'
}

export function UValueIndicator({ uValue, elementType }: UValueIndicatorProps) {
  const thresholds = {
    wall: { good: 0.24, medium: 0.5 },
    roof: { good: 0.14, medium: 0.35 },
    floor: { good: 0.25, medium: 0.5 },
    window: { good: 1.0, medium: 1.3 }
  }

  const t = thresholds[elementType]
  let status: 'good' | 'medium' | 'bad'
  
  if (uValue <= t.good) status = 'good'
  else if (uValue <= t.medium) status = 'medium'
  else status = 'bad'

  const colors = {
    good: '#22c55e',
    medium: '#f59e0b',
    bad: '#ef4444'
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
      <span style={{ fontWeight: 600, color: '#1e293b' }}>
        {uValue.toFixed(2)}
      </span>
      <div style={{
        width: '8px',
        height: '8px',
        borderRadius: '50%',
        background: colors[status]
      }} />
    </div>
  )
}
