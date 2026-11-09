// Treadstone live demo: five scripted agents use the real app in visible browser windows.
// They are NOT AI - each follows a fixed script, clicking and typing like a person would,
// against the real Django API and database. Run with run-live-demo.bat (start.bat must be running).
//
// Options (environment variables):
//   DEMO_URL=http://localhost:5173   app address
//   DEMO_CHANNEL=msedge              msedge | chrome | chromium
//   DEMO_SPEED=1                     2 = twice as fast, 0.5 = half speed
//   DEMO_ADMIN=1                     0 = don't open the admin window
//   DEMO_AUTO=0                      1 = don't wait for Enter between phases (testing)

const { chromium } = require('playwright-core')
const path = require('path')
const readline = require('readline')

const BASE = (process.env.DEMO_URL || 'http://localhost:5173').replace(/\/$/, '')
const CHANNEL = process.env.DEMO_CHANNEL || 'msedge'
const SPEED = Number(process.env.DEMO_SPEED || 1)
const SHOW_ADMIN = process.env.DEMO_ADMIN !== '0'
const AUTO = process.env.DEMO_AUTO === '1'
const PASSWORD = 'Demo@2026'

const wait = (ms) => new Promise((r) => setTimeout(r, ms / SPEED))
const log = (who, msg) => console.log(`[${new Date().toLocaleTimeString()}] ${who.padEnd(14)} ${msg}`)

const AGENTS = [
  { name: 'Mwila Banda', role: 'Market trader · K500 a month since Mar 2024', phone: '0971000001', start: 0, script: mwila },
  { name: 'Grace Phiri', role: 'Teacher · K300 a month', phone: '0971000002', start: 5, script: grace },
  { name: 'Joseph Chanda', role: 'Hardware shop · borrows against his gold', phone: '0971000003', start: 10, script: joseph },
  { name: 'Mutale Zulu', role: 'Maize farmer · pays after each harvest', phone: '0971000004', start: 15, script: mutale },
  { name: 'Natasha Mumba', role: 'Joined late (Jun 2025, near the peak)', phone: '0971000005', start: 20, script: natasha },
]

// ---------- what panelists see in every window: a name bar and a gold ring on every click ----------
function overlayScript({ name, role }) {
  const install = () => {
    if (document.getElementById('__agent_bar')) return
    const bar = document.createElement('div')
    bar.id = '__agent_bar'
    bar.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:2147483647;display:flex;flex-direction:column;' +
      'gap:2px;padding:7px 12px;background:#1F1A10;color:#F5E6B8;font:600 13px/1.25 system-ui,sans-serif;' +
      'box-shadow:0 2px 8px rgba(0,0,0,.25);pointer-events:none'
    bar.innerHTML = `<span><span style="color:#D4AF37">●</span> Scripted agent: ${name} <span style="opacity:.65;font-weight:500">· ${role}</span></span>` +
      '<span id="__agent_status" style="font-weight:500;color:#fff">Starting…</span>'
    document.body.appendChild(bar)
    document.body.style.paddingTop = '52px'
    window.__agentStatus = (t) => { document.getElementById('__agent_status').textContent = t }
    document.addEventListener('mousedown', (e) => {
      const r = document.createElement('div')
      r.style.cssText = `position:fixed;left:${e.clientX - 18}px;top:${e.clientY - 18}px;width:36px;height:36px;` +
        'border:3px solid #D4AF37;border-radius:50%;z-index:2147483647;pointer-events:none;' +
        'transition:transform .5s ease-out,opacity .5s ease-out;background:rgba(212,175,55,.25)'
      document.body.appendChild(r)
      requestAnimationFrame(() => { r.style.transform = 'scale(1.8)'; r.style.opacity = '0' })
      setTimeout(() => r.remove(), 600)
    }, true)
  }
  if (document.body) install()
  else document.addEventListener('DOMContentLoaded', install)
}

async function status(a, text) {
  log(a.name, text)
  await a.page.evaluate((t) => window.__agentStatus && window.__agentStatus(t), text).catch(() => {})
}

// ---------- reusable steps (selectors come from the real React pages) ----------
async function login(a) {
  const p = a.page
  await status(a, 'Opening Treadstone…')
  await p.goto(BASE + '/')
  await p.getByLabel('Mobile money number').waitFor()
  await wait(1200)
  await status(a, 'Logging in with mobile money number')
  await p.getByLabel('Mobile money number').click()
  await p.getByLabel('Mobile money number').pressSequentially(a.phone, { delay: 90 / SPEED })
  await p.locator('input[type=password]').click()
  await p.locator('input[type=password]').pressSequentially(PASSWORD, { delay: 70 / SPEED })
  await wait(500)
  await p.locator('form button[type=submit]').click()
  await p.locator('text=Preserved vs cash >> visible=true').first().waitFor({ timeout: 20000 })
  await wait(1500)
  await status(a, `Dashboard - preserved vs cash: ${await preserved(a)}`)
  await wait(3500)
}

