interface StatusBadgeProps {
  status: 'good' | 'medium' | 'bad' | 'neutral'
  label?: string
}

export function StatusBadge({ status, label }: StatusBadgeProps) {
  const styles = {
    good: { bg: '#dcfce7', color: '#166534', border: '#86efac' },
    medium: { bg: '#fef3c7', color: '#92400e', border: '#fcd34d' },
    bad: { bg: '#fee2e2', color: '#991b1b', border: '#fca5a5' },
    neutral: { bg: '#f1f5f9', color: '#475569', border: '#cbd5e1' }
  }

  const style = styles[status]

  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      padding: '2px 8px',
      borderRadius: '12px',
      fontSize: '11px',
      fontWeight: 600,
      background: style.bg,
      color: style.color,
      border: `1px solid ${style.border}`
    }}>
      {label || status.toUpperCase()}
    </span>
  )
}
