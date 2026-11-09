import { useState } from 'react'
import { METAL, grams, isStale, kwacha, perGram, time24 } from '../api'
import { useApi, usePrice } from '../hooks'
import { Alert, Card, Icon, Loading, PageTitle, PriceChange, PriceChart, Segmented } from '../ui'

const RANGE_SUFFIX = { '1W': ' this week', '1M': ' this month', '6M': ' in 6 months', '1Y': ' this year' }

export default function Vault() {
  const [range, setRange] = useState('1M')
  const dash = useApi('/auth/dashboard/')
  const gold = usePrice('XAU', range)
  const silver = usePrice('XAG', range)

  if (dash.loading && !dash.data) return <Loading />
  if (dash.error && !dash.data) return <Alert>{dash.error.message}</Alert>

  const d = dash.data
  const g = d.grams_by_metal || {}
  // What the member put in and hasn't had back, versus what that money is worth as gold now.
  const asCash = (Number(d.contributed_zmw) - Number(d.paid_out_zmw)).toFixed(2)
  const asGold = d.total_value_zmw
  const max = Math.max(Number(asCash), Number(asGold), 1)
  const at = gold.current?.fetched_at

  return (
    <>
      <PageTitle title="Vault & metals" sub={at ? `Prices at ${time24(at)}` : undefined} />

      <div className="flex flex-wrap gap-[18px] lg:gap-6">
        <div className="flex min-w-0 flex-[2_1_480px] flex-col gap-[18px] lg:gap-6">
          <Card className="flex flex-col gap-1">
            <span className="eyebrow mb-1">What you hold</span>
            {['XAU', 'XAG'].map((m) => {
              const p = m === 'XAU' ? gold.current : silver.current
              const held = g[m] || '0.0000'
              return (
                <div key={m} className="flex items-center justify-between gap-3 border-t border-track py-3.5 first:border-t-0">
                  <span className="flex items-center gap-2 font-semibold"><span className={`h-2.5 w-2.5 rounded-full ${m === 'XAU' ? 'bg-gold' : 'bg-silver'}`} />{METAL[m]}</span>
                  <span className="text-right">
                    <span className="num block text-lg font-semibold">{grams(held)}</span>
                    <span className="num block text-xs text-ink-3">
                      {Number(held) > 0 && p ? kwacha((Number(held) * Number(p.price_per_gram)).toFixed(2)) : `None of your groups use ${METAL[m].toLowerCase()}`}
                    </span>
                  </span>
                </div>
              )
            })}
          </Card>

          <Card className="flex flex-col gap-4">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div className="flex flex-col gap-1">
                <span className="eyebrow">Gold per gram</span>
                <span className="num text-3xl font-semibold tracking-[-0.02em] lg:text-4xl">{gold.current ? kwacha(gold.current.price_per_gram) : '—'}</span>
              </div>
              <PriceChange pct={gold.changePct} suffix={RANGE_SUFFIX[range]} />
            </div>
            <PriceChart points={gold.points} height={170} />
            <Segmented label="Chart range" className="w-full" value={range} onChange={setRange}
              options={['1W', '1M', '6M', '1Y'].map((r) => ({ value: r, label: r }))} />
            <p className={`text-xs ${at && isStale(at) ? 'text-negative' : 'text-ink-3'}`}>
              {at ? `Latest price at ${time24(at)}. ` : ''}Prices refresh every 15 minutes while the worker runs. Live and historical prices from GoldAPI, converted at each day's USD to ZMW rate.
            </p>
            {silver.current && (
              <div className="flex items-center justify-between border-t border-track pt-3 text-sm">
                <span className="flex items-center gap-2"><span className="h-2 w-2 rounded-full bg-silver" />Silver per gram</span>
                <span className="flex items-center gap-2"><span className="num font-semibold">{perGram(silver.current.price_per_gram)}</span><PriceChange pct={silver.changePct} /></span>
              </div>
            )}
          </Card>
        </div>

        <div className="flex min-w-0 flex-[1_1_300px] flex-col gap-[18px] lg:gap-6">
          {Number(d.contributed_zmw) > 0 && (
            <Card className="flex flex-col gap-3 !border-gold-tint-line !bg-gold-tint">
              <h2 className="font-display text-[17px] font-semibold">Your {kwacha(asCash)} if you had…</h2>
              {[['Kept it as kwacha', asCash, 'bg-disabled'], ['Saved it in gold', asGold, 'bg-gold']].map(([label, v, bar]) => (
                <div key={label} className="flex flex-col gap-1.5">
                  <div className="flex justify-between text-[13px] text-gold-muted"><span>{label}</span><span className="num font-semibold text-ink">{kwacha(v)}</span></div>
                  <div className="h-2 overflow-hidden rounded-full bg-card"><div className={`h-full rounded-full ${bar}`} style={{ width: `${(Number(v) / max) * 100}%` }} /></div>
                </div>
              ))}
              <p className="text-[13px] leading-snug text-gold-muted">
                {Number(asGold) >= Number(asCash)
                  ? `Gold kept ${kwacha(d.preserved_zmw)} more of your money's value, before inflation is counted.`
                  : `Right now gold is ${kwacha(d.preserved_zmw).replace('−', '')} behind cash, after the 1% fees and recent price moves.`}
              </p>
            </Card>
          )}
          <Card className="flex items-start gap-3">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-control bg-gold-chip text-gold-text"><Icon name="shield" /></span>
            <span className="flex flex-col gap-0.5">
              <span className="font-bold">Held by Zambia Gold Company Ltd</span>
              <span className="text-[13px] text-ink-3">Every purchase gets a ZGCL reference in your ledger. Simulated in this prototype.</span>
            </span>
          </Card>
        </div>
      </div>
    </>
  )
}
