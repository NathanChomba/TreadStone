import { useState } from 'react'
import { METAL, api, fullDate, grams, initials, kwacha, localPhone } from '../api'
import { useAction, useApi } from '../hooks'
import { Alert, Avatar, Button, Card, Chip, Field, Icon, LinkButton, Loading, PageTitle, StatTile, StatusChip } from '../ui'

function CycleBar({ total, current, closed }) {
  return (
    <div className="grid gap-1.5" style={{ gridTemplateColumns: `repeat(${total}, minmax(0, 1fr))` }}>
      {Array.from({ length: total }, (_, i) => {
        const n = i + 1
        const done = closed || n < current
        const now = !closed && n === current
        return <span key={n} className={`h-2 rounded-full ${done ? 'bg-gold' : now ? 'bg-gold-tint-line outline-2 outline-gold' : 'bg-track'}`} />
      })}
    </div>
  )
}

export default function GroupDetail({ id, online, member }) {
  const { data: g, loading, error, reload } = useApi(`/groups/${id}/`)
  const [withdrawGrams, setWithdrawGrams] = useState('')
  const action = useAction()
  const [copied, setCopied] = useState(false)

  if (loading && !g) return <Loading />
  if (error && !g) return <Alert>{error.message}</Alert>

  const rotating = g.group_type === 'ROTATING'
  const cs = g.cycle_status
  const paid = new Set(g.paid_member_ids || [])
  const iHavePaid = Boolean(g.paid_this_period)
  const due = g.next_due_date
  const allPaid = rotating && g.members.length > 0 && g.members.every((m) => paid.has(m.member))

  async function post(path, body, message) {
    const r = await action.run(() => api(path, { method: 'POST', body }), message)
    if (r) reload()
    return r
  }

  async function copyCode() {
    try {
      await navigator.clipboard.writeText(g.invite_code)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // clipboard blocked; the code is visible on screen
    }
  }

  return (
    <>
      <PageTitle back="#/groups" title={g.name}
        sub={`${rotating ? 'Tontine (rotating)' : 'Annuity'} · ${g.members.length} members · ${kwacha(g.contribution_amount)} ${g.frequency.toLowerCase()}`} />
      <div className="-mt-2 flex flex-wrap gap-1.5">
        <StatusChip value={g.status} />
        <Chip tone="gold">{METAL[g.metal]}-backed</Chip>
        {g.is_admin && <Chip>You're the admin</Chip>}
      </div>

      <Alert kind="success">{action.success}</Alert>
      <Alert>{action.error}</Alert>

      <div className="flex flex-wrap gap-[18px] lg:gap-6">
        <div className="flex min-w-0 flex-[2_1_480px] flex-col gap-[18px] lg:gap-6">
          <Card className="flex flex-col gap-4">
            <span className="eyebrow">Group pool at ZGCL</span>
            <div className="flex flex-col gap-1">
              <span className="num text-[34px] font-semibold leading-none tracking-[-0.03em] lg:text-5xl">{grams(g.group_grams)}</span>
              <span className="text-sm text-ink-2">of {METAL[g.metal].toLowerCase()} held for the group</span>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <StatTile label="Your share" value={grams(Number(g.my_grams) < 0 ? '0' : g.my_grams)} sub={kwacha(Number(g.my_value_zmw) < 0 ? '0' : g.my_value_zmw)} />
              {rotating
                ? <StatTile gold label={`Cycle ${g.current_cycle} pot goes to`} value={cs?.recipient?.name || '—'} valueClass="!font-sans" sub={cs ? `${paid.size} of ${g.members.length} paid` : ''} />
                : <StatTile gold label="You can withdraw" value={grams(g.my_available_grams)} sub={Number(g.my_locked_grams) > 0 ? `${grams(g.my_locked_grams)} locked by a loan` : 'None locked'} />}
            </div>
            {!rotating && g.started_at && (
              <div className="flex flex-col gap-2">
                <div className="flex justify-between text-[13px] text-ink-2">
                  <span>Period {Math.min(g.period_index, g.term_cycles)} of {g.term_cycles}</span>
                  <span>Matures {fullDate(g.maturity_date)}</span>
                </div>
                <CycleBar total={g.term_cycles} current={g.period_index} closed={g.period_index > g.term_cycles} />
              </div>
            )}
            {Number(g.my_received_zmw) > 0 && (
              <p className="rounded-tile bg-gold-tint px-3.5 py-2.5 text-[13px] text-gold-muted">
                Your <b className="num">{kwacha(g.my_received_zmw)}</b> is received. Its gold is bought on {fullDate(due)} at that day's price.
              </p>
            )}
            {rotating && g.status !== 'OPEN' && (
              <div className="flex flex-col gap-2">
                <div className="flex justify-between text-[13px] text-ink-2">
                  <span>{g.status === 'CLOSED' ? 'All cycles paid out' : `Cycle ${g.current_cycle} of ${g.members.length}`}</span>
                  <span>Paid out in kwacha at that day's gold price</span>
                </div>
                <CycleBar total={g.members.length} current={g.current_cycle} closed={g.status === 'CLOSED'} />
              </div>
            )}
          </Card>

          {g.status === 'OPEN' && (
            <Card className="flex flex-col gap-3">
              <h2 className="font-display text-[17px] font-semibold">Waiting for members</h2>
              <p className="text-sm text-ink-2">Share the invite code. The payout order follows the order people join.</p>
              {g.is_admin && (
                <Button disabled={!online || action.busy || g.members.length < 2}
                  onClick={() => post(`/groups/${g.id}/start/`, undefined, 'Group started. Members can now pay.')}>
                  Start the group ({g.members.length} members)
                </Button>
              )}
            </Card>
          )}

          {g.status === 'ACTIVE' && (
            <Card className="flex flex-wrap items-center justify-between gap-4">
              {iHavePaid ? (
                <span className="flex items-center gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-full bg-positive-bg text-positive"><Icon name="check" /></span>
                  <span>
                    <span className="block font-semibold">You've paid for this {rotating ? 'cycle' : 'period'}</span>
                    <span className="block text-[13px] text-ink-3">Next due {fullDate(due)}</span>
                  </span>
                </span>
              ) : (
                <span className="flex items-center gap-3">
                  <span className="flex h-10 w-10 items-center justify-center rounded-full bg-gold-chip text-gold-text"><Icon name="calendar" /></span>
                  <span>
                    <span className="num block font-semibold">{kwacha(g.contribution_amount)} due {fullDate(due)}</span>
                    <span className={`block text-[13px] ${g.days_until_due <= 2 ? 'font-semibold text-negative' : 'text-ink-3'}`}>
                      {g.days_until_due === 0 ? 'Due today' : `${g.days_until_due} day${g.days_until_due === 1 ? '' : 's'} left`} · gold bought that day
                    </span>
                  </span>
                </span>
              )}
              {!(rotating && iHavePaid) && (
                <LinkButton href={`#/contribute/${g.id}`} className={online ? '' : 'pointer-events-none opacity-50'}>
                  {iHavePaid ? 'Add more' : `Pay ${kwacha(g.contribution_amount)}`}
                </LinkButton>
              )}
            </Card>
          )}

          {g.status === 'ACTIVE' && !rotating && Number(g.my_available_grams) > 0 && (
            <Card className="flex flex-col gap-3">
              <h2 className="font-display text-[17px] font-semibold lg:text-xl">Withdraw</h2>
              <form className="flex flex-col gap-3" onSubmit={async (e) => {
                e.preventDefault()
                const r = await post('/payouts/withdraw/', { group: g.id, grams: withdrawGrams },
                  (p) => `Sold ${grams(p.grams)} for ${kwacha(p.amount_zmw)}. Sent to your mobile money (ref ${p.payment_reference}).`)
                if (r) setWithdrawGrams('')
              }}>
                <Field label="Grams to sell" mono type="number" inputMode="decimal" min="0.0001" step="0.0001" max={g.my_available_grams}
                  value={withdrawGrams} onChange={(e) => setWithdrawGrams(e.target.value)}
                  hint={`Up to ${grams(g.my_available_grams)}. Sold at that moment's price, less the 1% fee.`} required />
                <Button type="submit" variant="secondary" disabled={!online || action.busy}>Sell and withdraw</Button>
              </form>
            </Card>
          )}

          {rotating && g.status === 'ACTIVE' && g.is_admin && (
            <Card className="flex flex-col gap-3">
              <h2 className="font-display text-[17px] font-semibold lg:text-xl">Pay out cycle {g.current_cycle}</h2>
              <p className="text-sm text-ink-2">
                {!allPaid
                  ? `Unlocks when all ${g.members.length} members have paid this cycle.`
                  : cs?.awaiting_gold
                    ? `Everyone has paid. The gold is bought on ${fullDate(due)}; the pot can go to ${cs.recipient?.name} after that.`
                    : `Everyone has paid and the gold is bought. The pot goes to ${cs.recipient?.name}.`}
              </p>
              <Button disabled={!online || action.busy || !allPaid || cs?.awaiting_gold}
                onClick={() => post(`/groups/${g.id}/payout/`, undefined, (p) => `Paid ${kwacha(p.amount_zmw)} (${grams(p.grams)}) to ${cs.recipient?.name}.`)}>
                Pay {cs?.recipient?.name?.split(' ')[0] || 'recipient'} and start the next cycle
              </Button>
            </Card>
          )}
        </div>

        <div className="flex min-w-0 flex-[1_1_300px] flex-col gap-[18px] lg:gap-6">
          <Card className="flex flex-col gap-1">
            <div className="mb-1 flex items-center justify-between">
              <h2 className="font-display text-[17px] font-semibold">{rotating && g.status === 'ACTIVE' ? `Cycle ${g.current_cycle}` : 'Members'}</h2>
              {g.status === 'ACTIVE' && <span className="text-[13px] text-ink-3">{paid.size} of {g.members.length} paid</span>}
            </div>
            {g.is_admin && g.status === 'ACTIVE' && paid.size < g.members.length && (
              <Button variant="secondary" size="sm" className="mb-2" disabled={!online || action.busy}
                onClick={() => post(`/groups/${g.id}/remind/`, {}, (r) => (r.reminded.length ? `Reminder sent to ${r.reminded.join(', ')}.` : 'Everyone has paid.'))}>
                Remind everyone who hasn't paid
              </Button>
            )}
            {g.members.map((m) => {
              const isMe = m.member === member?.id
              return (
                <div key={m.id} className="flex items-center gap-3 border-t border-track py-3 first:border-t-0">
                  <Avatar text={initials(...(m.name || m.phone).split(' '))} me={isMe} />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate font-semibold">{m.name || localPhone(m.phone)}{isMe ? ' (you)' : ''}</span>
                    <span className="block text-xs text-ink-3">{rotating ? `#${m.position} in line` : localPhone(m.phone)}{m.is_admin ? ' · admin' : ''}</span>
                  </span>
                  {g.status === 'ACTIVE' && (paid.has(m.member)
                    ? <Chip tone="positive">Paid</Chip>
                    : g.is_admin && !isMe
                      ? <Button variant="soft" size="sm" disabled={!online || action.busy}
                          onClick={() => post(`/groups/${g.id}/remind/`, { member_ids: [m.member] }, `Reminder sent to ${m.name || localPhone(m.phone)}.`)}>Remind</Button>
                      : <Chip tone="gold">Due {fullDate(due).replace(/ \d{4}$/, '')}</Chip>)}
                </div>
              )
            })}
          </Card>

          <Card className="flex flex-col gap-2.5">
            <h2 className="font-display text-[17px] font-semibold">Invite</h2>
            <div className="flex items-center justify-between gap-2 rounded-tile bg-tile px-3.5 py-2">
              <span className="num text-lg font-semibold tracking-[0.14em]">{g.invite_code}</span>
              <button type="button" onClick={copyCode} aria-label="Copy invite code" className="flex h-11 items-center gap-1.5 px-2 text-sm font-semibold text-gold-text">
                <Icon name={copied ? 'check' : 'copy'} size={18} />{copied ? 'Copied' : 'Copy'}
              </button>
            </div>
            <span className="text-xs text-ink-3">{g.member_count} of {g.max_members} places taken</span>
          </Card>

          <Card className="flex flex-col gap-1 text-sm">
            <h2 className="mb-1 font-display text-[17px] font-semibold">Rules</h2>
            {[
              ['Contribution', `${kwacha(g.contribution_amount)} ${g.frequency.toLowerCase()}${rotating ? '' : ' minimum'}`],
              ['Due and gold bought', g.frequency === 'MONTHLY' ? `On the ${g.due_day}${['th', 'st', 'nd', 'rd'][(g.due_day % 10 > 3 || [11, 12, 13].includes(g.due_day)) ? 0 : g.due_day % 10]} of each month` : 'Weekly, on the day it started'],
              ['Payout', rotating ? 'Whole pot, in joining order' : 'Withdraw your own gold any time'],
              ['Loans', rotating ? 'Not available' : 'Up to 50% of your share, 10% flat'],
              ['Custody fee', '1% when gold is bought or sold'],
            ].map(([k, v]) => (
              <div key={k} className="flex justify-between gap-3 border-t border-track py-2.5 first:border-t-0">
                <span className="text-ink-3">{k}</span><span className="text-right font-semibold">{v}</span>
              </div>
            ))}
          </Card>
        </div>
      </div>
    </>
  )
}
