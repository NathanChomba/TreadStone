*Treadstone*

A precious metals-backed digital tontine and annuity system for preserving the value of community savings in Zambia.

Community savings groups lose value to inflation and kwacha depreciation: money saved today is worth less by the time it is paid out. Treadstone runs the group digitally and converts each contribution into gold or silver, so members are paid out in kwacha at the current metal price instead of the depreciated cash value.

Final-year project, Bachelor of Software Engineering, Zambia University College of Technology (ZUCoT), 2026.

*Features*
Tontine and Annuity groups: rotating pot (tontine) or individual metal balances withdrawn later (annuity), in gold or silver, with weekly or monthly schedules.
*Contributions to metal:* each payment is collected by mobile money and bought as metal through the custodian at the latest price, minus a fee.
*Preserved vs cash:* every balance is shown next to what the same money would be worth held as kwacha.
*Payouts:* metal is sold at the current price and disbursed to the member's mobile money wallet.
*Loans:* members borrow against their metal holdings, with a limit, interest and repayment tracking.
*Live and historical prices:* daily gold and silver prices (GoldAPI) converted to ZMW, with price history charts.
*Notifications and SMS:* due-date reminders, price alerts and payout notices (Africa's Talking).
*Admin panel:* a branded Django admin for group administrators, including loan approval.
*Installable PWA:* phone-first design for low-end Android on 3G, with a desktop layout.

*Tech stack*
Layer	Technology
Frontend	React 19, Vite, Tailwind CSS v4, vite-plugin-pwa
Backend	Python, Django 6, Django REST Framework
Background jobs	Django-Q2 (scheduled price updates, reminders, SMS)
Database	PostgreSQL 17
Integrations	GoldAPI (prices), Africa's Talking (SMS), mobile money adapter
Architecture
frontend/   React PWA (phone + desktop views)  ──►  /api/
backend/
  members/      accounts, mobile wallets, notifications
  savings/      groups, memberships, contributions, dues
  metals/       prices, FX, custodian ledger, scheduled tasks
  payouts/      payout processing
  loans/        loans and repayments
  integrations/ mobile money and SMS adapters
demo/       scripted agents for the live defense demo

All metal balances come from one ledger (CustodianTransaction), so grams × price = kwacha reconciles everywhere.

*Simulated Components*

These are clearly marked as simulations and can be swapped for real providers without changing the rest of the system:

ZGCL custodian (backend/metals/custodian.py): no public Zambia Gold Company Limited API exists, so this module behaves like one: it buys and sells at the stored price, charges a fee and issues a reference for each deal.
Mobile money (backend/integrations/mobile_money.py): confirms payments immediately. A real MTN MoMo or Airtel Money provider can be added as a class with the same collect / disburse methods.
SMS: with no Africa's Talking key set, messages are written to the log instead of sent.
Prices: METAL_PRICE_PROVIDER=simulated works offline; set it to GoldAPI with a key for real prices.
Running locally (Windows)

*Requirements*
Python 3.12+
Node.js 20.19+ (or 22.12+)
PostgreSQL 17

*1. Database*

Create an empty database named treadstone in PostgreSQL.

*2. Backend*
powershell
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env

Open backend\.env and set at least DJANGO_SECRET_KEY and DB_PASSWORD. Then:

powershell
python manage.py migrate
python manage.py setup_schedules
python manage.py createsuperuser

*3. Frontend*
powershell
cd frontend
npm install

*4. Start everything*

Double-click start.bat in the project root. It opens the API (port 8000), the background worker and the PWA (port 5173), then opens the app in your browser.

*Helper Scripts*
Script	What it does
start.bat	Starts the API, worker and PWA together
import-real-prices.bat	Imports real daily gold/silver prices from March 2024 (needs GOLDAPI_KEY)
reset-demo.bat	Rebuilds a five-member annuity group with backdated contributions at real historical prices
run-live-demo.bat	Runs five scripted members through the real app in browser windows (needs start.bat running)
allow-phone.bat	Opens port 5173 so a phone on the same Wi-Fi can use the app

*For the demo:* run import-real-prices.bat, then reset-demo.bat. The demo accounts use the password Demo@2026; their phone numbers are printed when the script finishes.

*Tests*
powershell
cd backend
venv\Scripts\python.exe manage.py test
Configuration

All settings are read from backend/.env. See backend/.env.example for the full list. Never commit .env.

*Licence*

*MIT. See LICENSE.*
