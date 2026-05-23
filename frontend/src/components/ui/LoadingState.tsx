export function LoadingState({ label = 'Loading…' }: { label?: string }) {
  return (
    <div style={{ padding: '64px 24px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '12px', color: 'var(--slate)' }}>
      <LoadingDots />
      <span style={{ fontSize: '12px', fontFamily: 'var(--f-mono)', letterSpacing: '0.06em' }}>{label}</span>
    </div>
  )
}

export function LoadingDots() {
  return (
    <div style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
      {[0, 1, 2].map(i => (
        <div
          key={i}
          style={{
            width: 6, height: 6, borderRadius: '50%',
            background: 'var(--slate)',
            animation: `pill-pulse 1.2s ease-in-out ${i * 0.2}s infinite`,
          }}
        />
      ))}
    </div>
  )
}
