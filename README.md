# Replication of Daniel and Moskowitz (2016), "Momentum Crashes"

Replication of Sections 2 and 3 (excluding Section 4, "Dynamic weighting of
the momentum portfolio", and Section 5, "International equities and other
asset classes") of

> Daniel, K. and Moskowitz, T. J. (2016). Momentum crashes. *Journal of
> Financial Economics*, 122(2), 221–247.
> [doi:10.1016/j.jfineco.2015.12.002](https://doi.org/10.1016/j.jfineco.2015.12.002)

The code runs from the raw data files to the tables (`.tex`) and figures
(`.pdf`) used in the report. Deviations from the paper and their likely causes
are documented in [docs/replication_notes.md](docs/replication_notes.md).

## Output

| Script | Output | Content |
|---|---|---|
| `01_build_data.py` | `processed/monthly.csv`, `processed/daily.csv` | Cleaned monthly and daily data; prints control numbers |
| `02_table1_2_fig1_2.py` | `table1.tex`, `table2.tex`, `figure1.pdf`, `figure2.pdf` | Decile and WML characteristics, 15 worst WML months, cumulative returns |
| `03_fig3_4.py` | `figure3.pdf`, `figure4.pdf`, `figure4_monthly_hedge.pdf` | Rolling market betas, ex ante vs. ex post hedged WML |
| `04_table3_4.py` | `table3.tex`, `table4.tex` | Market-timing regressions, optionality by decile |
| `05_table5_B1.py` | `table5.tex`, `tableB1.tex` | WML on bear indicator and market variance; Appendix Table B1 |
| `06_table6.py` | `table6.tex` | Daily WML on variance-swap returns |
| `07_OLS_W_NW_tstats.py` | `table_robust_tstats.tex` | Robustness: OLS, White and Newey–West *t*-statistics (not in the paper) |

Tables are written to `output/tables/` and figures to `output/figures/`.

## How to run

Requires Python 3.11 or later (developed with 3.14).

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows; on macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Place the data files in `raw/` as described below, then run the scripts in
order from the project root:

```bash
python src/01_build_data.py
python src/02_table1_2_fig1_2.py
python src/03_fig3_4.py
python src/04_table3_4.py
python src/05_table5_B1.py
python src/06_table6.py
python src/07_OLS_W_NW_tstats.py
```

`01_build_data.py` must run first; the other scripts only read from
`processed/` and can run in any order.

## Data

The raw data are not included in the repository: the WRDS files may not be
redistributed under the WRDS terms of use, and the other files are available
from their original sources. Files in `raw/` are never edited; all cleaning
happens in `01_build_data.py`.

```
raw/
  dm/m_m_pt_tot.txt
  dm/d_m_pt_tot.txt
  F-F_Research_Data_Factors.txt
  F-F_Research_Data_Factors_daily.csv
  sp500_daily.csv
  vix_daily.csv
  crsp_vw_monthly.csv
  The Devil in HMLs Details Factors Monthly.xlsx
```

### Daniel–Moskowitz momentum portfolios (`raw/dm/`)

The authors' own decile portfolios (`DM_data_2014_02`), from Kent Daniel's
data page ([kentdaniel.net](http://www.kentdaniel.net/data.php)). Unzip into
`raw/dm/`. Only `m_m_pt_tot.txt` (monthly) and `d_m_pt_tot.txt` (daily) are
used: deciles sorted on total returns from *t*−12 to *t*−2, all-firm
breakpoints, value-weighted, rebalanced monthly.

### Fama–French factors

From the [Kenneth French Data Library](https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html).

- **Monthly** (`F-F_Research_Data_Factors.txt`): the **July 2013 vintage**
  (built from the 201307 CRSP database), from the library's *Historical
  Archives*. This is the version available to the authors and reproduces the
  paper's 183 bear-market months. Do not replace it with a current vintage.
- **Daily** (`F-F_Research_Data_Factors_daily.csv`): current version of
  *Fama/French 3 Factors [Daily]* (here built from the 202609 CRSP database).
  Used for the 126-day market variance, rolling betas and Table 6.

### WRDS

Downloaded from [WRDS](https://wrds-www.wharton.upenn.edu/) (subscription
required), sample 1990-01-02 to 2013-03-28 unless stated otherwise:

- `sp500_daily.csv`: CRSP → Index → *Daily Stock Market Indexes* (CRSP v2/CIZ
  format), S&P 500 series. Columns `dlycaldt, sprtrn, spindx`.
- `vix_daily.csv`: Cboe Options → *Cboe Indexes*, VIX close. Columns
  `date, vix`. Duplicate dates and non-trading days are removed in code.
- `crsp_vw_monthly.csv`: CRSP → Index → *Monthly Stock Market Indexes* (v2/CIZ),
  value-weighted return including distributions, 1925-12 to 2013-03. Columns
  `mthcaldt, vwretd`. Used only as a robustness check of the bear indicator.

### HML-devil factor (AQR)

`The Devil in HMLs Details Factors Monthly.xlsx` from the
[AQR Data Library](https://www.aqr.com/Insights/Datasets) (*The Devil in HML's
Details: Factors, Monthly*), downloaded November 2026. The sheet "HML Devil",
column "USA", is used for columns (3), (4), (7) and (8) of Table B1. AQR
revises this series, so a later download may give slightly different numbers.

## Repository structure

```
raw/          original data files (not in the repository)
processed/    cleaned data written by 01_build_data.py (not in the repository)
src/          analysis scripts
output/       tables (.tex) and figures (.pdf)
docs/         replication notes
```
