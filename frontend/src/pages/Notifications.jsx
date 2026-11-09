import { useEffect } from 'react'
import { api, dayMonth, time24 } from '../api'
import { useApi } from '../hooks'
import { Alert, Card, Chip, Icon, Loading, PageTitle } from '../ui'

const KIND = {
  PAYMENT: ['gold', 'Payment'],
  GOLD: ['gold', 'Gold bought'],
  PAYOUT: ['positive', 'Payout'],
  LOAN: ['info', 'Loan'],
  REMINDER: ['gold', 'Reminder'],
  PRICE: ['neutral', 'Price alert'],
  GROUP: ['neutral', 'Group'],
}

export default function Notifications({ refreshUnread }) {
  const { data, loading, error } = useApi('/auth/notifications/')

  // Opening the list marks everything read.
  useEffect(() => {
    if (data?.unread) {
      api('/auth/notifications/read/', { method: 'POST' }).then(refreshUnread).catch(() => {})
    }
  }, [data, refreshUnread])

  return (
    <>
      <PageTitle back="#/" title="Notifications" sub="Payments, gold purchases, payouts and reminders. Each one is also sent by SMS." />
      {loading && !data && <Loading />}
      {error && !data && <Alert>{error.message}</Alert>}
      {data && data.results.length === 0 && <Card><p className="text-ink-3">Nothing yet.</p></Card>}
      {data && data.results.length > 0 && (
        <Card className="flex flex-col !py-1">
          {data.results.map((n) => {
            const [tone, label] = KIND[n.kind] || KIND.GROUP
            const body = (
              <span className="flex min-w-0 flex-1 flex-col gap-1">
                <span className="flex flex-wrap items-center gap-2">
                  <Chip tone={tone}>{label}</Chip>
                  {!n.read_at && <span className="h-2 w-2 rounded-full bg-gold" aria-label="Unread" />}
                  <span className="ml-auto text-xs text-ink-3">{dayMonth(n.created_at)} · {time24(n.created_at)}</span>
                </span>
                <span className="font-semibold text-ink">{n.title}</span>
                <span className="text-sm text-ink-2">{n.body}</span>
              </span>
            )
            return (
              <div key={n.id} className="border-t border-track py-3.5 first:border-t-0">
                {n.link ? (
                  <a href={`#${n.link}`} className="flex items-center gap-3 no-underline">{body}<Icon name="chevron" className="text-ink-3" /></a>
                ) : body}
              </div>
            )
          })}
        </Card>
      )}
    </>
  )
}
