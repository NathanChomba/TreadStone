import { useCallback, useEffect, useState } from 'react'
import { api } from './api'

export function useOnline() {
  const [online, setOnline] = useState(navigator.onLine)
  useEffect(() => {
    const on = () => setOnline(true)
    const off = () => setOnline(false)
    window.addEventListener('online', on)
    window.addEventListener('offline', off)
    return () => {
      window.removeEventListener('online', on)
      window.removeEventListener('offline', off)
    }
  }, [])
  return online
}

// GET data. When offline, the service worker answers from its cache.
export function useApi(path) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const [tick, setTick] = useState(0)
  const reload = useCallback(() => setTick((t) => t + 1), [])

  useEffect(() => {
    if (!path) return undefined
    let alive = true
    api(path)
      .then((data) => alive && setState({ data, error: null, loading: false }))
      .catch((error) => alive && setState((s) => ({ data: s.data, error, loading: false })))
    return () => {
      alive = false
    }
  }, [path, tick])

  return { ...state, reload }
}

// Latest price plus history over a range (1D, 1W, 1M, 6M, 1Y) for one metal.
export function usePrice(metal, range = '1M') {
  const latest = useApi('/metals/prices/latest/')
  const history = useApi(`/metals/history/?metal=${metal}&range=${range}`)
  const current = (latest.data || []).find((p) => p.metal === metal) || null
  const points = (history.data?.points || []).map((p) => Number(p.price))
  return { current, points, changePct: history.data?.change_pct ?? null, all: latest.data || [], loading: latest.loading }
}

export function useHashRoute() {
  const read = () => window.location.hash.replace(/^#/, '') || '/'
  const [route, setRoute] = useState(read)
  useEffect(() => {
    const onChange = () => setRoute(read())
    window.addEventListener('hashchange', onChange)
    return () => window.removeEventListener('hashchange', onChange)
  }, [])
  return route
}

export function go(path) {
  window.location.hash = path
}

// Runs an async action with busy/error/success state. Used by every form that moves money.
export function useAction() {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  async function run(fn, successMessage) {
    setBusy(true)
    setError('')
    setSuccess('')
    try {
      const result = await fn()
      if (successMessage) setSuccess(typeof successMessage === 'function' ? successMessage(result) : successMessage)
      return result
    } catch (e) {
      setError(e.message)
      return null
    } finally {
      setBusy(false)
    }
  }
  return { busy, error, success, run, setError }
}