async function preserved(a) {
  const tile = a.page.locator('text=Preserved vs cash >> visible=true').first().locator('xpath=..')
  return (await tile.innerText()).split('\n').find((l) => /K/.test(l)) || '?'
}

async function tab(a, href, heading) {
  const link = a.page.locator(`a[href="${href}"]:visible`).first()
  // Inside the payment flow the tab bar is hidden; then go there directly.
  if (await link.count()) await link.click()
  else await a.page.goto(BASE + '/' + href)
  if (heading) await a.page.locator(`text=${heading} >> visible=true`).first().waitFor()
  await wait(1200)
}

async function contribute(a, { preset, other }) {
  const p = a.page
  const amount = other ? `K${other}` : preset
  await status(a, `Contributing ${amount}`)
  await p.getByRole('link', { name: 'Contribute' }).first().click()
  await p.getByRole('heading', { name: 'How much?' }).waitFor()
  await wait(1000)
  if (other) {
    await p.getByRole('radio', { name: 'Other' }).click()
    await p.getByLabel('Amount (ZMW)').pressSequentially(String(other), { delay: 120 / SPEED })
  } else {
    await p.getByRole('radio', { name: preset, exact: true }).click()
  }
  await wait(800)
  await p.getByRole('button', { name: 'Continue' }).click()
  await status(a, 'Choosing mobile money wallet')
  await p.getByRole('heading', { name: 'Pay from' }).waitFor()
  await wait(1200)
  await p.getByRole('button', { name: 'Review' }).click()
  await p.getByRole('heading', { name: 'Check and pay' }).waitFor()
  await status(a, `Reviewing: ${amount} ≈ ${(await p.getByText('≈').first().innerText()).replace('≈', '').trim()} of gold at today's live price`)
  await wait(3000)
  await p.getByRole('button', { name: /^Pay K/ }).click()
  await status(a, 'Waiting for mobile money confirmation…')
  await p.getByRole('heading', { name: /received/ }).waitFor({ timeout: 20000 })
  const ref = await p.getByText(/^TS-/).first().innerText().catch(() => '')
  await status(a, `Paid ${amount} · receipt ${ref} · gold is bought on the due date`)
  await wait(3500)
}

// ---------- the five scripts ----------
async function mwila(a) {
  await login(a)
  await contribute(a, { other: 500 })
  await tab(a, '#/', 'Preserved vs cash')
  await status(a, `Back on dashboard - K500 waiting for tomorrow's gold purchase`)
}

async function grace(a) {
  await login(a)
  await contribute(a, { preset: 'K300' })
  await status(a, 'Checking her ledger')
  await tab(a, '#/ledger', 'Ledger & history')
  await a.page.mouse.wheel(0, 500)
  await wait(2500)
  await status(a, 'Ledger: every kwacha in and the gold it bought')
}

async function joseph(a) {
  const p = a.page
  await login(a)
  await status(a, 'Looking at the real gold price history (1 year)')
  await tab(a, '#/vault', 'Vault & metals')
  await p.getByRole('button', { name: '1Y', exact: true }).first().click({ timeout: 5000 }).catch(() => {})
  await wait(3500)
  await status(a, 'Applying for a loan secured by his gold')
  await tab(a, '#/', 'Preserved vs cash')
  await p.getByRole('link', { name: 'Loan' }).first().click()
  await p.locator('text=You can borrow up to >> visible=true').first().waitFor()
  await wait(2000)
  await p.getByLabel('How much?').click()
  await p.getByLabel('How much?').pressSequentially('5000', { delay: 140 / SPEED })
  await wait(1500)
  await p.getByRole('button', { name: 'Send request' }).click()
  await p.getByText(/sent\./).waitFor({ timeout: 15000 })
  await status(a, 'Loan of K5,000 requested - waiting for officer approval (gold held as collateral)')
}

async function mutale(a) {
  await login(a)
  await status(a, 'Reviewing his harvest-time gold purchases')
  await tab(a, '#/ledger', 'Ledger & history')
  for (let i = 0; i < 4; i++) { await a.page.mouse.wheel(0, 350); await wait(1200) }
  await wait(1500)
  await tab(a, '#/', 'Preserved vs cash')
  await status(a, `Saved after harvests only - preserved vs cash: ${await preserved(a)}`)
}

