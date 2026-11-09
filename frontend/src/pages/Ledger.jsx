import { useState } from 'react'
import { dayMonth, fullDate, grams, kwacha, perGram } from '../api'
import { useApi } from '../hooks'
import { Alert, Card, Chip, Loading, PageTitle, StatTile } from '../ui'

const FILTERS = [
  { value: 'all', label: 'All' },
  { value: 'contribution', label: 'Contributions' },
  { value: 'payout', label: 'Payouts' },
  { value: 'loan', label: 'Loans' },
]

const VIA = { MTN: 'MTN MoMo', AIRTEL: 'Airtel Money', ZAMTEL: 'Zamtel Kwacha' }

const BADGE = {
  contribution: ['gold', 'Contribution'],
  payout: ['positive', 'Payout'],
  loan: ['info', 'Loan received'],
  repayment: ['info', 'Loan repaid'],
  failed: ['negative', 'Failed payment'],
}

// One list of everything that moved money, newest first.
function buildRows(contributions, payouts, loans) {
  const rows = []
  for (const c of contributions) {
    rows.push({
      key: `c${c.id}`, type: c.status === 'FAILED' ? 'failed' : 'contribution', filter: 'contribution', at: c.created_at,
      group: c.group_name, amount: c.status === 'FAILED' ? null : `-${c.amount}`, grams: c.grams, price: c.price_per_gram,
      ref: c.reference || c.custodian_reference || c.payment_reference || '—', note: c.failure_reason,
      estimate: c.estimated_grams, buyDate: c.gold_buy_date, via: c.provider,
    })
  }
  for (const p of payouts) {
    rows.push({
      key: `p${p.id}`, type: 'payout', filter: 'payout', at: p.created_at, group: p.group_name,
      amount: p.amount_zmw, grams: `-${p.grams}`, price: p.price_per_gram, ref: p.custodian_reference,
    })
  }
  for (const l of loans) {
    if (l.disbursement_reference) {
      rows.push({ key: `l${l.id}`, type: 'loan', filter: 'loan', at: l.reviewed_at || l.created_at, group: l.group_name, amount: l.principal, ref: l.disbursement_reference })
    }
    for (const r of l.repayments) {
      rows.push({ key: `r${r.id}`, type: 'repayment', filter: 'loan', at: r.created_at, group: l.group_name, amount: `-${r.amount}`, ref: r.payment_reference })
    }
  }
  return rows.sort((a, b) => new Date(b.at) - new Date(a.at))
}

