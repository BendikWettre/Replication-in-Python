from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "processed"
TABLES = ROOT / "output" / "tables"

DAILY_FILE = PROCESSED / "daily.csv"
daily = pd.read_csv(DAILY_FILE, index_col="date", parse_dates=["date"])
start, end = "1990-01-02", "2013-03-28"

daily_t6 = daily.loc[start:end]
daily_t6["r_vs"] /= 10000

# Normalize panic by the mean bear-market variance in the 1990-2013 sample
v_bar_b = daily_t6.loc[daily_t6["bear"] == 1, "mkt_var"].mean()
daily_t6["panic"] = daily_t6["bear"] * daily_t6["mkt_var"] / v_bar_b


specs_t6 = {
    "(1)" :  "wml ~ panic",
    "(2)" :  "wml ~ panic + mkt_rf + panic:mkt_rf",
    "(3)" :  "wml ~ panic + mkt_rf + panic:mkt_rf + r_vs + panic:r_vs",
 }

params_t6, tvals_t6 = {}, {}
for name, formula in specs_t6.items():
    res = smf.ols(formula, data=daily_t6).fit()
    params_t6[name] = res.params
    tvals_t6[name] = res.tvalues

params_t6 = pd.DataFrame(params_t6) 
tvals_t6 = pd.DataFrame(tvals_t6)
params_t6.loc[["Intercept","panic"]] *= 25200
order_t6 = ["Intercept", "panic", "mkt_rf", "panic:mkt_rf", "r_vs", "panic:r_vs"]
params_t6 = params_t6.reindex(order_t6)
tvals_t6 = tvals_t6.reindex(order_t6)

rows_t6 = {}
for var in params_t6.index:
    rows_t6[var] = params_t6.loc[var].map(lambda x: f"{x:.2f}" if pd.notna(x) else "")
    rows_t6[f"t_{var}"] = tvals_t6.loc[var].map(lambda x: f"({x:.1f})" if pd.notna(x) else "")

table6 = pd.DataFrame(rows_t6).T
print(table6)
# Display labels for LaTeX
row_labels_t6 = {
    "Intercept"        : r"$\alpha$",
    "t_Intercept"      : r"",
    "panic"            : r"$I_{B\sigma^2}$",
    "t_panic"          : r"",
    "mkt_rf"           : r"$\tilde{r}_{m,t}^e$",
    "t_mkt_rf"         : r"",
    "panic:mkt_rf"     : r"$I_{B\sigma^2}\cdot \tilde{r}_{m,t}^e$",
    "t_panic:mkt_rf"   : r"",
    "r_vs"             : r"$\tilde{r}_{vs,t}$",
    "t_r_vs"           : r"",
    "panic:r_vs"       : r"$I_{B\sigma^2}\cdot \tilde{r}_{vs,t}$",
    "t_panic:r_vs"     : r"",
}

table6_tex = (table6.rename(index=row_labels_t6)
               .rename_axis(columns="Independent variable"))
table6_tex.to_latex(TABLES / "table6.tex", column_format="l" + "c" * 3)
