import { useState } from 'react'
import { METAL, dayMonth, fullDate, grams, greeting, initials, isNegative, isStale, kwacha, longToday, perGram, time24 } from '../api'
import { useApi, usePrice } from '../hooks'
import { Alert, Avatar, Bell, Card, Chip, Icon, LinkButton, Loading, PriceChange, PriceChart, Segmented, StatTile, StatusChip } from '../ui'

function RateCard({ metal, compact = false }) {
  const p = usePrice(metal)
  if (!p.current) return null
  const up = p.points.length < 2 || p.points[p.points.length - 1] >= p.points[0]
  return (
    <div className="flex items-center justify-between gap-3 rounded-tile bg-tile p-3.5">
      <span className="flex min-w-0 flex-col gap-1">
        <span className="flex items-center gap-1.5 text-[13px] font-semibold">
          <span className={`h-2 w-2 rounded-full ${metal === 'XAU' ? 'bg-gold' : 'bg-silver'}`} />{METAL[metal]}
        </span>
        <span className={`num font-semibold ${compact ? 'text-base' : 'text-lg'}`}>{kwacha(p.current.price_per_gram)}</span>
        <PriceChange pct={p.changePct} suffix=" this month" />
      </span>
      <PriceChart points={p.points} height={36} area={false} tone={up ? 'up' : 'down'} className="!w-24" />
    </div>
  )
}

