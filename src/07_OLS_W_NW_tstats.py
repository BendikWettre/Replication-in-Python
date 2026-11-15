from pathlib import Path
import pandas as pd
import statsmodels.formula.api as smf


ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "processed"
TABLES = ROOT / "output" / "tables"

DAILY_FILE = PROCESSED / "daily.csv"
MONTHLY_FILE = PROCESSED / "monthly.csv"

monthly = pd.read_csv(MONTHLY_FILE, index_col="month")
monthly_var = monthly.dropna(subset=["mkt_var"])
daily = pd.read_csv(DAILY_FILE, index_col="date", parse_dates=["date"])
daily_t6 = daily.loc["1990-01-02":"2013-03-28"].copy()
daily_t6["r_vs"] /= 10000
v_bar_b = daily_t6.loc[daily_t6["bear"] == 1, "mkt_var"].mean()
daily_t6["panic"] = daily_t6["bear"] * daily_t6["mkt_var"] / v_bar_b

NW_LAGS_MONTHLY = 6     # months; mkt_var uses ~6 months of daily data
NW_LAGS_DAILY = 126     # trading days; length of the variance window


def three_tstats(formula, data, var, lags):
    """Estimate and t-statistics (OLS, White, Newey-West) for one coefficient."""
    model = smf.ols(formula, data=data)
    ols = model.fit()
    white = model.fit(cov_type="HC1")
    nw = model.fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    return [ols.params[var], ols.tvalues[var], white.tvalues[var], nw.tvalues[var]]


rows = [
    # (label, formula, data, variable, lags)
    (r"3 (3) & $\hat\beta_{B,U}$", "wml ~ bear + mkt_rf + bear:mkt_rf + bear:up:mkt_rf",
     monthly, "bear:up:mkt_rf", NW_LAGS_MONTHLY),
    (r"5 (2) & $\hat\gamma_{\sigma^2_m}$", "wml ~ mkt_var", 
     monthly_var, "mkt_var", NW_LAGS_MONTHLY),
    (r"5 (4) & $\hat\gamma_{\text{int}}$", "wml ~ bear:mkt_var", 
     monthly_var, "bear:mkt_var", NW_LAGS_MONTHLY),
    (r"6 (2) & $I_{B\sigma^2}$", "wml ~ panic + mkt_rf + panic:mkt_rf", 
     daily_t6, "panic", NW_LAGS_DAILY),
    (r"6 (2) & $I_{B\sigma^2}\cdot \tilde r^e_{m,t}$", "wml ~ panic + mkt_rf + panic:mkt_rf", 
     daily_t6, "panic:mkt_rf", NW_LAGS_DAILY),
    (r"6 (3) & $I_{B\sigma^2}\cdot \tilde r_{vs,t}$", "wml ~ panic + mkt_rf + panic:mkt_rf + r_vs + panic:r_vs", 
     daily_t6, "panic:r_vs", NW_LAGS_DAILY),
]

results = {label: three_tstats(f, d, v, l) for label, f, d, v, l in rows}
table = pd.DataFrame(results, index=["Estimate", "t (OLS)", "t (White)", "t (Newey-West)"]).T
table.loc[r"6 (2) & $I_{B\sigma^2}$", "Estimate"] *= 25200  # annualized %

# LaTeX export
table_tex = table.copy().astype(object)
table_tex["Estimate"] = table["Estimate"].map(lambda x: f"{x:.3f}")
for col in ["t (OLS)", "t (White)", "t (Newey-West)"]:
    table_tex[col] = table[col].map(lambda x: f"{x:.2f}")
tex = table_tex.to_latex(column_format="llcccc")
tex = tex.replace("\\toprule\n & ", "\\toprule\nTable & Coefficient & ", 1)
(TABLES / "table_robust_tstats.tex").write_text(tex)