async function natasha(a) {
  await login(a)
  await status(a, `Joined near the 2025 peak - preserved vs cash: ${await preserved(a)} (the honest risk case)`)
  await wait(4000)
  await tab(a, '#/vault', 'Vault & metals')
  await status(a, 'Checking today\'s price before adding more')
  await wait(3000)
  await tab(a, '#/', 'Preserved vs cash')
  await contribute(a, { preset: 'K1,500' })
}

// ---------- phase 2: after the presenter acts in the admin window ----------
async function refresh(a) {
  const p = a.page
  await p.goto(BASE + '/#/')
  await p.reload()
  await p.locator('text=Preserved vs cash >> visible=true').first().waitFor({ timeout: 20000 })
  if (a.name === 'Joseph Chanda') {
    await p.getByRole('link', { name: 'Loan' }).first().click()
    await p.locator('text=Your loans >> visible=true').first().waitFor()
    await status(a, 'Loan status updated by the officer')
  } else {
    await status(a, `Updated - preserved vs cash: ${await preserved(a)}`)
  }
}

// ---------- window layout ----------
async function placeWindow(page, { left, top, width, height }) {
  const s = await page.context().newCDPSession(page)
  const { windowId } = await s.send('Browser.getWindowForTarget')
  await s.send('Browser.setWindowBounds', { windowId, bounds: { windowState: 'normal' } })
  await s.send('Browser.setWindowBounds', { windowId, bounds: { left, top, width, height } })
}

function slots(screenW, screenH) {
  const cols = 3, rows = 2, w = Math.floor(screenW / cols), h = Math.floor(screenH / rows)
  return Array.from({ length: 6 }, (_, i) => ({ left: (i % cols) * w, top: Math.floor(i / cols) * h, width: w, height: h }))
}

async function launch(options = {}) {
  const tries = CHANNEL === 'chromium' ? [undefined] : [CHANNEL, 'chrome', undefined]
  let lastErr
  for (const channel of tries) {
    try {
      return await chromium.launch({ headless: false, channel, slowMo: 60 / SPEED, args: ['--disable-features=Translate'], ...options })
    } catch (e) { lastErr = e }
  }
  throw lastErr
}

function pressEnter(question) {
  if (AUTO) return wait(4000)
  return new Promise((resolve) => {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout })
    rl.question(question, () => { rl.close(); resolve() })
  })
}

async function main() {
  console.log(`Treadstone live demo - app at ${BASE}\n`)
  const browser = await launch()

  // Measure the screen with a first window, then tile everything in a 3x2 grid.
  const first = await browser.newContext({ viewport: null })
  const firstPage = await first.newPage()
  const [sw, sh] = await firstPage.evaluate(() => [screen.availWidth, screen.availHeight])
  const grid = slots(sw, sh)

  for (const [i, a] of AGENTS.entries()) {
    a.context = i === 0 ? first : await browser.newContext({ viewport: null })
    a.page = i === 0 ? firstPage : await a.context.newPage()
    await a.context.addInitScript(overlayScript, { name: a.name, role: a.role })
    await placeWindow(a.page, grid[i])
    await a.page.goto('about:blank')
  }

  let admin
  if (SHOW_ADMIN) {
    // Kept in its own profile so the admin login is remembered between runs.
    admin = await chromium.launchPersistentContext(path.join(__dirname, '.admin-profile'), {
      headless: false, viewport: null, channel: CHANNEL === 'chromium' ? undefined : CHANNEL,
    }).catch(() => null)
    if (admin) {
      const ap = admin.pages()[0] || await admin.newPage()
      await placeWindow(ap, grid[5])
      await ap.goto(BASE + '/admin/savings/savingsgroup/')
    }
  }

  await pressEnter('\nWindows are ready. Press Enter to start the agents… ')

  // Phase 1: each agent starts a few seconds after the previous one so the panel can follow.
  await Promise.all(AGENTS.map(async (a) => {
    await wait(a.start * 1000)
    try { await a.script(a) } catch (e) {
      await status(a, `⚠ Stopped: ${String(e.message).split('\n')[0]}`)
    }
  }))

  console.log('\nPhase 1 done. In the admin window (bottom right):')
  console.log('  1. Savings groups -> tick "Copperbelt Gold Savers" -> Action "Buy gold now" -> Go')
  console.log('  2. Loans -> open Joseph Chanda\'s pending loan -> Approve')
  await pressEnter('Then press Enter here to refresh every agent… ')

  // Phase 2: every agent reloads and shows the result of the officer's actions.
  await Promise.all(AGENTS.map((a) => refresh(a).catch((e) => status(a, `⚠ ${String(e.message).split('\n')[0]}`))))

  await pressEnter('\nDemo finished. Press Enter to close all windows… ')
  await browser.close()
  if (admin) await admin.close()
}

main().catch((e) => { console.error(e); process.exit(1) })
