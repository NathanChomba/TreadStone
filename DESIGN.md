# Treadstone — Design Specification

The visual and interaction rules for the Treadstone PWA (React + Tailwind CSS v4). This file is the source of truth for the frontend: when code and this file disagree, fix the code or update this file on purpose.

Reference canvas: "Treadstone UI Overhaul" (Claude Design artifact) — 10 screens, desktop and phone.

---

## 1. Design principles

1. **Show value preserved, not just value held.** The product's argument is that gold beats cash. Every money screen that shows a balance should, where the data exists, show the *same money held as kwacha* next to it (the "Preserved vs cash" figure). This is the one element that distinguishes Treadstone from a plain mobile-money savings app.
2. **Numbers must reconcile.** Grams × price = kwacha, everywhere, to the ngwee. Never show a value that can't be derived from the ledger (e.g. negative holdings, totals that don't sum).
3. **Phone first, low-end Android, 3G.** Design at 390 px wide first. Desktop adds columns, never features.
4. **Gold is the accent, not the decoration.** Gold marks primary actions, the user's gold, and "preserved" gains. If everything is gold, nothing is.
5. **Plain language.** "Pay for group", "Paid out 12 Oct", "Gold bought on the 10th". No fintech jargon, no exchange-platform copy.

---

## 2. Colour

White and gold, on a warm off-white page. All text pairs below meet WCAG 2.1 AA (≥ 4.5:1 for normal text).

### 2.1 Surfaces

| Token | Hex | Use |
|---|---|---|
| `page` | `#FAF8F2` | App background |
| `card` | `#FFFFFF` | Cards, sidebar, bottom nav, inputs on page |
| `tile` | `#F7F4EC` | Stat tiles inside cards |
| `inset` | `#F4F1E8` | Inset controls (segmented toggle track) |
| `track` | `#EFEBE1` | Progress-bar track, neutral chips, row dividers |
| `border` | `#E7E2D5` | Card borders |
| `control-border` | `#D9D3C3` | Secondary-button and input borders, switch "off" |
| `disabled` | `#B5AE9A` | Off radio rings, "cash" bar, dashed comparison line |

### 2.2 Text

| Token | Hex | On white | Use |
|---|---|---|---|
| `text` | `#1C1A14` | 17.4:1 | Headings, body, figures |
| `text-2` | `#5E5848` | 7.1:1 | Secondary lines, inactive nav |
| `text-3` | `#6E6857` | 5.6:1 (5.2 on page) | Labels, captions, timestamps |

### 2.3 Gold

| Token | Hex | Use | Rule |
|---|---|---|---|
| `gold` | `#D4A537` | Primary button fill, logo, chart lines, progress fill, gold dot | **Never as text** — only 2.3:1 on white |
| `on-gold` | `#14130D` | Text on `gold` fills | 8.2:1 |
| `gold-text` | `#8A6410` | Links, active nav item, avatar initials | 5.4:1 on white |
| `gold-text-hover` | `#5E430A` | Link hover/pressed | |
| `gold-strong` | `#805A0A` | Gain figures and chip text on gold tints | 5.6:1 on `gold-tint` |
| `gold-muted` | `#7A5C12` | Captions inside gold-tint cards | 5.7:1 on `gold-tint` |
| `gold-tint` | `#FBF4E2` | "Preserved vs cash" cards, selected chips | |
| `gold-tint-border` | `#E8D6A6` | Border of gold-tint cards, current-month bar | |
| `gold-chip` | `#F6EDD3` | Gold chip/badge bg, active nav bg, avatar bg | |

### 2.4 Status

| Token | Fg | Bg | Use |
|---|---|---|---|
| `positive` | `#1E7A47` | `#E3F4EA` | Paid, Active, inflows, price up (4.7:1 on bg) |
| `negative` | `#B4570F` | — | Price down, Sign out (4.9:1 on white) |
| `info` | `#2F5AA8` | `#E6EEFB` | Loan transactions (5.7:1) |
| `silver` | `#9AA1AB` | — | Silver dot only |

Colour never carries meaning alone: price changes always include ▲/▼ and a sign; statuses always include a word ("Paid", "Due 10 Nov", "Cycle closed").

---

## 3. Typography

Google Fonts: `Sora` (500, 600, 700), `Manrope` (400–700), `JetBrains Mono` (500, 600).

| Role | Font | Size / weight | Notes |
|---|---|---|---|
| Hero figure (desktop) | JetBrains Mono | `clamp(40px, 5vw, 60px)` / 600 | letter-spacing −0.03em, line-height 1 |
| Hero figure (phone) | JetBrains Mono | 34–40 / 600 | |
| Page title (desktop) | Sora | 30–34 / 600 | letter-spacing −0.02em |
| Page title (phone) | Sora | 20–22 / 600 | |
| Section title | Sora | 17 (phone) – 20 (desktop) / 600 | |
| Eyebrow label | Manrope | 12–14 / 600, UPPERCASE | letter-spacing 0.08em, colour `text-3` |
| Body | Manrope | 15 / 500–600 | |
| Secondary | Manrope | 13–14 / 400–500 | |
| Micro (chips, nav) | Manrope | 11–12 / 600–700 | Minimum size anywhere: 11 px |
| Stat figures | JetBrains Mono | 16–26 / 600 | |
| References, IDs | JetBrains Mono | 13 / 500 | e.g. `TS-2610-10-4410` |

