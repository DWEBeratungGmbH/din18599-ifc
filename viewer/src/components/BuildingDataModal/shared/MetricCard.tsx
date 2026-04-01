interface MetricCardProps {
  label: string
  value: string | number
  unit?: string
  trend?: 'good' | 'medium' | 'bad'
  icon?: string
}

export function MetricCard({ label, value, unit, trend, icon }: MetricCardProps) {
  const trendColors = {
    good: '#22c55e',
    medium: '#f59e0b',
    bad: '#ef4444'
  }

  return (
    <div style={{
      background: 'white',
      border: '1px solid #e5e7eb',
      borderRadius: '8px',
      padding: '16px',
      display: 'flex',
      flexDirection: 'column',
      gap: '8px'
    }}>
      <div style={{
        fontSize: '12px',
        color: '#64748b',
        fontWeight: 500,
        textTransform: 'uppercase',
        letterSpacing: '0.5px'
      }}>
        {icon && <span style={{ marginRight: '6px' }}>{icon}</span>}
        {label}
      </div>
      <div style={{
        fontSize: '24px',
        fontWeight: 600,
        color: trend ? trendColors[trend] : '#1e293b',
        display: 'flex',
        alignItems: 'baseline',
        gap: '4px'
      }}>
        <span>{typeof value === 'number' ? value.toLocaleString('de-DE') : value}</span>
        {unit && (
          <span style={{ fontSize: '14px', fontWeight: 400, color: '#64748b' }}>
            {unit}
          </span>
        )}
      </div>
    </div>
  )
}
