// Treadstone UI kit, following DESIGN.md section 7.

const ICONS = {
  home: <><rect x="3" y="3" width="7" height="8" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" /><rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="15" width="7" height="6" rx="1.5" /></>,
  groups: <><circle cx="9" cy="8" r="3.5" /><path d="M2.5 20a6.5 6.5 0 0113 0" /><path d="M16 4.5a3.5 3.5 0 010 7M18 14a6 6 0 013.5 6" /></>,
  vault: <><path d="M5 20h14l-2-9H7z" /><path d="M9 11V8a3 3 0 016 0v3" /></>,
  ledger: <><path d="M6 3h9l3 3v15H6z" /><path d="M9 10h6M9 14h6M9 18h3" /></>,
  me: <><circle cx="12" cy="8" r="4" /><path d="M4 21a8 8 0 0116 0" /></>,
  loans: <><rect x="3" y="6" width="18" height="13" rx="2" /><path d="M3 10h18M7 15h3" /></>,
  bell: <><path d="M6 8a6 6 0 0112 0c0 7 3 9 3 9H3s3-2 3-9" /><path d="M10.3 21a1.9 1.9 0 003.4 0" /></>,
  back: <path d="M15 18l-6-6 6-6" />,
  chevron: <path d="M9 6l6 6-6 6" />,
  plus: <path d="M12 5v14M5 12h14" />,
  up: <><path d="M12 19V5" /><path d="M6 11l6-6 6 6" /></>,
  payGroup: <><circle cx="9" cy="8" r="3.5" /><path d="M2.5 20a6.5 6.5 0 0113 0" /><path d="M19 8v6M16 11h6" /></>,
  shield: <><path d="M12 3l8 3v6c0 4.5-3.4 8.3-8 9-4.6-.7-8-4.5-8-9V6z" /><path d="M9 12l2 2 4-4" /></>,
  copy: <><rect x="9" y="9" width="11" height="11" rx="2" /><path d="M5 15V5a1 1 0 011-1h10" /></>,
  check: <path d="M5 12l5 5L20 7" />,
  calendar: <><rect x="3" y="5" width="18" height="16" rx="2" /><path d="M3 10h18M8 3v4M16 3v4" /></>,
  clock: <><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></>,
  logout: <><path d="M15 4h4v16h-4" /><path d="M10 8l-4 4 4 4M6 12h10" /></>,
  phone: <><rect x="7" y="2" width="10" height="20" rx="2" /><path d="M11 18h2" /></>,
  eye: <><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z" /><circle cx="12" cy="12" r="3" /></>,
}

export function Icon({ name, size = 20, className = '', strokeWidth = 1.8 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={strokeWidth}
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className={`shrink-0 ${className}`}>
      {ICONS[name]}
    </svg>
  )
}

export function Logo({ size = 28, withName = true }) {
  return (
    <span className="inline-flex items-center gap-2.5">
      <svg width={size} height={size} viewBox="0 0 32 32" fill="none" stroke="#D4A537" strokeWidth="2.2" strokeLinejoin="round" strokeLinecap="round" aria-hidden="true">
        <path d="M16 2.5l11.7 6.75v13.5L16 29.5 4.3 22.75V9.25z" />
        <path d="M10.5 11.5h11M16 11.5v10" />
      </svg>
      {withName && <span className="font-display text-lg font-bold tracking-tight text-ink">Treadstone</span>}
    </span>
  )
}

export function Card({ children, className = '', as: Tag = 'section', ...props }) {
  return (
    <Tag className={`rounded-[18px] border border-line bg-card p-4 lg:rounded-card lg:p-6 ${className}`} {...props}>
      {children}
    </Tag>
  )
}

const BUTTON = {
  primary: 'bg-gold text-on-gold hover:bg-gold-hover font-bold',
  secondary: 'border border-control bg-transparent text-ink hover:bg-tile font-semibold',
  soft: 'bg-gold-chip text-gold-strong hover:bg-gold-tint-line font-bold',
  danger: 'bg-transparent text-negative hover:bg-negative-bg font-bold',
}

