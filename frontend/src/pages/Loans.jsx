import { useState } from 'react'
import { api, fullDate, grams, kwacha } from '../api'
import { useAction, useApi } from '../hooks'
import { Alert, Button, Card, Field, Loading, PageTitle, StatTile, StatusChip } from '../ui'

function RepayForm({ loan, online, onDone }) {
  const [amount, setAmount] = useState(loan.outstanding)
  const action = useAction()
  return (
    <form className="flex flex-col gap-2.5 border-t border-track pt-3" onSubmit={async (e) => {
      e.preventDefault()
      const r = await action.run(() => api(`/loans/${loan.id}/repay/`, { method: 'POST', body: { amount } }))
      if (r) onDone()
    }}>
      <Field label="Repay (ZMW)" mono type="number" inputMode="decimal" min="0.01" max={loan.outstanding} step="0.01"
        value={amount} onChange={(e) => setAmount(e.target.value)} hint={`${kwacha(loan.outstanding)} left to pay`} required />
      <Alert>{action.error}</Alert>
      <Button type="submit" disabled={!online || action.busy}>Pay {kwacha(amount || '0')}</Button>
    </form>
  )
}

export default function Loans({ online, member }) {
  const loans = useApi('/loans/')
  const groups = useApi('/groups/')
  const annuity = (groups.data?.results || []).filter((g) => g.group_type === 'ANNUITY' && g.status === 'ACTIVE')
  const [groupId, setGroupId] = useState('')
  const selected = groupId || annuity[0]?.id || ''
  const limit = useApi(selected ? `/loans/limit/?group=${selected}` : null)
  const [amount, setAmount] = useState('')
  const action = useAction()
  const verified = member?.kyc_status === 'VERIFIED'
  const interest = amount ? (Number(amount) * 0.1).toFixed(2) : '0.00'
  const repay = amount ? (Number(amount) * 1.1).toFixed(2) : '0.00'

  async function request(e) {
    e.preventDefault()
    const r = await action.run(
      () => api('/loans/', { method: 'POST', body: { group: selected, principal: amount } }),
      (l) => `Request for ${kwacha(l.principal)} sent. ${grams(l.collateral_grams)} of your gold is held as collateral until it's repaid.`,
    )
    if (r) {
      setAmount('')
      loans.reload()
      limit.reload()
    }
  }

  return (
    <>
      <PageTitle back="#/" title="Loans" sub="Borrow against your gold without selling it" />

      <div className="flex flex-wrap items-start gap-[18px] lg:gap-6">
        <Card className="flex min-w-0 flex-[1_1_380px] flex-col gap-4">
          {annuity.length === 0 ? (
            <p className="text-sm text-ink-2">Loans are secured by annuity savings. Join or create an annuity group first.</p>
          ) : (
            <>
              <div className="grid grid-cols-2 gap-3">
                <StatTile gold label="You can borrow up to" value={kwacha(limit.data?.max_loan)} sub="50% of your available gold" />
                <StatTile label="Available gold" value={grams(limit.data?.available_grams)} />
              </div>
              {!verified && <Alert kind="info">Verify your NRC on the Me page before you borrow.</Alert>}
              <form onSubmit={request} className="flex flex-col gap-4">
                {annuity.length > 1 && (
                  <Field label="Secured by" value={selected} onChange={(e) => setGroupId(e.target.value)}>
                    {annuity.map((g) => <option key={g.id} value={g.id}>{g.name}</option>)}
                  </Field>
                )}
                <Field label="How much?" mono type="number" inputMode="decimal" min="1" step="0.01" max={limit.data?.max_loan}
                  value={amount} onChange={(e) => setAmount(e.target.value)} required />
                <div className="grid grid-cols-2 gap-3">
                  <StatTile label="Interest (10% flat)" value={kwacha(interest)} />
                  <StatTile label="You repay" value={kwacha(repay)} />
                </div>
                <Alert kind="success">{action.success}</Alert>
                <Alert>{action.error}</Alert>
                <Button type="submit" size="lg" disabled={!online || action.busy || !verified}>Send request</Button>
                <p className="text-[13px] text-ink-3">A Treadstone officer approves it, then the money goes to your mobile money.</p>
              </form>
            </>
          )}
        </Card>

        <div className="flex min-w-0 flex-[1_1_380px] flex-col gap-3">
          <h2 className="eyebrow">Your loans</h2>
          {loans.loading && !loans.data && <Loading />}
          {loans.data?.results.length === 0 && <Card><p className="text-ink-3">No loans yet.</p></Card>}
          {loans.data?.results.map((l) => (
            <Card key={l.id} className="flex flex-col gap-3">
              <div className="flex items-start justify-between gap-2">
                <span>
                  <span className="num block text-lg font-semibold">{kwacha(l.principal)}</span>
                  <span className="block text-xs text-ink-3">{l.group_name} · {fullDate(l.created_at)} · {grams(l.collateral_grams)} held</span>
                </span>
                <StatusChip value={l.status} label={l.status === 'PENDING' ? 'Awaiting approval' : undefined} />
              </div>
              {l.status === 'ACTIVE' && (
                <>
                  <div className="h-2 overflow-hidden rounded-full bg-track">
                    <div className="h-full rounded-full bg-gold" style={{ width: `${(Number(l.amount_repaid) / Number(l.total_due)) * 100}%` }} />
                  </div>
                  <span className="num text-sm text-ink-2">{kwacha(l.amount_repaid)} of {kwacha(l.total_due)} repaid</span>
                  <RepayForm loan={l} online={online} onDone={() => { loans.reload(); limit.reload() }} />
                </>
              )}
            </Card>
          ))}
        </div>
      </div>
    </>
  )
}