export default function Dashboard({ member, unread }) {
  const { data, error, loading } = useApi('/auth/dashboard/')
  const activity = useApi('/metals/ledger/')
  const gold = usePrice('XAU')
  const [unit, setUnit] = useState('zmw')

  if (loading && !data) return <Loading />
  if (error && !data) return <Alert>{error.message}</Alert>

  const me = data.member || member
  const goldGrams = data.grams_by_metal?.XAU || '0.0000'
  const active = data.holdings.filter((h) => h.group_status === 'ACTIVE')
  const firstActive = active[0]
  const annuity = active.find((h) => h.group_type === 'ANNUITY' && Number(h.available_grams) > 0)
  const preservedNeg = isNegative(data.preserved_zmw)
  const priceAt = gold.current?.fetched_at

  return (
    <>
      <header className="flex items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-3">
          <a href="#/me" aria-label="Profile" className="no-underline lg:hidden"><Avatar text={initials(me.first_name, me.last_name)} me size={44} /></a>
          <div className="min-w-0">
            <p className="text-[13px] text-ink-3"><span className="lg:hidden">{greeting()}</span><span className="hidden lg:inline">{longToday()}</span></p>
            <h1 className="truncate font-display text-xl font-semibold tracking-tight lg:text-3xl">
              <span className="hidden lg:inline">{greeting()}, </span>{me.first_name}
            </h1>
          </div>
        </div>
        <div className="flex items-center gap-2.5">
          {me.kyc_status === 'VERIFIED'
            ? <Chip tone="positive" className="hidden sm:inline-flex">✓ KYC verified</Chip>
            : <a href="#/me" className="no-underline"><Chip tone="gold">Verify your NRC</Chip></a>}
          <Bell unread={unread ?? data.unread_notifications} />
          <a href="#/me" aria-label="Profile" className="hidden no-underline lg:inline-flex"><Avatar text={initials(me.first_name, me.last_name)} me size={44} /></a>
        </div>
      </header>

      <div className="flex flex-wrap gap-[18px] lg:gap-6">
        <Card className="flex min-w-0 flex-[2_1_520px] flex-col gap-4">
          <div className="flex items-center justify-between gap-3">
            <span className="eyebrow">Vault value</span>
            <Segmented label="Show value in" options={[{ value: 'zmw', label: 'Kwacha' }, { value: 'g', label: 'Grams' }]} value={unit} onChange={setUnit} />
          </div>
          <div className="flex flex-col gap-1.5">
            <span className="num text-[38px] font-semibold leading-none tracking-[-0.03em] lg:text-[clamp(40px,5vw,60px)]">
              {unit === 'zmw' ? kwacha(data.total_value_zmw) : grams(goldGrams)}
            </span>
            <span className="text-sm text-ink-2">
              = {unit === 'zmw' ? grams(goldGrams) : kwacha(data.total_value_zmw)} · held as gold at ZGCL
            </span>
          </div>
          {Number(data.awaiting_gold_zmw) > 0 && (
            <p className="rounded-tile bg-gold-tint px-3.5 py-2.5 text-[13px] text-gold-muted">
              Plus <b className="num">{kwacha(data.awaiting_gold_zmw)}</b> received and waiting for its gold, bought on the group's due date.
            </p>
          )}
          <div className="flex flex-col gap-1.5">
            <PriceChart points={gold.points} height={110} />
            <span className={`text-xs ${priceAt && isStale(priceAt) ? 'text-negative' : 'text-ink-3'}`}>
              Gold price per gram, last 30 days{priceAt ? ` · prices at ${time24(priceAt)}` : ''}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            <StatTile label="You contributed" value={kwacha(data.contributed_zmw)} />
            <StatTile gold label="Preserved vs cash" value={kwacha(data.preserved_zmw, { signed: true })}
              valueClass={preservedNeg ? '!text-negative' : ''}
              sub={preservedNeg ? 'Fees and price moves so far' : 'More than keeping kwacha'} />
            <StatTile label="Paid out to you" value={kwacha(data.paid_out_zmw)} />
          </div>
          <div className="grid grid-cols-3 gap-2.5 sm:flex sm:flex-wrap">
            <LinkButton href={firstActive ? `#/contribute/${firstActive.group}` : '#/groups'} className="col-span-3 sm:col-auto">
              <Icon name="plus" size={18} />Contribute
            </LinkButton>
            <LinkButton variant="secondary" href={annuity ? `#/groups/${annuity.group}` : '#/vault'} className="col-span-1 px-2 sm:px-5"><Icon name="up" size={18} />Withdraw</LinkButton>
            <LinkButton variant="secondary" href="#/groups" className="col-span-1 px-2 sm:px-5"><Icon name="payGroup" size={18} />Groups</LinkButton>
            <LinkButton variant="secondary" href="#/loans" className="col-span-1 px-2 sm:px-5"><Icon name="loans" size={18} />Loan</LinkButton>
          </div>
        </Card>

        <div className="flex min-w-0 flex-[1_1_300px] flex-col gap-[18px] lg:gap-6">
          <Card className="flex flex-col gap-3">
            <div className="flex items-baseline justify-between">
              <span className="eyebrow">Metal rates</span>
              <span className="text-xs text-ink-3">per gram{priceAt ? ` · ${time24(priceAt)}` : ''}</span>
            </div>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-1">
              <RateCard metal="XAU" compact />
              <RateCard metal="XAG" compact />
            </div>
          </Card>
          {data.up_next.length > 0 && (
            <Card className="flex flex-col gap-1">
              <span className="eyebrow mb-1">Up next</span>
              {data.up_next.map((u) => (
                <a key={`${u.kind}${u.group}`} href={u.kind === 'due' ? `#/contribute/${u.group}` : `#/groups/${u.group}`}
                  className="flex items-center gap-3 border-t border-track py-3 text-ink no-underline first:border-t-0">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-control bg-gold-chip text-gold-text">
                    <Icon name={u.kind === 'matures' ? 'clock' : 'calendar'} size={18} />
                  </span>
                  <span className="min-w-0 flex-1">
                    {u.kind === 'due' && <>
                      <span className="num block font-semibold">{kwacha(u.amount)} due to {u.group_name}</span>
                      <span className={`block text-xs ${u.days <= 2 ? 'font-semibold text-negative' : 'text-ink-3'}`}>{fullDate(u.date)} · {u.days === 0 ? 'today' : u.days === 1 ? 'tomorrow' : `${u.days} days left`}</span>
                    </>}
                    {u.kind === 'gold' && <>
                      <span className="block font-semibold">Gold bought for {u.group_name}</span>
                      <span className="block text-xs text-ink-3">{fullDate(u.date)} · <span className="num">{kwacha(u.amount)}</span> waiting</span>
                    </>}
                    {u.kind === 'matures' && <>
                      <span className="block font-semibold">{u.group_name} matures {fullDate(u.date)}</span>
                      <span className="block text-xs text-ink-3">Annuity · period {u.period_index} of {u.term_cycles}</span>
                    </>}
                  </span>
                  <Icon name="chevron" size={18} className="text-ink-3" />
                </a>
              ))}
            </Card>
          )}
          {me.kyc_status !== 'VERIFIED' && (
            <Card className="flex flex-col gap-2 !border-gold-tint-line !bg-gold-tint">
              <span className="font-display font-semibold">Verify your identity</span>
              <span className="text-sm text-gold-muted">Add your NRC to borrow against your gold and receive payouts.</span>
              <LinkButton variant="soft" href="#/me" className="mt-1 self-start">Add NRC</LinkButton>
            </Card>
          )}
        </div>
      </div>

      <Card className="flex flex-col gap-2 !p-0">
        <div className="flex items-center justify-between px-4 pt-4 lg:px-6 lg:pt-5">
          <h2 className="font-display text-[17px] font-semibold lg:text-xl">Your savings groups</h2>
          <a href="#/groups" className="text-sm font-semibold">Join or create</a>
        </div>
        {data.holdings.length === 0 && <p className="px-4 pb-5 text-ink-3 lg:px-6">You're not in a group yet.</p>}
        <div className="overflow-x-auto">
          <table className="w-full min-w-[640px] border-collapse text-sm">
            <thead className="sr-only sm:not-sr-only">
              <tr className="text-left text-xs uppercase tracking-[0.08em] text-ink-3">
                <th className="px-4 py-2.5 font-semibold lg:px-6">Group</th>
                <th className="px-3 py-2.5 font-semibold">Model</th>
                <th className="px-3 py-2.5 text-right font-semibold">Monthly</th>
                <th className="px-3 py-2.5 text-right font-semibold">Your share</th>
                <th className="px-3 py-2.5 font-semibold">Status</th>
                <th className="px-4 py-2.5 lg:px-6"><span className="sr-only">Action</span></th>
              </tr>
            </thead>
            <tbody>
              {data.holdings.map((h) => (
                <tr key={h.group} className="border-t border-track">
                  <td className="px-4 py-3.5 lg:px-6">
                    <a href={`#/groups/${h.group}`} className="font-bold">{h.group_name}</a>
                    <div className="text-xs text-ink-3">{h.member_count} members · {METAL[h.metal]}{h.is_admin ? ' · you admin' : ''}</div>
                  </td>
                  <td className="px-3 py-3.5 text-ink-2">{h.group_type === 'ANNUITY' ? 'Annuity' : 'Tontine (rotating)'}</td>
                  <td className="num px-3 py-3.5 text-right font-semibold">{kwacha(h.contribution_amount)}</td>
                  <td className="px-3 py-3.5 text-right">
                    <div className="num font-semibold">{grams(h.grams)}</div>
                    <div className="num text-xs text-ink-3">{kwacha(h.value_zmw)}</div>
                  </td>
                  <td className="px-3 py-3.5"><StatusChip value={h.group_status} /></td>
                  <td className="px-4 py-3.5 text-right lg:px-6">
                    {h.group_status === 'ACTIVE'
                      ? (h.paid_this_period
                        ? <Chip tone="positive">Paid</Chip>
                        : <LinkButton variant="soft" href={`#/contribute/${h.group}`} className="!min-h-11 !px-4 text-sm">Contribute</LinkButton>)
                      : <LinkButton variant="secondary" href={`#/groups/${h.group}`} className="!min-h-11 !px-4 text-sm">Details</LinkButton>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card className="flex flex-col gap-1">
        <div className="mb-1 flex items-center justify-between">
          <h2 className="font-display text-[17px] font-semibold lg:text-xl">Recent activity</h2>
          <a href="#/ledger" className="text-sm font-semibold">Full ledger</a>
        </div>
        {(activity.data?.results || []).length === 0 && <p className="py-3 text-ink-3">Nothing yet. Your first contribution will show here.</p>}
        {(activity.data?.results || []).slice(0, 5).map((t) => (
          <div key={t.id} className="flex items-center justify-between gap-3 border-t border-track py-3.5 first:border-t-0">
            <span className="min-w-0">
              <span className="block font-semibold">{t.kind === 'BUY' ? 'Gold bought' : 'Gold sold'} · {t.group_name}</span>
              <span className="block text-xs text-ink-3">{dayMonth(t.created_at)} · {perGram(t.price_per_gram)}</span>
            </span>
            <span className="text-right">
              <span className={`num block font-semibold ${t.kind === 'BUY' ? 'text-positive' : 'text-ink'}`}>{grams(t.kind === 'BUY' ? t.grams : `-${t.grams}`, { signed: true })}</span>
              <span className="num block text-xs text-ink-3">{kwacha(t.gross_zmw)}</span>
            </span>
          </div>
        ))}
      </Card>
    </>
  )
}
