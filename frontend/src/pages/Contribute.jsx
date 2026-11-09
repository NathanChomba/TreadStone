import { useState } from 'react'
import { METAL, api, fullDate, grams, kwacha, localPhone, perGram } from '../api'
import { useAction, useApi } from '../hooks'
import { Alert, Button, Card, ChoiceChips, Field, Icon, LinkButton, Loading, PageTitle } from '../ui'

const STEPS = ['Amount', 'Pay from', 'Review', 'Done']

function Steps({ step }) {
  return (
    <ol className="grid grid-cols-4 gap-1.5" aria-label="Progress">
      {STEPS.map((label, i) => (
        <li key={label} className="flex flex-col gap-1.5" aria-current={i === step ? 'step' : undefined}>
          <span className={`h-1.5 rounded-full ${i <= step ? 'bg-gold' : 'bg-track'}`} />
          <span className={`text-[11px] font-semibold ${i === step ? 'text-gold-text' : 'text-ink-3'}`}>{label}</span>
        </li>
      ))}
    </ol>
  )
}

function Row({ k, v, mono = true }) {
  return (
    <div className="flex justify-between gap-3 border-t border-track py-3 first:border-t-0">
      <span className="text-sm text-ink-3">{k}</span>
      <span className={`text-right font-semibold ${mono ? 'num' : ''}`}>{v}</span>
    </div>
  )
}