export default function Ledger() {
  const contributions = useApi('/contributions/')
  const payouts = useApi('/payouts/')
  const loans = useApi('/loans/')
  const dash = useApi('/auth/dashboard/')
  const [filter, setFilter] = useState('all')

  const ready = contributions.data && payouts.data && loans.data
  if (!ready && (contributions.loading || payouts.loading || loans.loading)) return <Loading />
  const err = contributions.error || payouts.error || loans.error
  if (!ready && err) return <Alert>{err.message}</Alert>

  const all = buildRows(contributions.data.results, payouts.data.results, loans.data.results)
  const rows = filter === 'all' ? all : all.filter((r) => r.filter === filter)
  const owed = loans.data.results.filter((l) => l.status === 'ACTIVE').reduce((s, l) => s + Number(l.outstanding), 0).toFixed(2)
  const d = dash.data

  return (
    <>
      <PageTitle title="Ledger & history" sub="Every kwacha in and out, and the gold it bought or sold." />

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <StatTile label="Contributed" value={kwacha(d?.contributed_zmw)} />
        <StatTile label="Paid out to you" value={kwacha(d?.paid_out_zmw)} valueClass="!text-positive" />
        <StatTile label="Loans owed" value={kwacha(owed)} />
        <StatTile gold label="Gold held now" value={grams(d?.grams_by_metal?.XAU || '0')} sub={d ? `${kwacha(d.total_value_zmw)} today` : ''} />
      </div>

      <Card className="flex flex-col gap-3 !p-0">
        <div className="flex flex-wrap items-center justify-between gap-3 px-4 pt-4 lg:px-6 lg:pt-5">
          <h2 className="font-display text-[17px] font-semibold lg:text-xl">Transactions</h2>
          <div role="radiogroup" aria-label="Filter transactions" className="flex gap-2 overflow-x-auto">
            {FILTERS.map((f) => (
              <button key={f.value} type="button" role="radio" aria-checked={filter === f.value} onClick={() => setFilter(f.value)}
                className={`min-h-11 whitespace-nowrap rounded-full px-4 text-sm ${filter === f.value ? 'bg-gold font-bold text-on-gold' : 'border border-control font-semibold text-ink-2'}`}>
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {rows.length === 0 && <p className="px-4 pb-5 text-ink-3 lg:px-6">Nothing here yet.</p>}

        {/* Phone: cards */}
        <ul className="flex flex-col lg:hidden">
          {rows.map((r) => (
            <li key={r.key} className="flex flex-col gap-1.5 border-t border-track px-4 py-3.5">
              <div className="flex items-center justify-between gap-2">
                <Chip tone={BADGE[r.type][0]}>{BADGE[r.type][1]}</Chip>
                <span className={`num font-semibold ${r.amount && !r.amount.startsWith('-') ? 'text-positive' : ''}`}>{r.amount ? kwacha(r.amount, { signed: true }) : '—'}</span>
              </div>
              <div className="flex items-start justify-between gap-2 text-xs text-ink-3">
                <span><b className="text-sm text-ink">{r.group}</b><br />{fullDate(r.at)}{r.note ? ` · ${r.note}` : ''}</span>
                <span className="num text-right">
                  {r.grams ? <><b className="text-ink">{grams(r.grams, { signed: true })}</b><br />{perGram(r.price)}</>
                    : r.estimate ? <><b className="text-gold-strong">≈ {grams(r.estimate, { signed: true })}</b><br />bought {dayMonth(r.buyDate)}</>
                    : 'No gold moved'}
                </span>
              </div>
            </li>
          ))}
        </ul>

        {/* Desktop: table */}
        <div className="hidden overflow-x-auto lg:block">
          <table className="w-full min-w-[880px] border-collapse text-sm">
            <thead>
              <tr className="text-left text-xs uppercase tracking-[0.08em] text-ink-3">
                <th className="px-6 py-2.5 font-semibold">Date</th>
                <th className="px-3 py-2.5 font-semibold">Type</th>
                <th className="px-3 py-2.5 font-semibold">Group</th>
                <th className="px-3 py-2.5 font-semibold">Via</th>
                <th className="px-3 py-2.5 text-right font-semibold">Amount</th>
                <th className="px-3 py-2.5 text-right font-semibold">Gold</th>
                <th className="px-3 py-2.5 text-right font-semibold">Price / g</th>
                <th className="px-6 py-2.5 font-semibold">Reference</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.key} className="border-t border-track">
                  <td className="whitespace-nowrap px-6 py-3.5">{fullDate(r.at)}</td>
                  <td className="px-3 py-3.5"><Chip tone={BADGE[r.type][0]}>{BADGE[r.type][1]}</Chip></td>
                  <td className="px-3 py-3.5 font-semibold">{r.group}</td>
                  <td className="px-3 py-3.5 text-ink-2">{VIA[r.via] || '—'}</td>
                  <td className={`num px-3 py-3.5 text-right font-semibold ${r.amount && !r.amount.startsWith('-') ? 'text-positive' : ''}`}>{r.amount ? kwacha(r.amount, { signed: true }) : '—'}</td>
                  <td className="num px-3 py-3.5 text-right font-semibold">
                    {r.grams ? grams(r.grams, { signed: true }) : r.estimate ? <span className="text-gold-strong">≈ {grams(r.estimate, { signed: true })}</span> : '—'}
                  </td>
                  <td className="num px-3 py-3.5 text-right text-ink-2">{r.price ? kwacha(r.price) : r.buyDate ? <span className="font-sans text-xs">bought {dayMonth(r.buyDate)}</span> : '—'}</td>
                  <td className="num px-6 py-3.5 text-[13px] text-ink-3">{r.ref}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="px-6 py-4 text-xs text-ink-3">Gold prices are what the custodian charged or paid on the day. Contributions are pooled and bought on the group's due date; ≈ marks an estimate until then.</p>
        </div>
      </Card>
    </>
  )
}
