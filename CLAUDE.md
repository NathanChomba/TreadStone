# Treadstone — Project Context

Final-year ZUCoT (BSc Software Engineering) project: a community-based digital Tontine and Annuity platform. Pooled contributions are converted into gold/silver holdings through the Zambia Gold Company Limited (ZGCL) as custodian, so payouts in ZMW reflect the metal's value instead of a depreciating Kwacha.

Visual and interaction rules for the frontend live in **`DESIGN.md`** (tokens, components, screens, behaviour). Read it before touching UI.

## Environment (Windows, 12 GB RAM)
- Python 3.13, Node 26, npm 12, PostgreSQL 17 (psql on PATH). Django 6.1, DRF 3.18, Django-Q2 1.11, React 19, Vite 8, Tailwind 4.
- Terminal: PowerShell. Activate the venv with `.\venv\Scripts\Activate.ps1` (or call `backend\venv\Scripts\python.exe` directly).
- No Redis: it doesn't run natively on Windows. Do NOT suggest Celery.
- No Android emulator / Flutter. The frontend is a PWA.
- The VS Code terminal is not elevated; anything needing admin (firewall) goes through a self-elevating `.bat` or an admin PowerShell.

## Stack (decided — don't change without asking)
- Frontend: React (Vite) + Tailwind CSS v4 (`@tailwindcss/vite`) + `vite-plugin-pwa`, ESLint. No router library (hash routing in `App.jsx`).
- Backend: Django + Django REST Framework (token auth), django-cors-headers, python-dotenv
- Database: PostgreSQL 17, database name `treadstone`
- Background jobs: Django-Q2 with the ORM broker (PostgreSQL). Worker: `python manage.py qcluster` (does NOT auto-reload on code changes — restart it).
- External services: mobile money sandboxes, a metal price API, Africa's Talking (SMS, optional USSD), and a SIMULATED ZGCL custodian (no real ZGCL API exists)

## Layout
```
C:\Treadstone
├── CLAUDE.md, DESIGN.md
├── start.bat          double-click: API + worker + PWA in one Windows Terminal window, opens browser
├── allow-phone.bat    one-time, self-elevating: firewall rule for port 5173 + prints the LAN URL
├── .vscode\tasks.json Ctrl+Shift+B "Start Treadstone"
├── backend\           Django project (config\ = settings, urls, errors.py), venv\, .env, .env.example, requirements.txt
│   ├── apps: members, savings, loans, metals, payouts
│   ├── integrations\  mobile_money.py (simulated provider), sms.py (Africa's Talking; prints to console without a key)
│   ├── templates\admin\  Treadstone admin theme (base_site.html, loans/loan/change_form.html)
│   └── static\treadstone\admin.css
└── frontend\          Vite React PWA (dev server :5173, host: true; proxies /api, /admin, /static to 127.0.0.1:8000)
    └── src\ App.jsx, api.js (fetch + formatters), hooks.js, ui.jsx (component kit), index.css (@theme tokens), pages\
```

## Rules
- Offline: cache GET responses only (balances, history, last price). Contributions, loans and payouts require a live connection. Never queue payments offline (`api.js` refuses non-GET when offline).
- Money: use DecimalField / Decimal, never float. Metal quantities are stored in grams with 4 decimal places. Frontend formats money from strings (`kwacha()`, `grams()` in `api.js`), true minus sign.
- Secrets live in backend\.env, which is never committed. Never put real passwords in this file.
- TIME_ZONE = "Africa/Lusaka"
- Don't invent data presented as real: simulated things (custodian, mobile money, price history before the live feed) are labelled as simulated in the UI.

## Running
Quickest: double-click `start.bat`, or Ctrl+Shift+B in VS Code. Manual equivalent:
1. `cd backend; .\venv\Scripts\Activate.ps1; python manage.py runserver`
2. Second terminal: activate the venv, then `python manage.py qcluster`
3. Third terminal: `cd frontend; npm run dev`

One-time setup on a fresh database: `python manage.py migrate`, `createsuperuser`, `setup_schedules`, optionally `seed_price_history --days 365` (simulated history for the 6M/1Y charts; refuses to run with a real price provider).

Phone on the same Wi-Fi: run `allow-phone.bat` once, then open `http://<PC-IP>:5173` (last known 172.18.6.11; `ipconfig` shows the current one). Django trusts the PC's LAN origins for CSRF automatically when DEBUG. Campus Wi-Fi may isolate clients → use the phone's hotspot. PWA install/offline needs HTTPS (not set up; a Cloudflare tunnel was offered).

Tests: `cd backend; python manage.py test` (18 passing, in `savings/tests.py`). Frontend: `npm run lint`, `npm run build`.

Admin: `/admin/` (also via :5173). Staff approve loans (buttons on the loan page or list action), verify KYC (Members action), and can force "Buy gold now" (Savings groups action).