export default function Contribute({ groupId, online, refreshUnread }) {
  const group = useApi(`/groups/${groupId}/`)
  const wallets = useApi('/auth/wallets/')
  const [step, setStep] = useState(0)
  const [choice, setChoice] = useState(null)
  const [custom, setCustom] = useState('')
  const [walletId, setWalletId] = useState(null)
  const [quote, setQuote] = useState(null)
  const [result, setResult] = useState(null)
  const action = useAction()

  if ((group.loading && !group.data) || (wallets.loading && !wallets.data)) return <Loading />
  if (group.error && !group.data) return <Alert>{group.error.message}</Alert>

  const g = group.data
  const rotating = g.group_type === 'ROTATING'
  const min = g.contribution_amount
  const presets = rotating ? [min] : [min, (Number(min) * 2).toFixed(2), (Number(min) * 5).toFixed(2)]
  const amount = rotating ? min : choice === 'other' ? custom : choice || min
  const list = wallets.data || []
  const wallet = list.find((w) => w.id === walletId) || list.find((w) => w.is_default) || list[0]
  const metal = METAL[g.metal].toLowerCase()

  async function toReview() {
    const q = await action.run(() => api(`/metals/quote/?metal=${g.metal}&amount=${amount}`))
    if (q) {
      setQuote(q)
      setStep(2)
    }
  }

  async function pay() {
    const c = await action.run(() => api('/contributions/', { method: 'POST', body: { group: g.id, amount, wallet: wallet?.id } }))
    if (c) {
      setResult(c)
      setStep(3)
      refreshUnread?.()
    }
  }

  if (g.status !== 'ACTIVE') {
    return (
      <>
        <PageTitle back={`#/groups/${g.id}`} title={`Pay for ${g.name}`} />
        <Alert kind="info">This group isn't taking payments right now.</Alert>
      </>
    )
  }
  if (rotating && g.paid_this_period && step < 3) {
    return (
      <>
        <PageTitle back={`#/groups/${g.id}`} title={`Pay for ${g.name}`} />
        <Alert kind="success">You've already paid for cycle {g.current_cycle}.</Alert>
      </>
    )
  }

  return (
    <div className="mx-auto flex w-full max-w-[560px] flex-col gap-5">
      <PageTitle back={step === 0 || step === 3 ? `#/groups/${g.id}` : undefined} title={`Pay for ${g.name}`}
        sub={`Due ${fullDate(g.next_due_date)} · ${METAL[g.metal]}-backed`} />
      {step > 0 && step < 3 && (
        <button type="button" onClick={() => setStep(step - 1)} className="-mt-2 flex min-h-11 items-center gap-1 self-start text-sm font-semibold text-gold-text">
          <Icon name="back" size={18} />Back
        </button>
      )}
      <Steps step={step} />

      {step === 0 && (
        <Card className="flex flex-col gap-4">
          <h2 className="font-display text-lg font-semibold">How much?</h2>
          {rotating ? (
            <div className="flex flex-col gap-1 rounded-tile bg-tile p-4">
              <span className="text-[13px] text-ink-3">Cycle {g.current_cycle} contribution, the same for everyone</span>
              <span className="num text-3xl font-semibold">{kwacha(min)}</span>
            </div>
          ) : (
            <>
              <ChoiceChips label="Amount" mono columns={4} value={choice || min} onChange={setChoice}
                options={[...presets.map((p) => ({ value: p, label: kwacha(p).replace('.00', '') })), { value: 'other', label: 'Other' }]} />
              {choice === 'other' && (
                <Field label="Amount (ZMW)" mono type="number" inputMode="decimal" min={min} step="0.01"
                  value={custom} onChange={(e) => setCustom(e.target.value)} hint={`At least ${kwacha(min)}`} />
              )}
            </>
          )}
          <Button size="lg" disabled={!amount || Number(amount) < Number(min)} onClick={() => setStep(1)}>Continue</Button>
        </Card>
      )}

      {step === 1 && (
        <Card className="flex flex-col gap-4">
          <h2 className="font-display text-lg font-semibold">Pay from</h2>
          <div role="radiogroup" aria-label="Mobile money number" className="flex flex-col gap-2">
            {list.map((w) => {
              const on = wallet?.id === w.id
              return (
                <button key={w.id} type="button" role="radio" aria-checked={on} onClick={() => setWalletId(w.id)}
                  className={`flex min-h-16 items-center gap-3 rounded-[14px] px-4 text-left ${on ? 'border-2 border-gold bg-gold-tint' : 'border border-control bg-card'}`}>
                  <span className={`h-5 w-5 shrink-0 rounded-full bg-card ${on ? 'border-[6px] border-gold' : 'border-2 border-disabled'}`} />
                  <span className="flex flex-1 flex-col">
                    <span className="font-bold">{w.provider_name}</span>
                    <span className="num text-sm text-ink-2">{localPhone(w.number)}</span>
                  </span>
                  {w.is_default && <span className="text-xs font-semibold text-ink-3">Default</span>}
                </button>
              )
            })}
          </div>
          <a href="#/me" className="text-sm font-semibold">Add another number</a>
          <Button size="lg" disabled={!wallet || action.busy} onClick={toReview}>{action.busy ? 'Getting today\'s price…' : 'Review'}</Button>
          <Alert>{action.error}</Alert>
        </Card>
      )}

      {step === 2 && quote && (
        <Card className="flex flex-col gap-4">
          <h2 className="font-display text-lg font-semibold">Check and pay</h2>
          <div className="flex flex-col">
            <Row k="Group" v={g.name} mono={false} />
            <Row k="Amount" v={kwacha(amount)} />
            <Row k="From" v={`${wallet.provider_name} · ${localPhone(wallet.number)}`} />
          </div>
          <div className="flex flex-col gap-1.5 rounded-2xl border border-gold-tint-line bg-gold-tint p-4">
            <span className="text-xs font-semibold uppercase tracking-[0.08em] text-gold-muted">Estimated {metal}</span>
            <span className="num text-[28px] font-semibold text-gold-strong">≈ {grams(quote.grams)}</span>
            <span className="text-[13px] leading-snug text-gold-muted">
              At today's {perGram(quote.price_per_gram)}, after the {kwacha(quote.fee_zmw)} custody fee.
              The group's {metal} is bought on <b>{fullDate(g.next_due_date)}</b> at that day's price, so the final amount may differ a little.
            </span>
          </div>
          <Alert>{action.error}</Alert>
          <Button size="lg" disabled={!online || action.busy} onClick={pay}>{action.busy ? 'Waiting for your mobile money…' : `Pay ${kwacha(amount)}`}</Button>
          {!online && <p className="text-[13px] text-ink-3">Paying needs a live connection. Nothing is saved to send later.</p>}
        </Card>
      )}

      {step === 3 && result && (
        <Card className="flex flex-col items-center gap-4 text-center">
          <span className="flex h-16 w-16 items-center justify-center rounded-full bg-positive-bg text-positive"><Icon name="check" size={32} strokeWidth={2.4} /></span>
          <div className="flex flex-col gap-1">
            <h2 className="font-display text-2xl font-semibold">{kwacha(result.amount)} received</h2>
            <p className="text-sm text-ink-2">from {localPhone(result.wallet_number)}</p>
          </div>
          <div className="flex w-full flex-col text-left">
            <Row k="Reference" v={result.reference} />
            <Row k="Estimated gold" v={`≈ ${grams(result.estimated_grams)}`} />
            <Row k="Gold bought on" v={fullDate(result.gold_buy_date)} mono={false} />
          </div>
          <p className="text-[13px] text-ink-3">We've sent you an SMS receipt. You'll get another when the gold is bought.</p>
          <div className="grid w-full grid-cols-2 gap-3">
            <LinkButton variant="secondary" href="#/ledger">View ledger</LinkButton>
            <LinkButton href={`#/groups/${g.id}`}>Done</LinkButton>
          </div>
        </Card>
      )}
    </div>
  )
}
