import { useCallback, useEffect, useState } from 'react'
import { api, getToken, setToken, time24 } from './api'
import { go, useHashRoute, useOnline } from './hooks'
import AuthPage from './pages/AuthPage'
import Contribute from './pages/Contribute'
import Dashboard from './pages/Dashboard'
import GroupDetail from './pages/GroupDetail'
import Groups from './pages/Groups'
import Ledger from './pages/Ledger'
import Loans from './pages/Loans'
import Me from './pages/Me'
import Notifications from './pages/Notifications'
import Vault from './pages/Vault'
import { Icon, Logo } from './ui'

// Phone: 5 tabs. Desktop: the same plus Loans in the sidebar.
const NAV = [
  { path: '/', label: 'Home', long: 'Dashboard', icon: 'home' },
  { path: '/groups', label: 'Groups', long: 'Savings groups', icon: 'groups' },
  { path: '/vault', label: 'Vault', long: 'Vault & metals', icon: 'vault' },
  { path: '/loans', label: 'Loans', long: 'Loans', icon: 'loans', desktopOnly: true },
  { path: '/ledger', label: 'Ledger', long: 'Ledger & history', icon: 'ledger' },
  { path: '/me', label: 'Me', long: 'Profile & settings', icon: 'me' },
]

export default function App() {
  const route = useHashRoute()
  const online = useOnline()
  const [member, setMember] = useState(null)
  const [checking, setChecking] = useState(Boolean(getToken()))
  const [lastSync, setLastSync] = useState(null)
  const [unread, setUnread] = useState(0)

  const refreshUnread = useCallback(() => {
    if (!getToken()) return
    api('/auth/notifications/').then((d) => setUnread(d.unread)).catch(() => {})
  }, [])

  // Poll the bell once a minute while signed in.
  useEffect(() => {
    if (!member) return undefined
    refreshUnread()
    const t = setInterval(refreshUnread, 60000)
    return () => clearInterval(t)
  }, [member, refreshUnread])

  // Page language follows the member's setting (DESIGN.md section 10).
  useEffect(() => {
    document.documentElement.lang = member?.language || 'en'
  }, [member?.language])

  useEffect(() => {
    if (!getToken()) return
    api('/auth/me/')
      .then((m) => {
        setMember(m)
        setLastSync(new Date().toISOString())
      })
      .catch((e) => {
        if (e.status === 401) setToken(null)
      })
      .finally(() => setChecking(false))
  }, [])

  function onAuth({ token, member: m }) {
    setToken(token)
    setMember(m)
    go('/')
  }

  async function logout() {
    try {
      await api('/auth/logout/', { method: 'POST' })
    } catch {
      // signing out offline still clears this device
    }
    setToken(null)
    setMember(null)
    go('/')
  }

  if (checking) return <p className="p-10 text-center text-ink-3">Loading…</p>
  if (!getToken()) return <AuthPage onAuth={onAuth} />

  const groupMatch = route.match(/^\/groups\/(\d+)$/)
  const payMatch = route.match(/^\/contribute\/(\d+)$/)
  const ctx = { member, setMember, online, logout, unread, refreshUnread }
  let page
  if (payMatch) page = <Contribute groupId={payMatch[1]} {...ctx} />
  else if (groupMatch) page = <GroupDetail id={groupMatch[1]} {...ctx} />
  else if (route === '/notifications') page = <Notifications {...ctx} />
  else if (route === '/groups') page = <Groups {...ctx} />
  else if (route === '/vault') page = <Vault {...ctx} />
  else if (route === '/loans') page = <Loans {...ctx} />
  else if (route === '/ledger') page = <Ledger {...ctx} />
  else if (route === '/me') page = <Me {...ctx} />
  else page = <Dashboard {...ctx} />

  const active = groupMatch || payMatch ? '/groups' : route
  // Flows hide the tab bar and show a back button instead (DESIGN.md section 6).
  const inFlow = Boolean(payMatch)

  return (
    <div className="flex min-h-svh flex-wrap bg-page">
      {/* Desktop sidebar (DESIGN.md section 6) */}
      <aside className="hidden flex-[1_1_230px] flex-col gap-7 border-r border-line bg-card px-4 py-6 lg:flex lg:max-w-[260px]">
        <a href="#/" className="px-2"><Logo /></a>
        <nav aria-label="Main" className="flex flex-col gap-0.5">
          {NAV.map((n) => (
            <a key={n.path} href={`#${n.path}`} aria-current={active === n.path ? 'page' : undefined}
              className={`flex min-h-11 items-center gap-3 rounded-[10px] px-3 text-sm no-underline ${active === n.path ? 'bg-gold-chip font-bold text-gold-text' : 'font-semibold text-ink-2 hover:bg-tile hover:text-ink'}`}>
              <Icon name={n.icon} size={18} />
              {n.long}
            </a>
          ))}
        </nav>
        <div className="mt-auto flex flex-col gap-1 rounded-tile bg-tile p-3.5">
          <span className="eyebrow">Custodian</span>
          <span className="text-sm font-bold">Zambia Gold Company Ltd</span>
          <span className="text-[13px] text-ink-3">Simulated for this prototype</span>
        </div>
      </aside>

      <div className="flex min-w-0 flex-[999_1_560px] flex-col">
        {!online && (
          <div role="status" className="border-b border-gold-tint-line bg-gold-tint px-4 py-2.5 text-sm font-semibold text-gold-muted">
            You're offline. Showing what was saved{lastSync ? ` at ${time24(lastSync)}` : ''}. Payments are off until you reconnect.
          </div>
        )}
        <main className="mx-auto flex w-full max-w-[1200px] flex-col gap-[18px] px-4 pb-28 pt-5 lg:gap-6 lg:px-[clamp(16px,3vw,44px)] lg:pb-12 lg:pt-8">
          {page}
        </main>
      </div>

      {/* Phone tab bar */}
      <nav aria-label="Main" className={`fixed inset-x-0 bottom-0 z-20 border-t border-line bg-card lg:hidden ${inFlow ? 'hidden' : ''}`}>
        <div className="mx-auto grid max-w-xl grid-cols-5 pb-[env(safe-area-inset-bottom)]">
          {NAV.filter((n) => !n.desktopOnly).map((n) => (
            <a key={n.path} href={`#${n.path}`} aria-current={active === n.path ? 'page' : undefined}
              className={`flex min-h-14 flex-col items-center justify-center gap-0.5 text-[11px] no-underline ${active === n.path ? 'font-bold text-gold-text' : 'font-semibold text-ink-2'}`}>
              <Icon name={n.icon} size={22} />
              {n.label}
            </a>
          ))}
        </div>
      </nav>
    </div>
  )
}
