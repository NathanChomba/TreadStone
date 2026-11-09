import { useState } from 'react'
import { METAL, api, kwacha } from '../api'
import { go, useAction, useApi } from '../hooks'
import { Alert, Button, Card, ChoiceChips, Chip, Field, Icon, Loading, PageTitle, StatusChip } from '../ui'

const AMOUNTS = ['200', '500', '1000']

function RadioCard({ checked, onClick, title, body }) {
  return (
    <button type="button" role="radio" aria-checked={checked} onClick={onClick}
      className={`flex items-start gap-3 rounded-[14px] p-3.5 text-left ${checked ? 'border-2 border-gold bg-gold-tint' : 'border border-control bg-card'}`}>
      <span className={`mt-0.5 h-5 w-5 shrink-0 rounded-full bg-card ${checked ? 'border-[6px] border-gold' : 'border-2 border-disabled'}`} />
      <span className="flex flex-col gap-0.5">
        <span className="text-[15px] font-bold">{title}</span>
        <span className="text-[13px] leading-snug text-ink-2">{body}</span>
      </span>
    </button>
  )
}

function CreateForm({ online }) {
  const [form, setForm] = useState({ name: '', group_type: 'ROTATING', metal: 'XAU', amount: '500', other: '', frequency: 'MONTHLY', max_members: 12 })
  const action = useAction()
  const set = (k, v) => setForm({ ...form, [k]: v })
  const amount = form.amount === 'other' ? form.other : form.amount
  const rotating = form.group_type === 'ROTATING'

  async function submit(e) {
    e.preventDefault()
    const body = {
      name: form.name, group_type: form.group_type, metal: form.metal, frequency: form.frequency,
      contribution_amount: amount, max_members: Number(form.max_members),
    }
    const g = await action.run(() => api('/groups/', { method: 'POST', body }))
    if (g) go(`/groups/${g.id}`)
  }

  return (
    <form onSubmit={submit} className="flex flex-col gap-[18px]">
      <Field label="Group name" placeholder="e.g. Kalingalinga Circle" value={form.name} onChange={(e) => set('name', e.target.value)} required />
      <div role="radiogroup" aria-label="How it pays out" className="flex flex-col gap-2">
        <span className="text-[13px] font-semibold text-ink-2">How it pays out</span>
        <RadioCard checked={rotating} onClick={() => set('group_type', 'ROTATING')} title="Take turns (chilimba)"
          body="Everyone pays the same each cycle. One member gets the whole pot each cycle, in joining order." />
        <RadioCard checked={!rotating} onClick={() => set('group_type', 'ANNUITY')} title="Save for later (annuity)"
          body="Each member builds their own gold and draws it down later. You can borrow against it." />
      </div>
      <div className="flex flex-col gap-2">
        <span className="text-[13px] font-semibold text-ink-2">Hold savings in</span>
        <ChoiceChips label="Metal" value={form.metal} onChange={(v) => set('metal', v)}
          options={[{ value: 'XAU', label: 'Gold', dot: 'bg-gold' }, { value: 'XAG', label: 'Silver', dot: 'bg-silver' }]} />
      </div>
      <div className="flex flex-col gap-2">
        <span className="text-[13px] font-semibold text-ink-2">{rotating ? 'Each member pays' : 'Minimum deposit'}</span>
        <ChoiceChips label="Amount" mono columns={4} value={form.amount} onChange={(v) => set('amount', v)}
          options={[...AMOUNTS.map((a) => ({ value: a, label: kwacha(a).replace('.00', '') })), { value: 'other', label: 'Other' }]} />
        {form.amount === 'other' && (
          <Field label="Amount (ZMW)" mono type="number" inputMode="decimal" min="10" step="0.01" value={form.other} onChange={(e) => set('other', e.target.value)} required />
        )}
      </div>
      <div className="grid grid-cols-2 gap-3">
        <Field label="How often" value={form.frequency} onChange={(e) => set('frequency', e.target.value)}>
          <option value="MONTHLY">Monthly</option>
          <option value="WEEKLY">Weekly</option>
        </Field>
        <div className="flex flex-col gap-1.5">
          <span className="text-[13px] font-semibold text-ink-2">Members</span>
          <span className="flex items-center gap-1.5">
            <button type="button" aria-label="Fewer members" onClick={() => set('max_members', Math.max(2, form.max_members - 1))}
              className="h-[52px] w-11 rounded-control border border-control bg-card text-xl font-semibold">−</button>
            <span className="num flex-1 text-center text-xl font-semibold" aria-live="polite">{form.max_members}</span>
            <button type="button" aria-label="More members" onClick={() => set('max_members', Math.min(100, form.max_members + 1))}
              className="h-[52px] w-11 rounded-control border border-control bg-card text-xl font-semibold">+</button>
          </span>
        </div>
      </div>
      {rotating && amount && (
        <div className="flex flex-col gap-1 rounded-2xl border border-gold-tint-line bg-gold-tint p-4">
          <span className="text-xs font-semibold uppercase tracking-[0.08em] text-gold-muted">Each cycle's pot</span>
          <span className="num text-2xl font-semibold text-gold-strong">{kwacha((Number(amount) * form.max_members).toFixed(2))}</span>
          <span className="text-[13px] leading-snug text-gold-muted">{form.max_members} × {kwacha(Number(amount).toFixed(2))}, held as {METAL[form.metal].toLowerCase()} until it's paid out. A 1% custody fee applies when metal is bought and sold.</span>
        </div>
      )}
      <Alert>{action.error}</Alert>
      <Button type="submit" size="lg" disabled={!online || action.busy}>{action.busy ? 'Creating…' : 'Create group'}</Button>
      <p className="text-center text-[13px] text-ink-3">You become the admin. Share the invite code, then start the group once everyone has joined.</p>
    </form>
  )
}

