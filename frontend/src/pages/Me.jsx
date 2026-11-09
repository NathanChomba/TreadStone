import { useState } from 'react'
import { api, initials, localPhone, toE164 } from '../api'
import { useAction, useApi } from '../hooks'
import { Alert, Avatar, Button, Card, ChoiceChips, Chip, Field, Icon, Loading, PageTitle, Switch } from '../ui'

const KYC = {
  VERIFIED: ['positive', '✓ KYC verified'],
  PENDING: ['gold', 'KYC pending'],
  REJECTED: ['negative', 'KYC rejected'],
}

const PROVIDERS = [
  { value: 'MTN', label: 'MTN' },
  { value: 'AIRTEL', label: 'Airtel' },
  { value: 'ZAMTEL', label: 'Zamtel' },
]

function guessProvider(local) {
  const d = local.replace(/\D/g, '').replace(/^260/, '0')
  if (/^0?(96|76)/.test(d)) return 'MTN'
  if (/^0?(97|77)/.test(d)) return 'AIRTEL'
  if (/^0?95/.test(d)) return 'ZAMTEL'
  return null
}

function Wallets({ online }) {
  const { data, reload } = useApi('/auth/wallets/')
  const [adding, setAdding] = useState(false)
  const [number, setNumber] = useState('')
  const [provider, setProvider] = useState(null)
  const action = useAction()

  async function act(fn, msg) {
    const r = await action.run(fn, msg)
    reload()
    return r
  }

  async function add(e) {
    e.preventDefault()
    const r = await act(() => api('/auth/wallets/', { method: 'POST', body: { number: toE164(number), provider: provider || guessProvider(number) || 'MTN' } }), 'Number added.')
    if (r) {
      setNumber('')
      setProvider(null)
      setAdding(false)
    }
  }

  return (
    <Card className="flex flex-col gap-1">
      <span className="eyebrow mb-1">Mobile money numbers</span>
      {(data || []).map((w) => (
        <div key={w.id} className="flex flex-wrap items-center justify-between gap-3 border-t border-track py-3 first:border-t-0">
          <span className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-control bg-tile text-ink-2"><Icon name="phone" /></span>
            <span>
              <span className="block font-semibold">{w.provider_name}</span>
              <span className="num block text-sm text-ink-2">{localPhone(w.number)}</span>
            </span>
          </span>
          {w.is_default ? <Chip tone="gold">Default</Chip> : (
            <span className="flex gap-1">
              <Button variant="soft" size="sm" disabled={!online || action.busy}
                onClick={() => act(() => api(`/auth/wallets/${w.id}/default/`, { method: 'POST' }), `${localPhone(w.number)} is now your default.`)}>Make default</Button>
              <Button variant="danger" size="sm" disabled={!online || action.busy} aria-label={`Remove ${localPhone(w.number)}`}
                onClick={() => act(() => api(`/auth/wallets/${w.id}/`, { method: 'DELETE' }), 'Number removed.')}>Remove</Button>
            </span>
          )}
        </div>
      ))}
      <p className="pb-2 text-[13px] text-ink-3">Payouts and loans are sent to your default number. You pick which number to pay from each time.</p>
      <Alert kind="success">{action.success}</Alert>
      <Alert>{action.error}</Alert>
      {adding ? (
        <form onSubmit={add} className="flex flex-col gap-3 border-t border-track pt-3">
          <Field label="Number" prefix="+260" mono type="tel" inputMode="tel" placeholder="096 765 4321" value={number}
            onChange={(e) => { setNumber(e.target.value); setProvider(null) }} required />
          <ChoiceChips label="Network" value={provider || guessProvider(number)} onChange={setProvider} options={PROVIDERS} />
          <div className="grid grid-cols-2 gap-3">
            <Button type="button" variant="secondary" onClick={() => setAdding(false)}>Cancel</Button>
            <Button type="submit" disabled={!online || action.busy}>Add number</Button>
          </div>
        </form>
      ) : (
        <button type="button" onClick={() => setAdding(true)} className="flex min-h-11 items-center gap-2 border-t border-track pt-2 text-sm font-bold text-gold-text">
          <Icon name="plus" size={18} />Add a number
        </button>
      )}
    </Card>
  )
}

function PasswordForm({ online }) {
  const [open, setOpen] = useState(false)
  const [form, setForm] = useState({ current: '', next: '' })
  const action = useAction()
  async function submit(e) {
    e.preventDefault()
    const r = await action.run(() => api('/auth/password/', { method: 'POST', body: { current: form.current, new: form.next } }), 'Password changed.')
    if (r) {
      setForm({ current: '', next: '' })
      setOpen(false)
    }
  }
  return (
    <div className="border-t border-track pt-1">
      <button type="button" aria-expanded={open} onClick={() => setOpen(!open)} className="flex min-h-12 w-full items-center justify-between text-left font-semibold">
        Change password <Icon name="chevron" size={18} className={`text-ink-3 transition-transform ${open ? 'rotate-90' : ''}`} />
      </button>
      <Alert kind="success">{action.success}</Alert>
      {open && (
        <form onSubmit={submit} className="flex flex-col gap-3 pb-2">
          <Field label="Current password" type="password" autoComplete="current-password" value={form.current} onChange={(e) => setForm({ ...form, current: e.target.value })} required />
          <Field label="New password" type="password" autoComplete="new-password" hint="At least 8 characters." value={form.next} onChange={(e) => setForm({ ...form, next: e.target.value })} required />
          <Alert>{action.error}</Alert>
          <Button type="submit" disabled={!online || action.busy}>Save new password</Button>
        </form>
      )}
    </div>
  )
}