**Every number that is money, weight, a price or a reference is set in JetBrains Mono** so columns align and digits are unambiguous.

---

## 4. Number and date formatting

| Kind | Format | Example |
|---|---|---|
| Kwacha | `K` + thousands comma + 2 dp | `K1,981.84` |
| Signed kwacha | sign then K | `+K131.84`, `−K1,000.00` (true minus `−`, U+2212) |
| Gold / silver | 4 dp + ` g` | `0.8866 g` |
| Price | `K… / g` | `K2,235.32 / g` |
| Percent | 1–2 dp with sign/arrow | `▲ 1.20%`, `+7.1%` |
| Date (in-list) | `d Mon` | `10 Oct` |
| Date (full) | `Weekday, d Month` or `d Mon yyyy` | `Tuesday, 10 Nov`, `10 Aug 2027` |
| Time | 24-hour | `13:32` |

Backend rule (mirrors CLAUDE.md): money is `Decimal`, never float; grams stored to 4 dp; rounding happens once, at display.

---

## 5. Spacing, radius, elevation

**Spacing scale (px):** 4 · 6 · 8 · 10 · 12 · 14 · 16 · 18 · 20 · 24 · 28 · 32 · 44 · 48.
- Phone screen gutter: **16**. Desktop main padding: `32px clamp(16px, 3vw, 44px)`.
- Gap between cards: **18** (phone), **24** (desktop). Inside a card: **12–16**.

**Radius:**

| Element | Radius |
|---|---|
| Segmented-toggle segment | 8 |
| Nav item, small button | 10 |
| Buttons, inputs, icon buttons | 12–14 |
| Stat tiles | 14 |
| Phone cards, list cards | 16–18 |
| Main cards | 20 |
| Chips, badges, progress bars, avatars | 999 (pill) |

**Elevation:** none. Separation comes from `card` on `page` plus a 1 px `border`. No drop shadows, no gradients except the gold area-fill under price charts (gold at 30% → 0%).

---

## 6. Layout

### Phone (default, 390 px design width)
- Single column, 16 px gutters, content scrolls above a fixed **5-tab bottom nav**: Home · Groups · Vault · Ledger · Me.
- Nav item: icon 22 px + 11 px label, min-height 56, active = `gold-text` 700 + `aria-current="page"`.
- Flows (Contribute, Loans) hide the tab bar and show a back button (44×44) top-left.

### Desktop (≥ 1024 px)
- `flex-wrap` row: sidebar `flex: 1 1 230px` + main `flex: 999 1 560px; min-width: 0`. On narrow screens the sidebar stacks on top — never sticky, never `100vh`.
- Sidebar: logo, 6 nav links, custodian card pinned to the bottom ("Zambia Gold Company Ltd — Simulated for this prototype").
- Main dashboard: vault card `flex: 2 1 520px` beside a rates/up-next column `flex: 1 1 300px`; tables below.
- Wide tables sit in an `overflow-x: auto` box with a `min-width` (720–900 px).

### Breakpoints (Tailwind defaults)
`sm 640` · `md 768` · `lg 1024` (sidebar appears) · `xl 1280`.

---

## 7. Components

### Buttons
| Variant | Style | Use |
|---|---|---|
| Primary | `gold` fill, `on-gold` text, 700, h 48 (desktop) / 56 (phone CTA), r 12–14 | One per screen: Contribute, Pay, Send request |
| Secondary | transparent, 1 px `control-border`, `text`, 600 | Withdraw, Details, Invite |
| Soft | `gold-chip` bg, `gold-strong` text | In-row actions (table "Contribute") |
| Icon | 44×44, `card` bg, 1 px `border`, r 12 | Back, notifications, export — always `aria-label` |
| Destructive text | no bg, `negative` text | Sign out |

Minimum touch target **44×44** for everything tappable.

### Segmented toggle (Kwacha / Grams, chart ranges)
Track `inset` + 1 px border, r 11, padding 3. Segment h 44, r 8; selected = `gold` fill + `on-gold`, unselected = transparent + `text-2`. Uses `aria-pressed`.

### Chips / badges
h 26, padding 0 10, pill, 12/700. Variants: positive (Active, Paid), gold (Due, Gold-backed, Contribution), neutral `track` (Cycle closed), info (Loan).

### Selectable chips (amount, term, language, filters)
h 44–52, r 12 (pill for filters). Selected = 2 px `gold` border + `gold-tint` bg + `gold-strong` text (or solid gold fill for filters). Radio-type groups use `role="radio"` + `aria-checked`.

### Switch
52×32 pill, knob 24 white; on = `gold`, off = `control-border`. `role="switch"`, `aria-checked`, labelled by its row title.

### Cards
- **Standard:** `card`, 1 px `border`, r 20, padding 20–28.
- **Preserved card:** `gold-tint`, 1 px `gold-tint-border`; label `gold-muted`, figure `gold-strong` mono. Reserved for value-vs-cash comparisons.
- **Stat tile:** `tile`, r 14, padding 14–16, label 12–13 `text-3` above a mono figure.

