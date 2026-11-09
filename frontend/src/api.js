// Thin wrapper around fetch for the Django API (proxied at /api by Vite),
// plus the display formatters from DESIGN.md section 4.

const TOKEN_KEY = 'treadstone.token'

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    // storage unavailable (private mode); the session just won't persist
  }
}

export class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.status = status
    this.data = data
  }
}

function messageFrom(data, fallback) {
  if (!data) return fallback
  if (typeof data === 'string') return data
  if (data.detail) return data.detail
  if (data.non_field_errors) return data.non_field_errors.join(' ')
  const first = Object.entries(data)[0]
  if (first) return `${first[0].replace(/_/g, ' ')}: ${[].concat(first[1]).join(' ')}`
  return fallback
}

export async function api(path, { method = 'GET', body } = {}) {
  // Money-moving calls need a live connection. Fail fast instead of queuing.
  if (method !== 'GET' && !navigator.onLine) {
    throw new ApiError('You are offline. This needs a live connection.', 0)
  }
  const headers = { Accept: 'application/json' }
  const token = getToken()
  if (token) headers.Authorization = `Token ${token}`
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  let res
  try {
    res = await fetch(`/api${path}`, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) })
  } catch {
    throw new ApiError('Could not reach Treadstone. Check your connection.', 0)
  }
  const text = await res.text()
  let data
  try {
    data = text ? JSON.parse(text) : null
  } catch {
    data = text
  }
  if (!res.ok) {
    if (res.status === 401) setToken(null)
    throw new ApiError(messageFrom(data, `Request failed (${res.status})`), res.status, data)
  }
  return data
}

// ---- formatting (string-based: money never goes through float maths) ----

const MINUS = '−'

function splitDecimal(value, dp) {
  const s = String(value ?? '0')
  const negative = s.startsWith('-')
  const [whole, frac = ''] = s.replace('-', '').split('.')
  return { negative, whole: whole || '0', frac: frac.padEnd(dp, '0').slice(0, dp) }
}

const commas = (digits) => digits.replace(/\B(?=(\d{3})+(?!\d))/g, ',')

// K1,981.84 ; signed: +K131.84 / −K1,000.00
export function kwacha(value, { signed = false } = {}) {
  if (value === null || value === undefined || value === '') return '—'
  const { negative, whole, frac } = splitDecimal(value, 2)
  const isZero = /^0*$/.test(whole + frac)
  const sign = negative && !isZero ? MINUS : signed && !isZero ? '+' : ''
  return `${sign}K${commas(whole)}.${frac}`
}

// 0.8866 g ; signed: +0.4474 g / −1.6214 g
export function grams(value, { signed = false } = {}) {
  if (value === null || value === undefined || value === '') return '—'
  const { negative, whole, frac } = splitDecimal(value, 4)
  const isZero = /^0*$/.test(whole + frac)
  const sign = negative && !isZero ? MINUS : signed && !isZero ? '+' : ''
  return `${sign}${whole}.${frac} g`
}

export const perGram = (value) => `${kwacha(value)} / g`

export const isNegative = (value) => String(value ?? '').startsWith('-') && !/^-0*(\.0*)?$/.test(String(value))

export const METAL = { XAU: 'Gold', XAG: 'Silver' }

// 097 123 4567
export function localPhone(phone) {
  if (phone && phone.startsWith('+260') && phone.length === 13) {
    const d = `0${phone.slice(4)}`
    return `${d.slice(0, 3)} ${d.slice(3, 6)} ${d.slice(6)}`
  }
  return phone || ''
}

// +260971234567 from what a member types ("097 123 4567", "0971234567", "+260 97...")
export function toE164(input) {
  const digits = String(input).replace(/\D/g, '')
  if (digits.startsWith('260')) return `+${digits}`
  if (digits.startsWith('0')) return `+260${digits.slice(1)}`
  return `+260${digits}`
}

const LOCALE = 'en-GB'
export const dayMonth = (iso) => new Date(iso).toLocaleDateString(LOCALE, { day: 'numeric', month: 'short' })
export const fullDate = (iso) => new Date(iso).toLocaleDateString(LOCALE, { day: 'numeric', month: 'short', year: 'numeric' })
export const time24 = (iso) => new Date(iso).toLocaleTimeString(LOCALE, { hour: '2-digit', minute: '2-digit', hour12: false })
export const longToday = () => new Date().toLocaleDateString(LOCALE, { weekday: 'long', day: 'numeric', month: 'long' })

export function greeting() {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
}

export function initials(first, last) {
  return `${(first || '?')[0]}${(last || '')[0] || ''}`.toUpperCase()
}

// A price older than 15 minutes is shown as stale (DESIGN.md section 9).
export const isStale = (iso) => Date.now() - new Date(iso).getTime() > 15 * 60 * 1000