export default function Me({ member, setMember, online, logout }) {
  const [nrc, setNrc] = useState(member?.nrc_number || '')
  const kyc = useAction()
  const prefs = useAction()

  if (!member) return <Loading />
  const [tone, label] = KYC[member.kyc_status] || KYC.PENDING

  async function saveNrc(e) {
    e.preventDefault()
    const m = await kyc.run(() => api('/auth/me/', { method: 'PATCH', body: { nrc_number: nrc } }),
      'Saved. A Treadstone officer will check it, usually within one working day.')
    if (m) setMember(m)
  }

  async function savePref(field, value) {
    const m = await prefs.run(() => api('/auth/me/', { method: 'PATCH', body: { [field]: value } }))
    if (m) setMember(m)
  }

  return (
    <>
      <PageTitle title="Profile & settings" />

      <div className="flex flex-wrap items-start gap-[18px] lg:gap-6">
        <div className="flex min-w-0 flex-[1_1_380px] flex-col gap-[18px] lg:gap-6">
          <Card className="flex items-center gap-4">
            <Avatar text={initials(member.first_name, member.last_name)} me size={60} />
            <span className="flex min-w-0 flex-col gap-1">
              <span className="truncate font-display text-xl font-semibold">{member.first_name} {member.last_name}</span>
              <span className="num text-[13px] text-ink-3">Member TS-{String(member.id).padStart(7, '0')} · {localPhone(member.phone)}</span>
              <span><Chip tone={tone}>{label}</Chip></span>
            </span>
          </Card>

          <Wallets online={online} />

          <Card className="flex flex-col gap-3">
            <h2 className="font-display text-[17px] font-semibold">Identity (KYC)</h2>
            {member.kyc_status === 'VERIFIED' ? (
              <p className="text-sm text-ink-2">Your NRC <span className="num font-semibold text-ink">{member.nrc_number || ''}</span> is verified. You can borrow against your gold and receive payouts.</p>
            ) : (
              <form onSubmit={saveNrc} className="flex flex-col gap-3">
                <p className="text-sm text-ink-2">
                  {member.kyc_status === 'REJECTED'
                    ? 'Your last check did not pass. Check the number on your card and send it again.'
                    : 'You can save without it. We need your NRC before you can borrow or receive a payout.'}
                </p>
                <Field label="NRC number" mono placeholder="123456/78/1" value={nrc} onChange={(e) => setNrc(e.target.value)}
                  hint="As printed on the card: six digits / two / one." required />
                <Alert kind="success">{kyc.success}</Alert>
                <Alert>{kyc.error}</Alert>
                <Button type="submit" disabled={!online || kyc.busy}>Submit for checking</Button>
              </form>
            )}
          </Card>
        </div>

        <div className="flex min-w-0 flex-[1_1_380px] flex-col gap-[18px] lg:gap-6">
          <Card className="flex flex-col">
            <span className="eyebrow mb-1">Security & alerts</span>
            <Switch label="SMS reminders" sub="Two days before each due date" checked={member.sms_reminders}
              disabled={!online || prefs.busy} onChange={(v) => savePref('sms_reminders', v)} />
            <div className="border-t border-track" />
            <Switch label="Gold price alerts" sub="When gold moves 3% or more in a day" checked={member.price_alerts}
              disabled={!online || prefs.busy} onChange={(v) => savePref('price_alerts', v)} />
            <PasswordForm online={online} />
            <Alert>{prefs.error}</Alert>
          </Card>

          <Card className="flex flex-col gap-3">
            <span className="eyebrow">Language</span>
            <ChoiceChips label="Language" value={member.language} onChange={(v) => savePref('language', v)}
              options={[{ value: 'en', label: 'English' }, { value: 'bem', label: 'Bemba' }, { value: 'nya', label: 'Nyanja' }]} />
            {member.language !== 'en' && (
              <p className="text-[13px] text-ink-3">Saved. Screens are still in English while the Bemba and Nyanja wording is checked by fluent speakers.</p>
            )}
          </Card>

          <Card className="!py-2">
            <button type="button" onClick={logout} className="flex min-h-12 w-full items-center gap-3 text-left font-bold text-negative">
              <Icon name="logout" />Sign out
            </button>
          </Card>
        </div>
      </div>
    </>
  )
}