### Progress
- **Bar:** h 6–8, `track` background, `gold` fill.
- **Cycle bar:** 12 segments (one per month): paid = `gold`, current = `gold-tint-border` + 2 px gold outline, future = `track`. Month labels under each on desktop.

### Charts
- Price/vault line: 2.5 px `gold` stroke, non-scaling, area fill gold 30% → 0%.
- "Same money as cash" reference: 1.5 px dashed `disabled` line, with a legend entry.
- Sparklines: 2 px, `positive` when up, `negative` when down. Decorative SVGs get `aria-hidden="true"`; the figure next to them carries the meaning.

### Lists and tables
- Row padding 14–16 vertical, divider `track`. Figures right-aligned in mono.
- Member row: 36 px avatar (initials, `gold-chip` for the user, `track` for others) · name/sub · status chip.
- Transaction card (phone): badge + amount on line 1; group, date · provider and grams · price on line 2.

### Forms
- Input h 52–56, r 12, 1 px `control-border`, mono 17–22 for money/phone numbers, a visible `<label>` above each.
- Helper text 13 `text-3` beneath. Mobile-money numbers display as `097 123 4567`.

### Icons
Inline stroke SVG, 24 viewBox, 1.8–2 px stroke, round caps/joins, `currentColor`. Sizes 18 / 20 / 22. No emoji, no icon fonts.

---

## 8. Screens

| Screen | Artboard | Key content |
|---|---|---|
| Dashboard — desktop | `Main.dc.html` | Vault value + ZMW/g toggle, cash-vs-gold chart, 3 stat tiles, metal rates, up next, groups table, recent activity |
| Dashboard — phone | `Mobile.dc.html` | Vault card, 4 quick actions, rates, due card, group cards, tab bar |
| Group — desktop | `GroupDetail.dc.html` | Pool stats, 12-month cycle, November payments table, rules, ZGCL custody ref |
| Group — phone | `MobileGroup.dc.html` | Same content stacked; Contribute CTA |
| Contribute flow | `Contribute.dc.html` | 4 steps: amount → provider + number → review (gold estimate) → received |
| Loans | `Loans.dc.html` | Limit (50% of share), amount + term, interest & schedule, history |
| Ledger — desktop | `Ledger.dc.html` | Totals, filterable table: date, type, group, via, amount, grams, price/g, ref |
| Ledger — phone | `MobileLedger.dc.html` | Totals, filter chips, transaction cards |
| Vault & metals | `MobileVault.dc.html` | Holdings, gold chart with 1W/1M/6M/1Y, silver, "your K1,850 if you had…" bars, custody |
| Profile & settings | `MobileMe.dc.html` | Profile + KYC, mobile-money numbers, security/alert switches, language (English/Bemba/Nyanja), sign out |

Designed later on a separate canvas ("Treadstone Onboarding & Admin", https://claude.ai/artifact/LmmFcaBTfv2PE37XrW4cYZ): sign-up, KYC, create/join group, group-admin view. The Django admin restyle was designed by the user ("Site administration", member list, change loan).

---

## 9. Behaviour rules

- **Gold purchase timing:** contributions are pooled and the group's gold is bought **once, on the due date (the 10th)**. Until then the UI shows the payment as received and the grams as an *estimate* ("≈ 0.4474 g … bought on 10 Nov at that day's price"). Implemented as a scheduled Django-Q2 task.
- **Offline (PWA):** cached GET data (balances, history, last price) may be shown offline with a "Prices at hh:mm" stamp. Contribute, Withdraw, Loan request and Payout buttons are disabled offline with the reason shown. Payments are never queued.
- **Price freshness:** every price display shows its timestamp. Stale > 15 min → show the time in `negative`.
- **Payment confirmation:** the final CTA repeats the amount ("Pay K1,000.00"). Success screen shows a reference `TS-yymm-dd-nnnn`.
- **Custodian honesty:** while ZGCL is simulated, the sidebar card and the custody sections say so.

---

## 10. Accessibility checklist

- Real `<button>`, `<a href>`, `<input>` + `<label>`; no clickable `div`s.
- `aria-label` on every icon-only button; `aria-current="page"` on the active nav item; `aria-pressed` / `aria-checked` on toggles, chips and switches.
- Text contrast ≥ 4.5:1 (see §2). Gold `#D4A537` is a fill/line colour only.
- Touch targets ≥ 44×44. Body text ≥ 15 px, nothing below 11 px.
- `lang="en"` on `<html>`; switch it when the user picks Bemba or Nyanja.

---

## 11. Tailwind v4 tokens

Implemented in `frontend/src/index.css` (`@theme` block), with a few additions (`gold-hover`, `negative-bg`). Usage examples: `bg-page text-ink font-sans`, `bg-gold text-on-gold rounded-control h-12`, `num` (mono + tabular figures), `bg-gold-tint border border-gold-tint-line rounded-card`. Fonts load from Google Fonts in `frontend/index.html`. PWA manifest colours are `#FAF8F2`.