export default function Groups({ online }) {
  const { data, loading, error } = useApi('/groups/')
  const [code, setCode] = useState('')
  const [creating, setCreating] = useState(false)
  const join = useAction()
  const groups = data?.results || []

  async function submitJoin(e) {
    e.preventDefault()
    const g = await join.run(() => api('/groups/join/', { method: 'POST', body: { invite_code: code } }))
    if (g) go(`/groups/${g.id}`)
  }

  return (
    <>
      <PageTitle title="Savings groups" sub="Your circles, and the gold they hold" />

      <div className="flex flex-wrap items-start gap-[18px] lg:gap-6">
        <div className="flex min-w-0 flex-[2_1_480px] flex-col gap-3">
          {loading && !data && <Loading />}
          {error && !data && <Alert>{error.message}</Alert>}
          {data && groups.length === 0 && <Card><p className="text-ink-3">No groups yet. Join one with a code or create your own.</p></Card>}
          {groups.map((g) => (
            <a key={g.id} href={`#/groups/${g.id}`} className="block text-ink no-underline">
              <Card className="flex items-center justify-between gap-3 transition-colors hover:border-gold-tint-line">
                <span className="flex min-w-0 flex-col gap-1.5">
                  <span className="font-display text-[17px] font-semibold">{g.name}</span>
                  <span className="flex flex-wrap gap-1.5">
                    <StatusChip value={g.status} />
                    <Chip tone="gold">{g.group_type === 'ANNUITY' ? 'Annuity' : 'Tontine'} · {METAL[g.metal]}</Chip>
                  </span>
                </span>
                <span className="flex items-center gap-3 text-right">
                  <span className="flex flex-col">
                    <span className="num font-semibold">{kwacha(g.contribution_amount)}</span>
                    <span className="text-xs text-ink-3">{g.frequency.toLowerCase()} · {g.member_count}/{g.max_members}</span>
                  </span>
                  <Icon name="chevron" className="text-ink-3" />
                </span>
              </Card>
            </a>
          ))}
        </div>

        <div className="flex min-w-0 flex-[1_1_340px] flex-col gap-[18px] lg:gap-6">
          <Card className="flex flex-col gap-3">
            <div>
              <h2 className="font-display text-[17px] font-semibold">Have an invite code?</h2>
              <p className="text-sm text-ink-2">Ask your group's admin for it.</p>
            </div>
            <form onSubmit={submitJoin} className="flex gap-2">
              <label className="min-w-0 flex-1">
                <span className="sr-only">Invite code</span>
                <input value={code} onChange={(e) => setCode(e.target.value.toUpperCase())} placeholder="4F9A21BC" required
                  className="num min-h-[52px] w-full rounded-control border border-control bg-card px-3.5 text-[17px] font-semibold uppercase tracking-[0.12em] outline-none focus:border-gold focus:ring-2 focus:ring-gold-tint-line" />
              </label>
              <Button type="submit" variant="secondary" disabled={!online || join.busy}>Join</Button>
            </form>
            <Alert>{join.error}</Alert>
          </Card>

          <Card className="flex flex-col gap-4">
            <button type="button" aria-expanded={creating} onClick={() => setCreating(!creating)} className="flex min-h-11 items-center justify-between text-left">
              <span>
                <span className="block font-display text-[17px] font-semibold">Create your own group</span>
                <span className="block text-sm text-ink-2">You'll be its admin</span>
              </span>
              <Icon name="chevron" className={`text-ink-3 transition-transform ${creating ? 'rotate-90' : ''}`} />
            </button>
            {creating && <CreateForm online={online} />}
          </Card>
        </div>
      </div>
    </>
  )
}