export function Button({ children, variant = 'primary', size = 'md', className = '', ...props }) {
  const h = size === 'lg' ? 'min-h-14 px-5 text-base rounded-[14px]' : size === 'sm' ? 'min-h-11 px-4 text-sm rounded-[10px]' : 'min-h-12 px-5 text-[15px] rounded-control'
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 transition-colors disabled:cursor-not-allowed disabled:bg-track disabled:text-ink-2 disabled:border-transparent ${h} ${BUTTON[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}

export function LinkButton({ children, variant = 'primary', className = '', href }) {
  return (
    <a href={href} className={`inline-flex min-h-12 items-center justify-center gap-2 rounded-control px-5 text-[15px] no-underline transition-colors ${BUTTON[variant]} ${className}`}>
      {children}
    </a>
  )
}

export function IconButton({ label, icon, onClick, href }) {
  const cls = 'inline-flex h-11 w-11 items-center justify-center rounded-control border border-line bg-card text-ink hover:bg-tile'
  if (href) return <a href={href} aria-label={label} className={cls}><Icon name={icon} /></a>
  return <button type="button" aria-label={label} onClick={onClick} className={cls}><Icon name={icon} /></button>
}

const CHIP = {
  positive: 'bg-positive-bg text-positive',
  gold: 'bg-gold-chip text-gold-strong',
  neutral: 'bg-track text-ink-2',
  info: 'bg-info-bg text-info',
  negative: 'bg-negative-bg text-negative',
}

export function Chip({ children, tone = 'neutral', className = '' }) {
  return <span className={`inline-flex h-[26px] items-center whitespace-nowrap rounded-full px-2.5 text-xs font-bold ${CHIP[tone]} ${className}`}>{children}</span>
}

const STATUS = {
  COMPLETED: ['positive', 'Paid'],
  ACTIVE: ['positive', 'Active'],
  REPAID: ['neutral', 'Repaid'],
  VERIFIED: ['positive', 'Verified'],
  PENDING: ['gold', 'Pending'],
  OPEN: ['gold', 'Waiting for members'],
  FAILED: ['negative', 'Failed'],
  REJECTED: ['negative', 'Rejected'],
  CLOSED: ['neutral', 'Cycle closed'],
}

export function StatusChip({ value, label }) {
  const [tone, text] = STATUS[value] || ['neutral', value]
  return <Chip tone={tone}>{label || text}</Chip>
}

export function Segmented({ options, value, onChange, label, className = '' }) {
  return (
    <div role="group" aria-label={label} className={`inline-grid auto-cols-fr grid-flow-col gap-[3px] rounded-[11px] border border-line bg-inset p-[3px] ${className}`}>
      {options.map((o) => (
        <button key={o.value} type="button" aria-pressed={value === o.value} onClick={() => onChange(o.value)}
          className={`min-h-11 rounded-lg px-3.5 text-sm transition-colors ${value === o.value ? 'bg-gold font-bold text-on-gold' : 'font-semibold text-ink-2 hover:text-ink'}`}>
          {o.label}
        </button>
      ))}
    </div>
  )
}

export function ChoiceChips({ options, value, onChange, label, columns = options.length, mono = false }) {
  return (
    <div role="radiogroup" aria-label={label} className="grid gap-2" style={{ gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` }}>
      {options.map((o) => {
        const on = value === o.value
        return (
          <button key={o.value} type="button" role="radio" aria-checked={on} onClick={() => onChange(o.value)}
            className={`flex min-h-12 items-center justify-center gap-2 rounded-control px-2 text-[15px] ${mono ? 'num' : ''} ${on ? 'border-2 border-gold bg-gold-tint font-bold text-gold-strong' : 'border border-control bg-card font-semibold text-ink'}`}>
            {o.dot && <span className={`h-2.5 w-2.5 rounded-full ${o.dot}`} />}
            {o.label}
          </button>
        )
      })}
    </div>
  )
}

const inputCls = 'min-h-[52px] w-full min-w-0 rounded-control border border-control bg-card px-3.5 text-base text-ink placeholder:text-disabled focus:border-gold focus:outline-none focus:ring-2 focus:ring-gold-tint-line'

export function Field({ label, hint, mono = false, prefix, ...props }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-[13px] font-semibold text-ink-2">{label}</span>
      {prefix ? (
        <span className="flex min-h-[52px] items-stretch overflow-hidden rounded-control border border-control bg-card focus-within:border-gold focus-within:ring-2 focus-within:ring-gold-tint-line">
          <span className="num flex items-center border-r border-line bg-tile px-3 text-base font-semibold text-ink-2">{prefix}</span>
          <input className={`min-w-0 flex-1 bg-transparent px-3 text-lg font-semibold text-ink outline-none ${mono ? 'num' : ''}`} {...props} />
        </span>
      ) : props.children ? (
        <select className={`${inputCls} ${mono ? 'num' : ''}`} {...props} />
      ) : (
        <input className={`${inputCls} ${mono ? 'num text-lg font-semibold' : 'font-semibold'}`} {...props} />
      )}
      {hint && <span className="text-[13px] font-medium text-ink-3">{hint}</span>}
    </label>
  )
}

export function Alert({ kind = 'error', children }) {
  if (!children) return null
  const styles = {
    error: 'border-negative/30 bg-negative-bg text-negative',
    success: 'border-positive/30 bg-positive-bg text-positive',
    info: 'border-gold-tint-line bg-gold-tint text-gold-muted',
  }
  return <div role={kind === 'error' ? 'alert' : 'status'} className={`rounded-control border px-3.5 py-2.5 text-sm font-semibold ${styles[kind]}`}>{children}</div>
}

export function StatTile({ label, value, sub, gold = false, valueClass = '' }) {
  return (
    <div className={`flex min-w-0 flex-col gap-1 rounded-tile p-3.5 lg:p-4 ${gold ? 'border border-gold-tint-line bg-gold-tint' : 'bg-tile'}`}>
      <span className={`text-xs font-medium lg:text-[13px] ${gold ? 'text-gold-muted' : 'text-ink-3'}`}>{label}</span>
      <span className={`num truncate text-base font-semibold lg:text-xl ${gold ? 'text-gold-strong' : 'text-ink'} ${valueClass}`}>{value}</span>
      {sub && <span className={`text-xs ${gold ? 'text-gold-muted' : 'text-ink-3'}`}>{sub}</span>}
    </div>
  )
}

// Line chart for prices. `points` are numbers (display geometry only; never used for money maths).
export function PriceChart({ points, height = 120, area = true, tone = 'gold', className = '' }) {
  if (!points || points.length < 2) {
    return <div className={`flex items-center justify-center rounded-tile bg-tile text-xs text-ink-3 ${className}`} style={{ height }}>Not enough price history yet</div>
  }
  const w = 300
  const min = Math.min(...points)
  const max = Math.max(...points)
  const span = max - min || 1
  const xy = points.map((p, i) => [(i / (points.length - 1)) * w, height - 6 - ((p - min) / span) * (height - 12)])
  const line = xy.map(([x, y], i) => `${i ? 'L' : 'M'}${x.toFixed(1)} ${y.toFixed(1)}`).join(' ')
  const stroke = tone === 'gold' ? '#D4A537' : tone === 'up' ? '#1E7A47' : '#B4570F'
  const id = `fill-${tone}-${points.length}`
  return (
    <svg viewBox={`0 0 ${w} ${height}`} preserveAspectRatio="none" className={`block w-full ${className}`} style={{ height }} aria-hidden="true">
      {area && (
        <>
          <defs>
            <linearGradient id={id} x1="0" x2="0" y1="0" y2="1">
              <stop offset="0%" stopColor="#D4A537" stopOpacity="0.3" />
              <stop offset="100%" stopColor="#D4A537" stopOpacity="0" />
            </linearGradient>
          </defs>
          <path d={`${line} L${w} ${height} L0 ${height} Z`} fill={`url(#${id})`} />
        </>
      )}
      <path d={line} fill="none" stroke={stroke} strokeWidth={area ? 2.5 : 2} vectorEffect="non-scaling-stroke" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  )
}

// Price move with arrow and sign; `pct` is the server's decimal string, else derived from points.
export function PriceChange({ points, pct, suffix = '' }) {
  let value = pct
  if (value === undefined || value === null) {
    if (!points || points.length < 2 || !points[0]) return null
    value = (((points[points.length - 1] - points[0]) / points[0]) * 100).toFixed(2)
  }
  const up = !String(value).startsWith('-')
  return (
    <span className={`num text-xs font-semibold ${up ? 'text-positive' : 'text-negative'}`}>
      {up ? '▲' : '▼'} {String(value).replace('-', '')}%{suffix}
    </span>
  )
}

export function Switch({ checked, onChange, label, sub, disabled }) {
  return (
    <div className="flex min-h-14 items-center justify-between gap-4 py-2">
      <span className="flex flex-col">
        <span id={`sw-${label}`} className="text-[15px] font-semibold">{label}</span>
        {sub && <span className="text-[13px] text-ink-3">{sub}</span>}
      </span>
      <button type="button" role="switch" aria-checked={checked} aria-labelledby={`sw-${label}`} disabled={disabled}
        onClick={() => onChange(!checked)}
        className={`relative h-8 w-[52px] shrink-0 rounded-full transition-colors disabled:opacity-50 ${checked ? 'bg-gold' : 'bg-control'}`}>
        <span className={`absolute top-1 h-6 w-6 rounded-full bg-card shadow-sm transition-all ${checked ? 'left-[24px]' : 'left-1'}`} />
      </button>
    </div>
  )
}

export function Bell({ unread }) {
  return (
    <a href="#/notifications" aria-label={unread ? `Notifications, ${unread} unread` : 'Notifications'}
      className="relative inline-flex h-11 w-11 items-center justify-center rounded-control border border-line bg-card text-ink no-underline hover:bg-tile">
      <Icon name="bell" />
      {unread > 0 && (
        <span className="num absolute -right-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-gold px-1 text-[11px] font-bold text-on-gold">
          {unread > 9 ? '9+' : unread}
        </span>
      )}
    </a>
  )
}

export function Loading({ label = 'Loading…' }) {
  return <p className="py-10 text-center text-sm text-ink-3">{label}</p>
}

export function PageTitle({ title, sub, back, actions }) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-3">
      <div className="flex min-w-0 items-center gap-3">
        {back && <IconButton label="Back" icon="back" href={back} />}
        <div className="min-w-0">
          <h1 className="truncate font-display text-xl font-semibold tracking-tight lg:text-3xl">{title}</h1>
          {sub && <p className="mt-0.5 text-sm text-ink-3">{sub}</p>}
        </div>
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </header>
  )
}

export function Avatar({ text, me = false, size = 36 }) {
  return (
    <span className={`inline-flex shrink-0 items-center justify-center rounded-full text-[13px] font-bold ${me ? 'bg-gold-chip text-gold-text' : 'bg-track text-ink-2'}`} style={{ width: size, height: size }}>
      {text}
    </span>
  )
}
