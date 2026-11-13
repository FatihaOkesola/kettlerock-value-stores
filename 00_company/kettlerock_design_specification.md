# Kettlerock Value Stores: Design Specification

**Author:** Fatiha Abisola Okesola · **Version:** 2.8 · **Last updated:** 2026-11-12

> A fictional Canadian value retailer, generated from synthetic data calibrated to public retail benchmarks and the M5 dataset, for one FY2028 planning season told in seven chapters across FP&A and strategic finance.

## Contents

- [1. Project framing](#1-project-framing)
- [2. Glossary (permanent definitions)](#2-glossary-permanent-definitions)
- [3. Company profile](#3-company-profile)
- [4. Unit economics](#4-unit-economics)
- [5. Store network, timeline and markets](#5-store-network-timeline-and-markets)
- [6. Merchandise, pricing and sourcing](#6-merchandise-pricing-and-sourcing)
- [7. Fiscal calendar](#7-fiscal-calendar)
- [8. Accounting policy (management reporting basis)](#8-accounting-policy-management-reporting-basis)
- [9. Planning and version model](#9-planning-and-version-model)
- [10. Forecast methods and information firewall](#10-forecast-methods-and-information-firewall)
- [11. Macro inputs](#11-macro-inputs)
- [12. Basket model and price response](#12-basket-model-and-price-response)
- [13. Working capital, cash and debt](#13-working-capital-cash-and-debt)
- [14. Hidden events](#14-hidden-events)
- [15. Assumptions registry and world parameters](#15-assumptions-registry-and-world-parameters)
- [16. Lineage and data dictionary](#16-lineage-and-data-dictionary)
- [17. Schema: core (first release)](#17-schema-core-first-release)
- [18. Schema: extension modules](#18-schema-extension-modules)
- [19. Generation order](#19-generation-order)
- [20. Reconciliation checks](#20-reconciliation-checks)
- [21. Stage 1 calibration plan](#21-stage-1-calibration-plan)
- [22. Storyline: the FY2028 planning season](#22-storyline-the-fy2028-planning-season)
- [23. Repository structure](#23-repository-structure)

## 1. Project framing

Kettlerock is a controlled strategic finance simulation; every finding describes the simulated company, never a real retailer.

**Official description:** Kettlerock Value Stores is a controlled strategic finance simulation of a fictional Canadian value retailer, calibrated to public retail benchmarks. All company data is synthetic. Findings describe the simulated company, not any real retailer.

**Control statement:** The analyst does not control the realized outcome, but the model designer controls the data-generating process.

**What it demonstrates:** driver-based planning, variance analysis, forecasting and reforecasting, capital allocation, liquidity and covenant management, and scenario judgment on internally consistent data.

**What it does not claim:** any insight into the internal economics of a real company. Public sources only set descriptive patterns and plausible ranges.

**Disclosure in the README:** all data is synthetic; behavioural patterns are informed by the M5 retail dataset (credited per its terms); company-level ranges are benchmarked against public filings of discount retailers; macro history uses real public data.

## 2. Glossary (permanent definitions)

These definitions are fixed; every table, analysis and write-up uses them.

| Term | Definition |
| --- | --- |
| Traffic | Completed customer sales transactions. Kettlerock does not measure store visitors or footfall. |
| Transaction | One completed sales basket at the till. Return-only visits are not transactions. |
| Items | Units sold in sales transactions, before returns. |
| Returns | Units and value returned by customers, recorded separately from transactions. |
| Net units | Items minus units returned. |
| Items per basket | Items ÷ transactions, derived from integer counts. |
| Average ticket | Net sales ÷ transactions. |
| Net sales | Gross sales − promotional discounts − markdowns − returns, excluding sales taxes. |
| Comparable store | A store open at least 13 full fiscal months; excluded for any period it was closed more than two weeks for a remodel. |
| Comparable sales growth | Net sales growth of comparable stores against the same fiscal period last year. |
| Cohort | The fiscal year a store opened. |
| Market | A trade area of 1–3 stores (`market_id`), used for local events such as competitor openings. |
| Store contribution | Gross margin − store labour − occupancy − other store costs (four-wall EBITDA). |
| Covenant EBITDA | Adjusted EBITDA after lease payments, no lease add-back (section 8). |
| Net debt | Term loan + revolver − cash; excludes lease liabilities. |
| As-of date | The date a plan version was built; it may use no information from after this date. |

## 3. Company profile

Kettlerock Value Stores Inc. is a privately owned, private-equity-backed Canadian value retailer with 40 stores and one distribution centre at the end of Q3 FY2027.

- **Business:** everyday consumables, general merchandise and seasonal goods at fixed price points, in neighbourhood plaza stores. The pitch is a quick trip for basics and seasonal items at predictable prices.
- **Industry:** Canadian discount and dollar-store retail. Real competitors in the space include Dollarama, Dollar Tree, Giant Tiger and Walmart in some categories. Kettlerock is a small regional player competing on convenience and seasonal assortment.
- **History:** founded in Ontario in 2009 with 3 stores; 22 stores by 2021, funded from its own cash. In 2022 a fictional mid-market private equity firm bought a majority stake, bringing a professional finance team, a term loan and a formal budget process.
- **Footprint:** 26 stores in Ontario (Greater Toronto Area and Southwestern Ontario), 9 in Quebec (Montreal area), 5 in Atlantic Canada (Nova Scotia, New Brunswick). One leased distribution centre in the Greater Toronto Area.
- **Ownership and goals:** the private equity firm holds a majority stake and the founding family retains a minority. The firm targets 60 stores by FY2030 and a higher EBITDA margin ahead of an exit in FY2029–FY2030; the exit route is not decided.
- **Built-in tensions:** growth versus covenant headroom; protecting price points versus protecting margin; seasonal inventory risk versus seasonal sales.
- **Analyst role:** Analyst, Strategic Finance & Planning, reporting to the Director of Strategic Finance, who reports to the CFO. Works alongside FP&A and partners with merchandising, real estate, supply chain and store operations. Each chapter of the planning season (section 22) is led by a different part of the finance team, and the analyst works in that role's voice.
- **Now:** November 2026. Q3 FY2027 has closed. The team is preparing the Q3 reforecast, reviewing the expansion plan and starting the FY2028 budget.

The profile states the plan, not this year's results. Results come from the generator so they can be discovered in analysis.

## 4. Unit economics

A mature standard store sells about $2.95M a year at about a 19% store contribution; the company runs at about a 10% adjusted EBITDA margin on about $112M of FY2027 budget sales. Values were accepted on 2026-11-07. Origin tags: B = calibrated benchmark, A = authored assumption, O = observed public data, D = derived.

### Store

| Item | Value | Origin |
| --- | --- | --- |
| Selling area | Standard 9,000 sq ft; compact (Atlantic) 6,000 sq ft | A |
| Mature store net sales | Standard ≈ $2.95M/yr; compact ≈ 75% of standard | A, checked against B |
| Ramp-up (share of mature sales) | Year 1: 70%; Year 2: 85%; Year 3: 95%; Year 4+: 100% | A |
| Average ticket | ≈ $11.50 | A, checked against B |
| Items per basket | ≈ 4.3 (average unit price ≈ $2.67) | D |
| Transactions per day (mature standard store) | ≈ 705 ($2.95M ÷ 364 days ÷ $11.50) | D |
| Gross margin | ≈ 41% of net sales | B (range) |
| Store labour | ≈ 10.5% of sales (≈ 280 hours/week at maturity: fixed coverage of 2 staff × 70 open hours, plus ≈ 0.028 hours per transaction, at a loaded wage) | A; wage paths O |
| Occupancy (rent, shared mall costs, property tax) | ≈ 8.5% of sales on average; rent per sq ft varies by market and is highest in the GTA | A |
| Other store costs (utilities, repairs, supplies, card fees) | ≈ 3% of sales | A |
| Store contribution (four-wall EBITDA) | ≈ 19% of sales at maturity (41 − 10.5 − 8.5 − 3); lower while stores ramp | D |
| New store capex | ≈ $650K: leasehold improvements $350K, fixtures $230K, IT/POS $70K | A |
| Opening inventory | ≈ $180K (working capital, not capex) | A |
| Pre-opening costs | ≈ $40K, expensed | A |
| Payback hurdle | ≤ 3 years on store contribution | A |
| Remodel | ≈ $250K, about 3 per year; sales lift is an authored range | A |

### Company

| Item | Value | Origin |
| --- | --- | --- |
| FY2027 budget net sales | ≈ $112M | D |
| Distribution centre (DC rent, DC labour, outbound freight) | ≈ 2.5% of sales | A |
| Marketing | ≈ 1.5% of sales | A |
| Head office G&A (including owner's monitoring fee) | ≈ 5% of sales | A |
| Adjusted EBITDA (covenant basis) | ≈ 10% of sales (≈ $11M) | D |
| Maintenance capex | ≈ $0.6M/yr (≈ $15K per store; with remodels, ≈ $34K per store) | A |
| Depreciation | Store assets over lease term (≈ 10 years); IT over 3–5 years | A |
| Tax | Authored blended effective tax rate for management planning, ≈ 26.5% | A |

### Capital structure

| Item | Value | Origin |
| --- | --- | --- |
| Term loan | $40M at 2022 close; 5% annual amortization; ≈ $32M today | A |
| Revolving credit facility | $15M limit; drawn seasonally for the holiday inventory build | A |
| Interest | Floating: base rate + 3.75% spread; historical base rate path is real | A, O |
| Leverage covenant | Net debt ÷ covenant EBITDA (last 12 months) ≤ 3.50x | A |
| Internal headroom policy | At least 0.50x below the covenant | A |
| Minimum liquidity | Cash + undrawn revolver ≥ $5M; minimum operating cash $2M | A |
| Current leverage | ≈ 3.0x | D |

**Design check:** the numbers are set so that reaching 60 stores is possible but tight: after interest, tax, loan amortization and maintenance capex, free cash flow covers new-store capex only if EBITDA grows. Whether it does is the analysis, not the design.

## 5. Store network, timeline and markets

Kettlerock grows from 30 stores at the start of FY2025 to 40 at the end of Q3 FY2027, with 2 Ontario openings still planned for Q4.

| Fiscal year | Opening stores | Openings | Closing stores |
| --- | --- | --- | --- |
| FY2027 to end of Q3 (actual) | 37 | 3 (Atlantic) | 40 |
| FY2027 (budget) | 37 | 5 planned (3 Atlantic, 2 Ontario) | 42 planned |
| FY2026 | 34 | 3 (1 Ontario, 1 Quebec, 1 Atlantic) | 37 |
| FY2025 | 30 | 4 (2 Ontario, 1 Quebec, 1 Atlantic) | 34 |

At the start of FY2025 the 30 stores were 23 in Ontario, 7 in Quebec and none in Atlantic Canada. The two planned Q4 FY2027 openings would bring Ontario to 28 and the company to 42.

The long-range plan targets 60 stores by FY2030.

**Store attributes** (`dim_store`): province, region, location type (urban, suburban, small town), format (standard, compact), selling square feet, open date, remodel dates, lease start and end, rent per sq ft, cohort, `market_id`.

**Markets:** each store belongs to one trade area (`market_id`) of 1–3 stores. Markets are the unit for local events: a competitor opening affects every store in the chosen market (section 14). Market assignment is authored once and fixed.

The 40 stores form 21 markets: dense urban areas hold 2–3 stores per market, small towns are a market of one.

| Region | Stores | Markets | Stores per market |
| --- | --- | --- | --- |
| Greater Toronto Area | 14 | 5 | 3, 3, 3, 3, 2 |
| Southwestern Ontario | 12 | 8 | 2, 2, 2, 2, 1, 1, 1, 1 |
| Montreal area | 9 | 4 | 3, 2, 2, 2 |
| Atlantic Canada | 5 | 4 | Halifax 2; three single-store towns |
| Total | 40 | 21 |  |

The two Ontario stores planned for Q4 FY2027 join existing GTA markets. Sales transfer between stores in the same market (cannibalization) is not modelled in the first release.

**Comparable rule:** a store enters the comparable base after 13 full fiscal months; periods with a remodel closure over two weeks are excluded.

## 6. Merchandise, pricing and sourcing

About 180 items sit on eight fixed price points across three categories; prices change only by moving an item to another price point.

**Price points:** $1.25, $1.50, $2.00, $2.50, $3.00, $4.00, $5.00, $6.00.

| Category | Departments | Share of sales (approx.) | Product margin before shrink and markdowns (approx.) |
| --- | --- | --- | --- |
| Consumables | Snacks and confectionery; cleaning and paper; personal care | 45% | 37% |
| General merchandise | Kitchen and home; party and stationery; toys and crafts | 40% | 49% |
| Seasonal | Halloween; Christmas; Easter/spring; summer; back-to-school | 15% | 52% |

The weighted product margin is about 44%. Shrink (about 1.5% of net sales) and markdowns (about 1.5%) bring gross margin to about 41% (section 4).

**Seasonal windows:** seasonal items sell only inside their window. Unsold seasonal stock at the end of a window is marked down or written off.

**Sourcing:** about half of cost of goods is imported, bought in US dollars and received through the distribution centre; the rest is domestic and bought in Canadian dollars. Imports convert at the real historical CAD/USD rate during the actual period. Tariffs and FX hedging are extensions.

## 7. Fiscal calendar

The fiscal year ends on the Saturday closest to January 31, with 4-5-4 week quarters; FY2027 Q3 closed on October 31, 2026.

| Fiscal year | Starts | Ends | Weeks |
| --- | --- | --- | --- |
| FY2029 | Sun Jan 30, 2028 | Sat Feb 3, 2029 | 53 |
| FY2028 | Sun Jan 31, 2027 | Sat Jan 29, 2028 | 52 |
| FY2027 | Sun Feb 1, 2026 | Sat Jan 30, 2027 | 52 |
| FY2026 | Sun Feb 2, 2025 | Sat Jan 31, 2026 | 52 |
| FY2025 | Sun Feb 4, 2024 | Sat Feb 1, 2025 | 52 |

- Weeks run Sunday to Saturday. Each quarter is 13 weeks: fiscal months of 4, 5 and 4 weeks.
- FY2027 quarter ends: Q1 May 2, 2026; Q2 August 1, 2026; Q3 October 31, 2026.
- Years are named by the calendar year they end in.
- FY2029 is a 53-week year inside the long-range plan horizon; growth targets for it must adjust for the extra week.
- Holidays and store closures are province-specific (`dim_holiday`), as set out below.

**Store closures.** Stores close on the retail closing days set by provincial law. Ontario stores close on all nine days in the Retail Business Holidays Act, including stores in the City of Toronto, where the Act does not apply: closing them is company policy. New Brunswick stores open on Sundays under local exemptions to the Days of Rest Act (authored).

| Day | Ontario | Quebec | Nova Scotia | New Brunswick |
| --- | --- | --- | --- | --- |
| New Year's Day | Closed | Closed | Closed | Closed |
| Family Day / Heritage Day (third Monday of February) | Closed | Open | Closed | Closed |
| Good Friday | Closed | Open | Closed | Closed |
| Easter Sunday | Closed | Closed | Closed | Open |
| Victoria Day | Closed | Open | Open | Closed |
| Saint-Jean-Baptiste Day (June 24) | Open | Closed | Open | Open |
| Canada Day | Closed | Closed | Closed | Closed |
| New Brunswick Day (first Monday of August) | Open | Open | Open | Closed |
| Labour Day | Closed | Closed | Closed | Closed |
| Thanksgiving Day | Closed | Open | Closed | Closed |
| Remembrance Day | Open | Open | Closed | Closed |
| Christmas Eve | Reduced hours | Reduced hours | Reduced hours | Reduced hours |
| Christmas Day | Closed | Closed | Closed | Closed |
| Boxing Day | Open | Reduced hours (opens 1 p.m.) | Closed | Closed |
| New Year's Eve | Reduced hours | Reduced hours | Reduced hours | Reduced hours |

- **Closed:** no transactions.
- **Reduced hours:** traffic is an authored share of a normal day. Christmas Eve and New Year's Eve close at 5 p.m. (required in Quebec, company policy elsewhere).
- **Recaptured demand:** an authored share (40–70%) of a closed day's expected sales moves to the neighbouring open days.
- **Legal basis:** Ontario, Retail Business Holidays Act; Quebec, Act respecting hours and days of admission to commercial establishments and its regulation; Nova Scotia, Retail Business Designated Day Closing Act and Remembrance Day Act; New Brunswick, Days of Rest Act. Each has a row in `benchmark_sources.csv`.

## 8. Accounting policy (management reporting basis)

Kettlerock reports on an internal management basis in CAD, with lease payments as operating expenses and covenant EBITDA calculated after rent.

**Lease convention:** Kettlerock uses an internal management-reporting convention in which lease payments are shown as operating expenses. Statutory IFRS/ASPE accounting and lease-accounting differences are outside scope.

**Revenue:** gross sales at ticket price − promotional discounts − markdowns − returns = net sales. Sales taxes (HST, GST, QST) are excluded.

**Cost of goods (COGS):** landed cost of units sold + shrink + inventory write-downs − supplier rebates and allowances. Landed cost = supplier cost (imports at the exchange rate on the shipment date) + inbound freight + duty and tariffs; inventory is carried at landed cost. Supplier rebates reduce COGS when earned and are not deducted from inventory.

| Margin level | Definition |
| --- | --- |
| Gross margin | Net sales − COGS |
| Store contribution (four-wall EBITDA) | Gross margin − store labour − occupancy − other store costs |
| Adjusted EBITDA | Store contribution − distribution − marketing − head office; excludes pre-opening costs and one-off items, shown separately |
| Operating income | Adjusted EBITDA − pre-opening and one-offs − depreciation |
| Net income | Operating income − interest ± FX transaction gains and losses − tax |

**Covenant definitions:**

- Covenant EBITDA = adjusted EBITDA on this basis: after lease payments, with no lease add-back. Measured over the last 12 months.
- Net debt = term loan + revolver − cash. No lease liabilities.
- Leverage = net debt ÷ covenant EBITDA; tested at each fiscal quarter end against 3.50x.

**Other policy choices:**

- Distribution costs sit below gross margin, not in COGS.
- Tax uses an authored blended effective tax rate for management planning; provincial allocation and tax rules are not modelled.
- Pre-opening costs are expensed as incurred and excluded from adjusted EBITDA.

**Foreign exchange:** Kettlerock has no foreign subsidiaries, so there is no translation adjustment. Imports are recorded at the exchange rate on the shipment date, and that rate is built into landed cost, so the real currency effect on product cost flows into gross margin. Any difference between the shipment-date rate and the rate when the balance is paid is an FX transaction gain or loss, reported below operating income and excluded from adjusted EBITDA.

## 9. Planning and version model

Seven planning versions sit beside the actuals; the generator builds five, and the analyst builds the Q3 FY2027 forecast and the FY2028 plan.

| Version | Type | Case | As-of date | Actuals through | Built by | Status |
| --- | --- | --- | --- | --- | --- | --- |
| ACT | Actual | — | Rolling | Q3 FY2027 | Generator | — |
| LRP\_2025 | Long-range plan FY2026–FY2030 | Base | Mar 2025 | FY2025 | Generator (board plan to 60 stores) | Approved |
| BUD\_FY2026 | Budget | Base | Jan 2025 | Q3 FY2025 + estimate | Generator | Final |
| BUD\_FY2027 | Budget | Base | Jan 2026 | Q3 FY2026 + estimate | Generator | Approved |
| FCST\_FY2027\_Q1 | Forecast (3 + 9) | Base | May 2026 | Q1 FY2027 | Generator (as FP&A) | Superseded |
| FCST\_FY2027\_Q2 | Forecast (6 + 6) | Base | Aug 2026 | Q2 FY2027 | Generator (as FP&A) | Current |
| FCST\_FY2027\_Q3 | Forecast (9 + 3) | Base | Nov 2026 | Q3 FY2027 | Analyst | Deliverable |
| PLAN\_FY2028 | Plan | Base, Upside, Downside | Nov 2026 (draft started after the Q3 close) | Q3 FY2027, plus the Q3 forecast for Q4 | Analyst | Deliverable |

**Version fields** (`dim_scenario`): `scenario_id`, `scenario_type`, `case`, `planning_cycle`, `as_of_date`, `actuals_through`, `version_status`, `assumption_set_id`, `prepared_by`.

Each version links to one assumption set in the registry (section 15), so every planned number traces to the assumptions behind it.

## 10. Forecast methods and information firewall

Every plan version is built by a stated method from information available on its as-of date only; no artificial bias is added. Forecast error may reflect unavailable information, stochastic variation, model limitations, or inaccurate assumptions. The information firewall prevents future-data leakage.

| Version | Method |
| --- | --- |
| Long-range plan, budgets | Driver-based monthly forecast: traffic, ticket, category mix, margin rates, cost rates and the opening schedule, taken from the version's assumption set |
| Q1 and Q2 forecasts (generated as FP&A) | Actual results to date + driver-based forecast for remaining months. Comparable sales driver = blend of year-to-date trend and budget assumption under a fixed rule: weight on the year-to-date trend = months of actuals ÷ 12 (Q1 forecast 0.25, Q2 forecast 0.50). The rule is fixed before generation and recorded in the registry. Seasonality follows last year's actual monthly shape. Cost rates follow year-to-date run rates. Openings follow the schedule known on the as-of date |
| Q3 forecast and FY2028 plan (analyst) | Analyst's choice. A comparison of run-rate and driver-based methods is part of the analysis |

**Information firewall:**

1. A forecast builder receives only (a) actuals dated on or before its as-of date and (b) its own visible assumption set.
2. It never receives sealed world parameters, the events log, or future actuals.
3. Forward macro inputs come from the outlook available on the as-of date (section 11), not from later realized values.
4. **Firewall test:** after building each version, the generator perturbs all actuals after the as-of date and rebuilds. If the version changes, the build fails.
5. No optimism or pessimism bias parameter exists in the generated forecasts.

## 11. Macro inputs

Real historical macro data drives the actual period; every plan uses forward assumptions as they stood on its as-of date.

| Input | Actual period (Feb 2024 – Oct 2026) | Plan versions |
| --- | --- | --- |
| CAD/USD exchange rate | Real historical rates (Bank of Canada), tag O | Outlook as of each version's as-of date, tag A (informed by public forecasts then available) |
| Base interest rate | Real historical path, tag O | As above |
| Consumer price inflation | Real historical CPI (Statistics Canada), tag O | As above |
| Provincial minimum wages | Real published rates and announced increases, tag O | Announced increases known at the as-of date; beyond that, authored |

- FY2028 planning carries three macro paths (base, upside, downside), each recorded in the registry.
- Historical data is never presented as if it were known before it happened: the FY2027 budget uses the January 2026 outlook, not rates realized later.
- Every observed series has a row in the benchmark source register (section 21), referenced from the data dictionary by source\_id.

## 12. Basket model and price response

One daily basket-generation process per store produces transactions, items, category mix, prices, discounts and net sales together, so they reconcile by construction. It generates daily aggregate transactions and basket characteristics, not individual baskets.

**Basket model (per store, per day):**

1. Draw integer transactions (traffic) per store-day from the traffic model (section 19), including any qualifying category-wide price effect.
2. Compute each item's baseline expected units for the day: transactions × the item's baseline units per transaction (category seasonality, season windows, persistent item shares).
3. Apply each item's price-response multiplier: price-adjusted expected units per item.
4. Sum price-adjusted expected units by category and draw integer units per category around those sums. Items = the sum of integer category units.
5. Derive category mix and items per basket. Items per basket = items ÷ transactions, from integer counts, never multiplied out and rounded.
6. Price each category's units by its price point mix to get gross sales; apply discount, markdown and return rates to get net sales and returns (returned units are integers).
7. Each week, allocate integer category-week units across items in proportion to their price-adjusted expected units (a multinomial split), so item units follow the price response and sum to the category exactly.

**Price response rule:**

- **Sequence:** baseline demand by item → each item's price-response multiplier → resulting expected units aggregated to category totals → integer category units → category mix and items per basket derived. Only qualifying category-wide changes separately affect transactions, in the traffic step. Each effect is applied once, so nothing is double-counted.
- **Where it applies:** price changes happen only at item level, by moving an item to a different price point (`fact_price_change`).
- **Sensitivity:** each item's response is drawn from its category's authored range, then scaled by a store multiplier by location type.
- **Grain:** expected item demand is computed daily inside the generator; item results are stored weekly, and the daily store-category table carries the integer category outcome.
- **Transactions:** a category-wide price change above an authored threshold has a smaller authored effect on transactions.
- **Not modelled in the first release:** substitution between items. A lost sale on one item does not move to another. Substitution belongs to the pricing extension.
- **Ranges and values:** the authored ranges are recorded in `ref_assumptions`; the values actually drawn are sealed (section 15B). None come from M5. Price response is stress-tested in scenarios.

## 13. Working capital, cash and debt

The core models monthly inventory by category with a seasonal build and simple payables, so revolver borrowing peaks before the holiday season and covenant headroom is tightest where it would be in real life.

**Inventory (monthly, at landed cost, by category):**

- Valued at landed cost (supplier cost at the shipment-date exchange rate + inbound freight + duty and tariffs). Roll-forward: opening + receipts at landed cost − landed cost of units sold − shrink − write-downs = closing. Supplier rebates go to COGS, not inventory (section 8).
- Receipts follow a simplified purchasing rule: domestic goods arrive roughly in step with sales; imported and seasonal goods arrive ahead of their selling window by an authored lead time (holiday goods ≈ 8–12 weeks). Imported goods enter inventory at shipment and are shown as in-transit until they reach the distribution centre.
- New stores add opening inventory in the month before opening.

**Payables:** domestic suppliers are paid ≈ 30 days after delivery. Imports are paid 30% as a deposit when the order is placed and 70% at shipment; ownership transfers at shipment. Deposits are held as a current asset until shipment. All terms are authored and recorded in the registry.

**Cash flow (monthly):** adjusted EBITDA − pre-opening costs − cash one-off costs (none generated in the core release; the line is kept for later use) − change in net working capital (inventory including in-transit + supplier deposits − payables) − capex − interest − cash tax − term loan amortization = change in cash before revolver.

**Revolver rule:** draw to keep cash at the $2M minimum; repay when cash exceeds it. Liquidity = cash + undrawn revolver, tested against the $5M minimum.

**Covenant:** leverage recalculated each month for monitoring and tested at quarter ends (section 8).

The inventory and purchasing extension later replaces the simplified receipts rule with item-level replenishment and purchase orders, and must reconcile to these monthly balances.

## 14. Hidden events

The generator draws a few events per seed from an authored menu and records them in a sealed log, opened only after the analysis is finished.

| Event | Scope rule | Effect | Recovery |
| --- | --- | --- | --- |
| Competitor opening | Pick one `market_id` at random; affects every store in it | Transactions fall by an authored range | Recovers over 6–12 months |
| Local demand shock | One store or one market | Transactions up or down by an authored range | Authored duration |
| Seasonal sell-through miss | One seasonal window, all stores | Lower seasonal units; higher markdowns and write-downs | Ends with the window |
| Supplier cost increase | One department | Higher supplier cost from an effective date, written to fact\_cost\_history | Persistent |
| Freight cost spike | Imported goods (the exchange rate follows real history and is never an event) | Higher landed cost for a period | Authored duration |
| Store disruption | One store | Closed or reduced trading for days to weeks | Ends on reopening |

**Sealed log fields:** event ID, type, start date, end date, affected stores or categories, magnitude, recovery profile.

The event menu, ranges and timing rules are authored; the draw is random. Results are presented as a diagnostic exercise, not independent discovery.

## 15. Assumptions registry and world parameters

Two stores of numbers are kept apart: what management believed when planning (visible) and how the simulated world actually behaves (partly sealed); every variance comes from the gap between them.

**A. Planning assumptions (`ref_assumptions`, visible)** — one row per assumption:

| Field | Content |
| --- | --- |
| assumption\_id, name | Identifier and short name |
| value, unit | The number and its unit |
| scope | Company, province, market, store, category or item |
| effective\_from, effective\_to | Dates it applies |
| assumption\_set\_id | The plan version it belongs to |
| origin | Calibrated, authored, observed, or management plan |
| source | source\_id from the benchmark source register (section 21), or "authored" |
| rationale | One line on why |
| confidence | High, medium or low |
| used\_by | Model component that reads it |

**B. World parameters (`sealed_world_parameters`):**

- Visible structural parameters: ramp curve, price point list, cost structure, calendar, store attributes.
- Sealed until analysis ends: the random draws for each seed, the price response values actually used, and the events log.

## 16. Lineage and data dictionary

Every column in every table has a dictionary entry (`ref_data_dictionary`) with its name, definition, unit, grain and one origin tag.

| Tag | Meaning | Example |
| --- | --- | --- |
| R | Business rule | Closing inventory = opening + receipts − landed cost of units sold − shrink − write-downs |
| B | Calibrated benchmark | Gross margin range |
| O | Observed public data | CAD/USD rate, base interest rate, CPI, minimum wages |
| A | Authored assumption | Ramp curve, price response, remodel lift |
| S | Stochastic draw | Daily noise, store level factor |
| E | Hidden event | Competitor opening in one market |
| D | Derived calculation | Average ticket = net sales ÷ transactions |

Tagging is at column level in the dictionary, not on every row. Columns tagged B or O carry a source\_id that points to the benchmark source register (section 21).

## 17. Schema: core (first release)

The first release has 9 dimension tables, 13 fact tables and 4 reference or sealed tables, enough for chapters 0, 1, 2, 4 and 6 of the storyline; chapter 3 adds the seasonal buying extension and chapter 5 adds western cost inputs.

### Dimension tables

| Table | One row per | Key contents |
| --- | --- | --- |
| `dim_date` | Day | Fiscal year, quarter, 4-5-4 month, week, day of week, 53-week flag, season windows |
| `dim_holiday` | Holiday × province | Date, province, name, trading status (closed, reduced hours, open), legal basis |
| `dim_store` | Store | Province, region, location type, format, sq ft, open date, remodel dates, lease terms, rent per sq ft, cohort, `market_id` |
| `dim_market` | Market | `market_id`, region, stores in market |
| `dim_product` | Item (≈ 180) | Category, department, price point, base unit cost (changes in fact\_cost\_history), import flag and currency, seasonal window, launch and discontinue dates |
| `dim_scenario` | Version | Fields in section 9 |
| `dim_account` | Account | Chart of accounts with the section 8 hierarchy |
| `dim_capex_project` | Project | Type (new store, remodel, IT/DC), budget, planned and actual dates, linked store |
| `dim_debt_facility` | Facility | Term loan and revolver: limit, spread, amortization, covenant terms |

### Fact tables

| Table | One row per | Key contents |
| --- | --- | --- |
| `fact_traffic_day` | Store × day | Integer transactions, items, items per basket; return-only visits excluded |
| `fact_sales_category_day` | Store × category × day | Integer units sold and returned, gross sales, discounts, markdowns, returns value, net sales, COGS components, gross margin |
| `fact_sales_item_week` | Store × item × week | Integer units, net sales, average selling price, COGS; sums to category-week |
| `fact_price_change` | Item × effective date | Old and new price point, scope (all stores or listed stores) |
| `fact_cost_history` | Item × effective date | Supplier cost and currency, inbound freight rate, duty and tariff rate; landed unit cost derived at the shipment-date exchange rate |
| `fact_macro_month` | Month × series × version | CAD/USD, base rate, CPI, minimum wages; observed for actuals, outlook for plans |
| `fact_store_cost_month` | Store × month × account | Labour hours, wage rate, labour cost, occupancy, other store costs |
| `fact_company_cost_month` | Cost centre × month × account | Distribution, marketing, head office, pre-opening |
| `fact_inventory_month` | Category × month × version | Opening, receipts, landed cost of units sold, shrink, write-downs, closing, of which in-transit (at landed cost) |
| `fact_capex_month` | Project × month × version | Planned and actual spend |
| `fact_driver_plan` | Entity × month × driver × version | Transactions, ticket, comparable %, openings, margin rates, cost rates |
| `fact_pnl_month` | Entity × month × account × version | All P&L versions |
| `fact_cash_debt_month` | Month × version | Supplier deposits, payables, net working capital, FX transaction gains and losses, cash flow lines, cash, revolver, term loan, leverage, headroom, liquidity |

### Reference and sealed tables

| Table | Content |
| --- | --- |
| `ref_assumptions` | Planning assumptions (section 15A) |
| `ref_data_dictionary` | Column definitions and lineage tags (section 16) |
| `sealed_world_parameters` | Seeds, draws and price response values (section 15B) |
| `sealed_events_log` | Hidden events (section 14) |

## 18. Schema: extension modules

Eight extension modules are designed now and built when a role needs them; each replaces a simplified core line and must reconcile to it.

| Module | Tables | Replaces in the core | Used in |
| --- | --- | --- | --- |
| Inventory and purchasing | `fact_inventory_week` (location × item), `fact_purchase_order`, `fact_purchase_commitment`, `dim_supplier` | Simplified receipts rule in `fact_inventory_month` | Chapter 3 (deeper inventory analysis) |
| Detailed labour | `fact_labour_week` (store × role) | Store labour line | Chapter 2 |
| Promotions and marketing | `dim_promotion`, `fact_marketing_month` (region × channel) | Flat discount and marketing rates | Chapter 1 |
| Pricing with substitution | Substitution shares within department | No-substitution rule | Chapter 1 |
| Payments | `dim_tender`, `fact_tender_day` | Flat card-fee rate | Work beyond the storyline |
| FX hedging and tariff detail | `fact_fx_hedge`, tariff schedules by product and origin | Unhedged import cost; single duty and tariff rate per item in `fact_cost_history` | Chapters 1, 3 and 6 |
| Full balance sheet | `fact_balance_sheet_month` | `fact_cash_debt_month` | Chapter 6 |

**Seasonal buying** (eighth module): for each seasonal item and season, `fact_seasonal_buy` records the buy quantity (ordered before the window, at landed cost), units sold at full price, units sold at markdown and the markdown price, units written off, and stock-out weeks. It supports buy-quantity decisions of the newsvendor type: underage cost = full price − landed cost; overage cost = landed cost − markdown recovery. Sales during stock-outs show sales, not true demand. It replaces the category-level seasonal markdown and write-down rates in the core and reconciles to them. Used in chapter 3.

**Inventory equation reserved for the extension:** opening + receipts + transfers in − units sold − shrink − write-offs − transfers out = closing, plus open purchase commitments. Columns for transfers, write-offs and commitments are reserved in the design now.

## 19. Generation order

The generator runs traffic first and rolls everything up from it, then builds each plan version behind its firewall, then runs the checks.

1. **Structure:** calendar, holidays, markets, stores and opening timeline, products, cost history, accounts, debt facilities.
2. **World:** load structural parameters; draw seeded parameters and hidden events; seal them.
3. **Traffic:** integer daily transactions per store = mature base × store level factor × ramp-up × day-of-week shape × seasonality × holiday effect (authored mapping) × trading status (0 on closed days; an authored share on reduced-hours days; an authored share of a closed day's demand recaptured on the neighbouring open days; on a day next to a closure, only the larger of the pre-holiday sales increment and the recaptured sales increment is applied) × persistent drift × event effects × qualifying category-wide price effect × noise.
4. **Item demand:** baseline expected units per item per store-day, then each item's price-response multiplier (section 12).
5. **Category units and sales:** sum expected item units by category, draw integer category units, derive category mix and items per basket, then gross sales, discounts, markdowns, returns and net sales.
6. **Items:** weekly multinomial allocation of integer category-week units across items by price-adjusted expected units; seasonal items only in their window.
7. **Cost of goods:** landed unit cost from `fact_cost_history` at the real exchange rate, supplier rebates, shrink, end-of-season write-downs.
8. **Inventory and payables:** monthly receipts by the purchasing rule; inventory roll-forward at landed cost; payables by payment terms.
9. **Store costs:** labour hours = fixed coverage (2 staff × open hours) + hours per transaction × transactions, costed at the provincial wage path; occupancy from leases; other costs including card fees.
10. **Company costs:** distribution (fixed + per unit), marketing, head office (fixed + inflation), pre-opening.
11. **Capital and cash:** capex, depreciation, interest on the real base rate path, tax, cash flow, revolver, covenant.
12. **Plan versions:** long-range plan, budgets and Q1–Q2 forecasts, each from its as-of information only (section 10).
13. **Checks** (section 20). Any failure rejects the dataset.

## 20. Reconciliation checks

Every check must pass exactly (to the cent or unit) or the dataset is rejected.

**Basket and sales:**

- All transaction, unit and returned-unit counts are integers.
- `fact_traffic_day.items` = sum of `fact_sales_category_day.units_sold` for that store and day.
- Items per basket = items ÷ transactions, derived and never rounded.
- Average ticket = net sales ÷ transactions.
- Net units = units sold − units returned.
- Gross sales − discounts − markdowns − returns value = net sales.
- Item-week units and net sales sum to category-week totals.
- Stores sum to the company; days → weeks → 4-5-4 months → quarters → years tie exactly.

**Costs and P&L:**

- Labour cost = hours × wage rate.
- Actual P&L in `fact_pnl_month` = roll-up of the detail tables.
- Gross margin, store contribution, adjusted EBITDA and operating income follow the section 8 definitions.

**Inventory, cash and debt:**

- Inventory: opening + receipts − landed cost of units sold − shrink − write-downs = closing, every category and month; and COGS = landed cost of units sold + shrink + write-downs − supplier rebates.
- Cash: opening + flows = closing; revolver keeps cash at or above $2M.
- Debt balances follow draws and repayments; leverage recalculates from its components.

**Planning and documentation:**

- Firewall test passes for every generated plan version (section 10).
- No plan version references data after its as-of date.
- Every column appears in `ref_data_dictionary` with a lineage tag.
- Every assumption used by a version exists in `ref_assumptions` under its assumption set.

## 21. Stage 1 calibration plan

M5 records unit sales, not transactions, so it informs only descriptive sales activity, seasonality (including holiday-period seasonality), store variation, volatility and item concentration. It did not measure Canadian holidays. Transactions and average ticket are calibrated from public retailer ranges and authored relationships; official statistics supply macro history; everything causal, such as price response, is authored.

| Behaviour | Source | Used for |
| --- | --- | --- |
| Day-of-week sales pattern | M5 | Unit-sales shape by day of week; applied to transactions through an authored neutral bridge (weekend basket multiplier 1.00 in the base world, tested in scenarios) |
| Seasonality shape by category | M5 | Category seasonality |
| Sales variation between stores | M5 | Store level factor range |
| Week-to-week volatility and persistence | M5 | Drift and noise settings |
| Item-level intermittent demand and concentration | M5 | Item baseline shares |
| Holiday-period sales patterns | M5 (descriptive only) | Descriptive holiday-seasonality evidence, mapped to Kettlerock's Canadian calendar through an authored relationship; holiday lift sizes are authored |
| Comparable sales and transaction/ticket ranges | Public filings of discount retailers | Transaction and ticket levels and growth ranges; the transactions versus ticket split of sales growth is an authored relationship |
| Gross margin and SG&A ranges | Public filings | Cost structure checks |
| Store opening pace and ramp-up | Public filings | Ramp-up sanity check |
| CAD/USD, base rate, CPI, minimum wages | Bank of Canada, Statistics Canada, provincial governments | Observed history (tag O) |
| Price response | Authored range, not M5 | Ranges in `ref_assumptions`; drawn values sealed; tested in scenarios |

**Output of Stage 1:** `01_calibration/calibrated_parameters.csv`, one row per generator driver. Every business assumption, behavioural parameter, cost rate, range and authored relationship the generator uses appears once in this table, and none exists only as a number in code; structural constants such as days in a week or months in a year stay in code. The table feeds `ref_assumptions` (the ranges visible in the story) and `sealed_world_parameters` (the exact values drawn). Sealed values never appear in this public file: a row points to its sealed draw by `sealed_parameter_id` only. M5 is credited per its usage terms, and its raw data is never committed to the repository.

| Column | Content |
| --- | --- |
| parameter\_id, parameter\_name | Identifier and short name |
| parameter\_group | Store economics, demand shape, variation, growth, pricing, working capital, calendar, macro, capital |
| grain | Time grain (daily, weekly, monthly, annual), basis (units, transactions, sales dollars, cost), level (store, category, province, company) and, for a percentage, its denominator |
| unit | Unit of the value |
| central\_value, lower\_bound, upper\_bound | The calibrated or authored central value and its range |
| distribution | How the value is drawn, for parameters drawn per seed |
| source\_ids | One or more `source_id` values from the benchmark source register, or "authored" |
| evidence\_tag | Lineage tag from section 16 (B, O, A, S, E, D, R) |
| method | Taken directly, midpoint of a range, derived, or authored and checked against a range |
| rationale | Why this value, and where it sits relative to the evidence |
| evidence\_confidence | High, medium or low: how solid the evidence is |
| modeling\_confidence | High, medium or low: how sure the Kettlerock value is right |
| constraint | Parameters this one is tied to, and which of them is derived (for example sales = transactions × average ticket) |
| downstream\_table | Table or generation step that reads it |
| validation\_target | What the generated data is checked against |
| sealed\_parameter\_id | Pointer to the sealed draw, where one exists |

**Benchmark source register:** every external figure or series used for calibration (filings, M5 summary statistics, government series) is logged in `01_calibration/benchmark_sources.csv`, one row per extracted value, so "calibrated to public benchmarks" can be checked line by line.

| Column | Content |
| --- | --- |
| source\_id | Unique key, referenced by the data dictionary, `ref_assumptions` and the parameter table |
| source\_type | Filing, dataset, government series or legislation |
| company\_or\_publisher | Company, dataset owner or statistical agency |
| document | Document or dataset name, form type and filing or release date |
| source\_location | Page, table, section, or dataset column the value came from |
| metric | What was extracted, in the source's own definition |
| period | Fiscal period with calendar months, or date range |
| extracted\_value | The value as reported |
| unit | Unit of the extracted value (%, $, count, rate) |
| use\_in\_kettlerock | Parameter or range it informs, and how |
| url | Link to the source |
| retrieval\_date | Date the value was extracted |

## 22. Storyline: the FY2028 planning season

The project follows one planning season at Kettlerock, from the Q3 FY2027 close in November 2026 to the late-January 2027 board meeting that approves the FY2028 plan and the refreshed long-range plan. Seven chapters answer the season's questions in dependency order; each chapter's decision becomes the starting point for the next, so the FY2028 plan is built in layers.

The setting: supplier costs are rising against fixed price points, the newest Atlantic stores are still ramping, and each autumn the holiday inventory build pushes leverage toward the 3.50x covenant just as the October quarter-end test arrives. The private equity owner wants a credible exit plan at the same board meeting.

| Chapter | Question | Led by | Builds on | Data |
| --- | --- | --- | --- | --- |
| 0. Where we stand | How is FY2027 tracking against budget, why, and what must Q4 deliver? | FP&A | Baseline | Core |
| 1. The $1.25 problem | How should Kettlerock protect margin when costs rise but price points are fixed? | Strategic finance with merchandising | Margin variance from chapter 0 | Core; tariff detail optional |
| 2. Fix, move or close | Which stores should be renewed, fixed, relocated or closed, especially where leases expire in FY2028–FY2029? | Strategic finance with real estate | Store profitability under the chapter 1 margin structure | Core + authored sales-transfer assumption |
| 3. Cash before Christmas | How can peak borrowing fall without losing holiday sales? | Supply chain finance with treasury | Store base after chapter 2 | Core + seasonal buying extension |
| 4. Grow or protect | How many openings a year can the business afford under the covenant? | Strategic finance | New-store profile (chapter 2) and cash profile (chapter 3) | Core |
| 5. Go west? | Should affordable growth go to Western Canada or to more stores in the East? | Strategic finance with real estate and supply chain | Affordable pace (chapter 4) | Core + western cost and distribution-centre inputs, specified with the chapter |
| 6. Ready to sell | Which initiatives create the most exit value, and how do the owner's returns respond to exit timing and multiple? | Strategic finance for the owner | Every earlier chapter's initiative | Core + long-range plan |

- **Chapter 0, Where we stand.** Year-to-date variance against the FY2027 budget, split into transactions and ticket, comparable and new stores, category mix and margin drivers; accuracy of the May and August forecasts; the Q3 reforecast, what the holiday quarter must deliver, and the full-year covenant outlook. Output: the starting point of the FY2028 plan and the measured list of problems the year has exposed.
- **Chapter 1, The $1.25 problem.** The margin gap broken into product cost, mix, markdowns and shrink; where price points have room by category, item and store type; the transaction risk of broad price moves; absorbing costs, selective price-point moves, pack-size changes and domestic sourcing compared on break-even volume loss, tested across the full range of customer price response. Output: the FY2028 pricing and sourcing plan and a new margin structure by category and store.
- **Chapter 2, Fix, move or close.** Every store ranked on four-wall profitability under the new margins; weak results traced to market, execution or cost; Atlantic stores separated into underperforming versus still ramping; each expiring lease assessed for renewal, rent renegotiation, remodel, relocation or closure, with remodel returns and closure savings net of sales moving to sister stores. Output: the FY2028 store base and the profile of a good Kettlerock store.
- **Chapter 3, Cash before Christmas.** Monthly cash tied up in inventory; seasonal sell-through at full price, at markdown and not at all; newsvendor-based buy depths; the value of better import terms; inventory targets; the resulting peak borrowing and covenant headroom. Output: the FY2028 cash plan and the funding room for growth.
- **Chapter 4, Grow or protect.** Cohort payback against the 3-year hurdle; accelerated, planned and slowed opening paces run month by month through cash and the covenant, including the pre-holiday peak; EBITDA effects of ramping stores and pre-opening costs. Output: the affordable opening pace.
- **Chapter 5, Go west?** Western store economics at western rents and wages; the store count at which a second distribution centre beats freight or a third-party warehouse; filling the East, full western entry and a western test cluster valued against each other. Output: the regional growth plan and its capital.
- **Chapter 6, Ready to sell.** EBITDA normalized as a buyer would, including pre-opening, one-offs, currency effects and the 53-week FY2029; the value bridge across EBITDA growth, multiple and debt paydown; initiatives ranked by value for capital and risk; owner returns by exit year and multiple. Output: the value creation plan.

**First release:** chapters 0 and 1. Later chapters follow in order, each in its own folder (section 23).

- When the season's work is complete, the sealed events log is opened and compared with the diagnosis.
- Multi-seed robustness: the unchanged methods are applied to 3–4 other seeds, reporting where they hold and where they fail.

## 23. Repository structure

One repository holds the company, the engine and a folder per chapter of the planning season; each chapter is written in the voice of the role that leads it.

```
kettlerock-value-stores/
├── README.md                      (framing, disclosure, storyline, lineage summary)
├── 00_company/                    (this specification)
├── 01_calibration/                (Stage 1: how retail behaves)
│   ├── benchmark_sources.csv      (one row per external figure or series; columns in section 21)
│   └── calibrated_parameters.csv  (each parameter: value, source_id, method, confidence)
├── 02_engine/                     (generator, checks, assumptions registry, data dictionary)
├── 03_ch0_where_we_stand/         (FP&A)
├── 04_ch1_price_points/           (strategic finance with merchandising)
├── 05_ch2_store_portfolio/        (strategic finance with real estate)
├── 06_ch3_working_capital/        (supply chain finance with treasury)
├── 07_ch4_expansion_pace/         (strategic finance)
├── 08_ch5_regional_growth/        (strategic finance with real estate and supply chain)
└── 09_ch6_value_creation/         (strategic finance for the owner)
```

Sealed outputs are stored outside the analysis folders until each analysis is finished.
