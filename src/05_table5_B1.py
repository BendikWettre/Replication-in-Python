from pathlib import Path
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "processed"
TABLES = ROOT / "output" / "tables"
MONTHLY_FILE = PROCESSED / "monthly.csv"

monthly = pd.read_csv(MONTHLY_FILE, index_col="month").dropna(subset=["mkt_var"])

specs = {
    "(1)" :  "wml ~ bear",
    "(2)" :  "wml ~ mkt_var",
    "(3)" :  "wml ~ bear + mkt_var",
    "(4)" :  "wml ~ bear:mkt_var",
    "(5)" :  "wml ~ bear + mkt_var + bear:mkt_var"
 }

params, tvals, r2 = {}, {}, {}
for name, formula in specs.items():
    res = smf.ols(formula, data=monthly).fit()
    params[name] = res.params
    tvals[name] = res.tvalues
    r2[name] = res.rsquared_adj

params = pd.DataFrame(params) 
tvals = pd.DataFrame(tvals)
params.loc[["Intercept","bear"]] *= 100
params = params.reindex(["Intercept", "bear", "mkt_var", "bear:mkt_var"])
tvals = tvals.reindex(["Intercept", "bear", "mkt_var", "bear:mkt_var"])

rows = {}
for var in params.index:
    rows[var] = params.loc[var].map(lambda x: f"{x:.3f}" if pd.notna(x) else "")
    rows[f"t_{var}"] = tvals.loc[var].map(lambda x: f"({x:.1f})" if pd.notna(x) else "")

table5 = pd.DataFrame(rows).T

# Display labels for LaTeX
row_labels = {
    "Intercept"        : r"$\hat\gamma_0$",
    "t_Intercept"      : r"",
    "bear"             : r"$\hat\gamma_B$",
    "t_bear"           : r"",
    "mkt_var"          : r"$\hat\gamma_{\sigma^2_m}$",
    "t_mkt_var"        : r"",
    "bear:mkt_var"     : r"$\hat\gamma_{\text{int}}$",
    "t_bear:mkt_var"   : r"",
}

table5_tex = (table5.rename(index=row_labels)
               .rename_axis(columns="Coefficient"))
table5_tex.to_latex(TABLES / "table5.tex", column_format="lccccc")
