# Kettlerock Value Stores

A strategic finance portfolio project built on a fictional Canadian value retailer. Kettlerock's data is fully synthetic: generated to behave like a real 40-store chain and calibrated to public retailer filings, Canadian government statistics and the M5 retail dataset.

## The planning season

It is November 2026. Kettlerock has closed the third quarter of fiscal 2027, and its finance team is preparing the FY2028 plan and a refreshed long-range plan for the January board meeting. The project follows that season in seven chapters, each building on the last.

| Chapter | Question |
| --- | --- |
| 0. Where we stand | How is FY2027 tracking against budget, why, and what must Q4 deliver? |
| 1. The $1.25 problem | How should Kettlerock protect margin when costs rise but price points are fixed? |
| 2. Fix, move or close | Which stores should be renewed, fixed, relocated or closed? |
| 3. Cash before Christmas | How can peak borrowing fall without losing holiday sales? |
| 4. Grow or protect | How many openings a year can the business afford under its debt covenant? |
| 5. Go west? | Should growth go to Western Canada or to more stores in the East? |
| 6. Ready to sell | Which initiatives create the most value for the owner at exit? |

## Repository

| Folder | Contents |
| --- | --- |
| `00_company` | Design specification: company profile, unit economics, calendar, accounting policy, data model and storyline |
| `01_calibration` | Benchmark source register, M5 retail pattern analysis and government data extracts |

## Data and sources

- Kettlerock Value Stores does not exist. All company data is synthetic.
- Company benchmarks come from public filings of Dollarama, Dollar Tree, Five Below and Dollar General. Macro and legal inputs come from the Bank of Canada, Statistics Canada, the Government of Canada minimum wage database and provincial retail closing laws. Every external figure is logged in `01_calibration/benchmark_sources.csv` with its source, location and retrieval date.
- Retail sales patterns are informed by the M5 Forecasting dataset (Makridakis, Spiliotis and Assimakopoulos, 2022, *International Journal of Forecasting*), used for descriptive statistics only. The raw M5 files are not included; download them from the Kaggle M5 Forecasting – Accuracy competition and place them next to `01_calibration/m5_patterns.ipynb` to rerun the analysis.

**Author:** Fatiha Abisola Okesola
