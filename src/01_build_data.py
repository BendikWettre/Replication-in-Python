"""
Builds the monthly and daily data sets from the raw files in raw/ and saves
them to processed/monthly.csv and processed/daily.csv.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "raw"
PROCESSED = ROOT / "processed"

DM_MONTHLY_FILE = RAW / "dm" / "m_m_pt_tot.txt"
DM_DAILY_FILE = RAW / "dm" / "d_m_pt_tot.txt"
FRENCH_MONTHLY_FILE = RAW / "F-F_Research_Data_Factors.txt"
FRENCH_DAILY_FILE = RAW / "F-F_Research_Data_Factors_daily.csv"
SP500_FILE = RAW / "sp500_daily.csv"
VIX_FILE = RAW / "vix_daily.csv"
CRSP_VW_FILE = RAW / "crsp_vw_monthly.csv"

SAMPLE_START = "1927-01"
SAMPLE_END = "2013-03"
LAST_DAY = "2013-03-28"

BEAR_WINDOW = 24   # months
VAR_WINDOW = 126   # trading days
DAYS_PER_YEAR = 252


def read_dm(path):
    """Read a DM decile file and return decile returns in wide format plus WML."""
    long = pd.read_csv(path, sep=r"\s+", header=None,
                       names=["date", "decile", "ret", "me", "n"])
    long["date"] = pd.to_datetime(long["date"].astype(str), format="%Y%m%d")
    wide = long.pivot(index="date", columns="decile", values="ret")
    wide.columns = [f"d{i}" for i in wide.columns]
    wide["wml"] = wide["d10"] - wide["d1"]  # zero-investment, so no RF
    return wide


# Monthly data

dm_m = read_dm(DM_MONTHLY_FILE)
dm_m.index = dm_m.index.to_period("M")  # common key with French (YYYYMM)

# French monthly: skip the header text and stop before the annual block
with open(FRENCH_MONTHLY_FILE) as f:
    lines = f.readlines()
annual_start = next(i for i, line in enumerate(lines) if line.strip().startswith("Annual"))

ff_m = pd.read_csv(FRENCH_MONTHLY_FILE, sep=r"\s+", header=None, skiprows=4,
                   nrows=annual_start - 5,
                   names=["date", "mkt_rf", "smb", "hml", "rf"])
ff_m.index = pd.PeriodIndex(ff_m.pop("date").astype(int).astype(str), freq="M")
ff_m = ff_m / 100
ff_m["mkt"] = ff_m["mkt_rf"] + ff_m["rf"]

# Bear indicator: cumulative market return over t-24..t-1 is negative.
# Early 1927 uses the shorter history available (French starts 1926-07).
log_mkt = np.log1p(ff_m["mkt"])
ff_m["mkt_24m"] = np.expm1(log_mkt.rolling(BEAR_WINDOW, min_periods=1).sum().shift(1))
ff_m["bear"] = (ff_m["mkt_24m"] < 0).astype(int)

# Same indicator from the CRSP VW index (robustness check)
crsp = pd.read_csv(CRSP_VW_FILE, parse_dates=["mthcaldt"]).dropna()
crsp.index = crsp.pop("mthcaldt").dt.to_period("M")
crsp_24m = np.expm1(np.log1p(crsp["vwretd"]).rolling(BEAR_WINDOW, min_periods=1)
                    .sum().shift(1))
ff_m["bear_crsp"] = (crsp_24m.reindex(ff_m.index) < 0).astype(int)

monthly = dm_m.join(ff_m, how="left").loc[SAMPLE_START:SAMPLE_END]
monthly["bull"] = 1 - monthly["bear"]
monthly["up"] = (monthly["mkt_rf"] > 0).astype(int)


# Daily data

dm_d = read_dm(DM_DAILY_FILE)

ff_d = pd.read_csv(FRENCH_DAILY_FILE, skiprows=4, index_col=0)
ff_d.columns = ["mkt_rf", "smb", "hml", "rf"]
ff_d.index = pd.to_datetime(ff_d.index.astype(str).str.strip(),
                            format="%Y%m%d", errors="coerce")
ff_d = ff_d[ff_d.index.notna()].astype(float) / 100  # drops the copyright line

assert dm_d.index.isin(ff_d.index).all(), "DM days missing in French daily file"
daily = dm_d.join(ff_d, how="left")

# Market variance: 126-day variance of daily Mkt-RF at the end of month t-1,
# annualized. The window starts on the first DM day, so July 1927 is the
# first month with a value.
var_daily = daily["mkt_rf"].rolling(VAR_WINDOW).var() * DAYS_PER_YEAR
var_month_end = var_daily.groupby(daily.index.to_period("M")).last()
monthly["mkt_var"] = var_month_end.shift(1).reindex(monthly.index)

# Panic indicator: bear * variance, scaled by the mean variance in bear months
v_bar_b = monthly.loc[monthly["bear"] == 1, "mkt_var"].mean()
monthly["panic"] = monthly["bear"] * monthly["mkt_var"] / v_bar_b

month_vars = ["bear", "bull", "mkt_var", "panic"]
daily = daily.join(monthly[month_vars], on=daily.index.to_period("M"))


# Variance-swap returns (1990-2013)

sp = pd.read_csv(SP500_FILE, parse_dates=["dlycaldt"], index_col="dlycaldt")
sp = sp.loc[:LAST_DAY]

vix = pd.read_csv(VIX_FILE, parse_dates=["date"])
vix = vix.drop_duplicates(subset="date").set_index("date")["vix"]
vix = vix.reindex(sp.index)  # keep S&P trading days only
# VIX is missing on 1991-03-01, 1997-01-31 and 1997-11-26; these stay NaN.

# Appendix A.2, eq. (15). The paper writes D_t = (1 + r_1m)^(20/252), but a
# discount factor should be below one, so the exponent is -20/252. With
# French's daily RF this equals (1 + rf_daily)^(-20).
log_ret = np.log(sp["spindx"] / sp["spindx"].shift(1))
vix2 = vix ** 2
discount = (1 + daily["rf"].reindex(sp.index)) ** -20

r_vs = discount * ((DAYS_PER_YEAR * (100 * log_ret) ** 2 - vix2.shift(1)) / 21
                   + 20 / 21 * (vix2 - vix2.shift(1)))

assert sp.index.isin(daily.index).all(), "S&P days missing in DM daily file"
daily["spindx"] = sp["spindx"]
daily["vix"] = vix
daily["r_vs"] = r_vs


# Checks against the paper (values in brackets)

def pct(x):
    return f"{100 * x:.2f}"

print("MONTHLY")
print(f"  Months: {len(monthly)} ({monthly.index[0]} to {monthly.index[-1]})  [1,035]")
print(f"  Bear / up / down: {monthly['bear'].sum()} / {monthly['up'].sum()} / "
      f"{(1 - monthly['up']).sum()}  [183 / 618 / 417]")
print(f"  Bear months, CRSP VW: {monthly['bear_crsp'].sum()}")
print(f"  WML mean / sd, % p.a.: {pct(monthly['wml'].mean() * 12)} / "
      f"{pct(monthly['wml'].std() * 12**0.5)}  [17.9 / 30.0]")
print(f"  Mkt-RF mean / sd, % p.a.: {pct(monthly['mkt_rf'].mean() * 12)} / "
      f"{pct(monthly['mkt_rf'].std() * 12**0.5)}  [7.7 / 18.8]")
worst = monthly["wml"].nsmallest(3)
print("  Worst WML months: "
      + ", ".join(f"{d} {pct(r)}" for d, r in worst.items())
      + "  [1932-08 -74.36, 1932-07 -60.98, 2001-01 -49.19]")
print("  24-month market return 1932-08 / 2009-04 / 1974-01: "
      + " / ".join(pct(monthly.loc[m, "mkt_24m"]) for m in ["1932-08", "2009-04", "1974-01"])
      + "  [-67.77 / -40.62 / -5.67]")
print(f"  Months with market variance: {monthly['mkt_var'].notna().sum()}  [1,029]")

print("DAILY")
print(f"  Days: {len(daily)} ({daily.index[0]:%Y-%m-%d} to {daily.index[-1]:%Y-%m-%d})")
print(f"  Missing Mkt-RF: {daily['mkt_rf'].isna().sum()}")
print(f"  Days with S&P 500 / VIX / variance-swap return: "
      f"{daily['spindx'].notna().sum()} / {daily['vix'].notna().sum()} / "
      f"{daily['r_vs'].notna().sum()}")


PROCESSED.mkdir(exist_ok=True)
monthly.to_csv(PROCESSED / "monthly.csv", index_label="month")
daily.to_csv(PROCESSED / "daily.csv", index_label="date")
