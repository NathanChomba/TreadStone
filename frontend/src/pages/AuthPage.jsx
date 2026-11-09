import { useState } from 'react'
import { api, perGram, toE164 } from '../api'
import { useAction, usePrice } from '../hooks'
import { Alert, Button, Field, Icon, Logo, PriceChange, PriceChart, Segmented } from '../ui'

export default function AuthPage({ onAuth }) {
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ phone: '', password: '', first_name: '', last_name: '' })
  const [showPassword, setShowPassword] = useState(false)
  const { busy, error, run } = useAction()
  const gold = usePrice('XAU')
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  async function submit(e) {
    e.preventDefault()
    const phone = toE164(form.phone)
    const body = mode === 'login' ? { phone, password: form.password } : { ...form, phone }
    const result = await run(() => api(`/auth/${mode === 'login' ? 'login' : 'register'}/`, { method: 'POST', body }))
    if (result) onAuth(result)
  }

  return (
    <div className="flex min-h-svh flex-wrap bg-page">
      {/* Desktop-only story panel */}
      <aside className="hidden flex-[1_1_420px] flex-col justify-between gap-10 border-r border-line bg-card p-12 lg:flex">
        <Logo size={32} />
        <div className="flex max-w-md flex-col gap-5">
          <h2 className="font-display text-4xl font-semibold leading-tight tracking-tight">Save with your group.<br />Keep it in gold.</h2>
          <p className="text-base leading-relaxed text-ink-2">Every contribution is turned into gold held by a custodian, so what you get back keeps its value when the kwacha falls.</p>
          {gold.current && (
            <div className="flex flex-col gap-3 rounded-card border border-gold-tint-line bg-gold-tint p-5">
              <div className="flex items-baseline justify-between">
                <span className="text-sm font-semibold text-gold-muted">Gold today</span>
                <PriceChange pct={gold.changePct} suffix=" this month" />
              </div>
              <span className="num text-3xl font-semibold">{perGram(gold.current.price_per_gram)}</span>
              <PriceChart points={gold.points} height={70} />
            </div>
          )}
        </div>
        <p className="text-[13px] text-ink-3">Gold held by Zambia Gold Company Ltd. Simulated for this prototype.</p>
      </aside>

      <div className="flex flex-[1_1_380px] items-center justify-center px-4 py-8">
        <div className="flex w-full max-w-[400px] flex-col gap-6">
          <div className="lg:hidden"><Logo /></div>
          <div className="flex flex-col gap-2 lg:hidden">
            <h1 className="font-display text-2xl font-semibold leading-tight tracking-tight">Save with your group.<br />Keep it in gold.</h1>
            <p className="text-[15px] leading-relaxed text-ink-2">Your contributions become gold, so they keep their value when the kwacha falls.</p>
          </div>
          {gold.current && (
            <div className="flex items-center gap-3 rounded-2xl border border-gold-tint-line bg-gold-tint px-3.5 py-3 lg:hidden">
              <span className="flex flex-1 flex-col">
                <span className="text-xs font-semibold text-gold-muted">Gold today</span>
                <span className="num text-lg font-semibold">{perGram(gold.current.price_per_gram)}</span>
              </span>
              <PriceChart points={gold.points} height={30} area={false} tone="up" className="!w-20" />
              <PriceChange pct={gold.changePct} suffix=" this month" />
            </div>
          )}
          <h1 className="hidden font-display text-3xl font-semibold tracking-tight lg:block">{mode === 'login' ? 'Welcome back' : 'Create your account'}</h1>

          <Segmented label="Log in or create an account" className="w-full"
            options={[{ value: 'login', label: 'Log in' }, { value: 'register', label: 'Create account' }]}
            value={mode} onChange={setMode} />

          <form onSubmit={submit} className="flex flex-col gap-4">
            {mode === 'register' && (
              <div className="grid grid-cols-2 gap-3">
                <Field label="First name" autoComplete="given-name" value={form.first_name} onChange={set('first_name')} required />
                <Field label="Last name" autoComplete="family-name" value={form.last_name} onChange={set('last_name')} required />
              </div>
            )}
            <Field label="Mobile money number" prefix="+260" mono type="tel" inputMode="tel" autoComplete="tel-national"
              placeholder="097 123 4567" value={form.phone} onChange={set('phone')} required
              hint={mode === 'register' ? 'MTN, Airtel or Zamtel. Payouts are sent here.' : undefined} />
            <label className="flex flex-col gap-1.5">
              <span className="text-[13px] font-semibold text-ink-2">Password</span>
              <span className="flex min-h-[52px] items-center rounded-control border border-control bg-card focus-within:border-gold focus-within:ring-2 focus-within:ring-gold-tint-line">
                <input type={showPassword ? 'text' : 'password'} autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                  value={form.password} onChange={set('password')} required
                  className="min-w-0 flex-1 bg-transparent px-3.5 text-base font-semibold outline-none" />
                <button type="button" aria-label={showPassword ? 'Hide password' : 'Show password'} aria-pressed={showPassword}
                  onClick={() => setShowPassword(!showPassword)} className="mr-1 flex h-11 w-11 items-center justify-center text-ink-2">
                  <Icon name="eye" />
                </button>
              </span>
              {mode === 'register' && <span className="text-[13px] font-medium text-ink-3">At least 8 characters.</span>}
            </label>
            <Alert>{error}</Alert>
            <Button type="submit" size="lg" disabled={busy} className="mt-1 w-full">
              {busy ? 'Please wait…' : mode === 'login' ? 'Log in' : 'Create account'}
            </Button>
          </form>

          <div className="flex items-start gap-3 rounded-2xl border border-line bg-card px-4 py-3.5 lg:hidden">
            <Icon name="shield" className="mt-0.5 text-gold-text" />
            <p className="text-[13px] leading-snug text-ink-2">Gold is held by <b className="text-ink">Zambia Gold Company Ltd</b>. Simulated for this prototype.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