## Architecture notes
- `members.Member` is the custom user (AUTH_USER_MODEL); logs in by phone (`+260` + 9x/7x, e.g. +260971234567). Fields also: nrc_number, kyc_status, language (en/bem/nya), sms_reminders, price_alerts.
- Business rules live in each app's `services.py`; views stay thin. Rule failures raise `config.errors.DomainError` subclasses, which the API returns as 400 `{"detail": ...}`.
- `metals.CustodianTransaction` is the append-only metal ledger. Balances = BUY grams − SELL grams (`metals/custodian.py`, which also has `quote()`). 1% custodian fee on buys and sells (`CUSTODIAN_FEE_PERCENT`).
- Prices: `metals/prices.py` (simulated random walk by default, goldapi.io optional), fetched every 15 min by `metals.tasks.fetch_prices`, which also sends price alerts (≥3% in 24 h). Chart data: `metals/history.py` (1D/1W/1M/6M/1Y, ≤60 points). Rows with source `simulated-history` are seeded, not real.
- Contributions: collected at once → status RECEIVED with receipt `TS-yymm-dd-nnnn`; pooled and bought as metal on the group's due date (`due_day`, default 10th; weekly groups use the start weekday) by the daily 06:00 task `savings.tasks.daily`, which also sends reminders 2 days before. Due-date maths: `savings/dues.py`. Statuses: PENDING → RECEIVED → COMPLETED, or FAILED.
- Group types: ROTATING (fixed amount per cycle; pot to position N in cycle N; payout only after everyone paid AND that cycle's gold is bought; group CLOSES after the last cycle) and ANNUITY (active at creation, min deposit, `term_cycles` periods to maturity, withdraw own grams).
- Loans only against ANNUITY balances (rotating-group grams all go to someone's pot). Need KYC VERIFIED. 50% LTV, 10% flat interest, no term/instalments. Collateral grams are locked while PENDING/ACTIVE. Approved by staff, not group admins.
- Notifications: `members.notify.notify()` writes the in-app notification AND queues the SMS. Use it instead of calling `queue_sms` directly.
- Wallets: `members.MobileWallet` (MTN 096/076, Airtel 097/077, Zamtel 095), one default; payouts and loans go to the default; each contribution records provider + number. Logic in `members/wallets.py`.
- Simulated mobile money: numbers ending 0000 fail payment.
- Dashboard API (`/api/auth/dashboard/`) returns holdings, up_next, contributed/paid_out/awaiting_gold, and `preserved_zmw` = value + paid out − contributions already bought (can be negative because of fees/price moves; the UI shows it honestly).
- Main API routes: `/api/auth/{register,login,logout,me,dashboard,password,wallets,notifications}/`, `/api/groups/` (+ `join`, `{id}/start|payout|remind`), `/api/contributions/`, `/api/payouts/` (+ `withdraw/`), `/api/loans/` (+ `{id}/repay|approve|reject`, `limit/`), `/api/metals/{prices/latest,prices,history,quote,ledger}/`.

## Frontend
- Rebuilt to DESIGN.md (white + gold, Sora/Manrope/JetBrains Mono, hexagon-T logo). Phone: 5-tab bar Home · Groups · Vault · Ledger · Me (hidden inside the contribute flow). Desktop ≥1024: sidebar adds Loans.
- Routes (`#/…`): `/`, `/groups`, `/groups/:id`, `/contribute/:id` (4 steps: amount → pay from → review with quote → done), `/vault` (1W/1M/6M/1Y), `/ledger`, `/loans`, `/me` (KYC, wallets, switches, language, change password), `/notifications` (bell polls every 60 s).
- Old dark/amber UI and `History.jsx` are gone.

## Design artifacts (claude.ai)
- User's "Treadstone UI Overhaul" canvas (10 screens) — source of DESIGN.md.
- "Treadstone Onboarding & Admin" canvas: https://claude.ai/artifact/LmmFcaBTfv2PE37XrW4cYZ (sign-up, KYC, create/join, group admin).

## Status
- [x] Setup: tools, DB, apps, settings, Vite config, `.env`, git initialised (nothing committed yet — commit only when the user asks)
- [x] Models, migrations, services, API, admin, tests (18 passing)
- [x] Superuser exists (patience, +260969313747); demo member Nathan (+260969920388, KYC verified); groups kalewa (annuity) and senior (rotating, closed)
- [x] Frontend rebuilt to DESIGN.md, all screens above
- [x] Django admin themed to match (cards, chips, member list with gold share, loan page with approve/reject buttons)
- [x] Gold bought on due date, due dates / Up next, contribute flow, multiple wallets, notifications + SMS reminders + price alerts, chart ranges, settings
- [x] One-click start (`start.bat`), phone access on LAN (`allow-phone.bat`)
- [ ] Real mobile money sandbox (MTN MoMo / Airtel) with async callbacks; USSD
- [ ] Loan terms per DESIGN (monthly interest, term, instalment schedule) — backend is flat 10%, no schedule
- [ ] Loan default handling (selling collateral)
- [ ] Bemba / Nyanja translations (preference stored; needs a fluent speaker — don't machine-invent them)
- [ ] Fingerprint unlock (WebAuthn)
- [ ] HTTPS for phone install (e.g. Cloudflare tunnel); production deployment

## Report notes
- Tech stack is written up in Chapter 4, section 4.5 Software Development Tools (not 3.4).
- Wording in the report: "a responsive Progressive Web App accessible on mobile and desktop browsers".
