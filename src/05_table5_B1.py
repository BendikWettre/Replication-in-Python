"""Table 5 and Appendix Table B1."""
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "processed"
TABLES = ROOT / "output" / "tables"
MONTHLY_FILE = PROCESSED / "monthly.csv"

monthly = pd.read_csv(MONTHLY_FILE, index_col="month").dropna(subset=["mkt_var"])

# Table 5: WML on bear indicator and market variance

specs_t5 = {
    "(1)" :  "wml ~ bear",
    "(2)" :  "wml ~ mkt_var",
    "(3)" :  "wml ~ bear + mkt_var",
    "(4)" :  "wml ~ bear:mkt_var",
    "(5)" :  "wml ~ bear + mkt_var + bear:mkt_var"
 }

params_t5, tvals_t5 = {}, {}
for name, formula in specs_t5.items():
    res = smf.ols(formula, data=monthly).fit()
    params_t5[name] = res.params
    tvals_t5[name] = res.tvalues

params_t5 = pd.DataFrame(params_t5) 
tvals_t5 = pd.DataFrame(tvals_t5)
params_t5.loc[["Intercept","bear"]] *= 100
params_t5 = params_t5.reindex(["Intercept", "bear", "mkt_var", "bear:mkt_var"])
tvals_t5 = tvals_t5.reindex(["Intercept", "bear", "mkt_var", "bear:mkt_var"])

rows_t5 = {}
for var in params_t5.index:
    rows_t5[var] = params_t5.loc[var].map(lambda x: f"{x:.3f}" if pd.notna(x) else "")
    rows_t5[f"t_{var}"] = tvals_t5.loc[var].map(lambda x: f"({x:.1f})" if pd.notna(x) else "")

table5 = pd.DataFrame(rows_t5).T

# Display labels for LaTeX
row_labels_t5 = {
    "Intercept"        : r"$\hat\gamma_0$",
    "t_Intercept"      : r"",
    "bear"             : r"$\hat\gamma_B$",
    "t_bear"           : r"",
    "mkt_var"          : r"$\hat\gamma_{\sigma^2_m}$",
    "t_mkt_var"        : r"",
    "bear:mkt_var"     : r"$\hat\gamma_{\text{int}}$",
    "t_bear:mkt_var"   : r"",
}

table5_tex = (table5.rename(index=row_labels_t5)
               .rename_axis(columns="Coefficient"))
table5_tex.to_latex(TABLES / "table5.tex", column_format="lccccc")


# Table B1: WML, HML-devil and SMB on the panic indicator

# HML-d columns end in 2012:12 in the paper
monthly.loc["2013-01":, "hmld"] = np.nan

# 50/50 WML and HML-d portfolio, columns (7)-(8)
monthly["wml_hmld"] = 0.5 * monthly["wml"] + 0.5 * monthly["hmld"]

specs_b1 = {
    "(1)": "wml ~ panic + mkt_rf + panic:mkt_rf",
    "(2)": "wml ~ panic + mkt_rf + panic:mkt_rf + smb + panic:smb + hml + panic:hml",
    "(3)": "hmld ~ panic",
    "(4)": "hmld ~ panic + mkt_rf + panic:mkt_rf",    
    "(5)": "smb ~ panic",
    "(6)": "smb ~ panic + mkt_rf + panic:mkt_rf",
    "(7)": "wml_hmld ~ panic",
    "(8)": "wml_hmld ~ panic + mkt_rf + panic:mkt_rf",
}

params_b1, tvals_b1 = {}, {}
for name, formula in specs_b1.items():
    res = smf.ols(formula, data=monthly).fit()
    params_b1[name] = res.params
    tvals_b1[name] = res.tvalues

params_b1 = pd.DataFrame(params_b1) 
tvals_b1 = pd.DataFrame(tvals_b1)
params_b1.loc[["Intercept", "panic"]] *= 1200

order_b1 = ["Intercept", "panic", "mkt_rf", "panic:mkt_rf", "smb", "panic:smb", "hml", "panic:hml"]
params_b1 = params_b1.reindex(order_b1)
tvals_b1 = tvals_b1.reindex(order_b1)

rows_b1 = {}
for var in params_b1.index:
    rows_b1[var] = params_b1.loc[var].map(lambda x: f"{x:.2f}" if pd.notna(x) else "")
    rows_b1[f"t_{var}"] = tvals_b1.loc[var].map(lambda x: f"({x:.1f})" if pd.notna(x) else "")

tableb1 = pd.DataFrame(rows_b1).T

# Display labels for LaTeX
row_labels_b1 = {
    "Intercept"        : r"$\alpha$",
    "t_Intercept"      : r"",
    "panic"            : r"$I_{B\sigma^2}$",
    "t_panic"          : r"",
    "mkt_rf"           : r"$r^e_m$",
    "t_mkt_rf"         : r"",
    "panic:mkt_rf"     : r"$I_{B\sigma^2}\cdot r^e_m$",
    "t_panic:mkt_rf"   : r"",
    "smb"              : r"$r_{\text{smb}}$",
    "t_smb"            : r"",
    "panic:smb"        : r"$I_{B\sigma^2}\cdot r_{\text{smb}}$",
    "t_panic:smb"      : r"",
    "hml"              : r"$r_{\text{HML}}$",
    "t_hml"            : r"",
    "panic:hml"        : r"$I_{B\sigma^2}\cdot r_{\text{HML}}$",
    "t_panic:hml"      : r"",
}

tableb1_tex = (tableb1.rename(index=row_labels_b1)
               .rename_axis(columns="Variable"))

tex_b1 = tableb1_tex.to_latex(column_format="l" + "c" * 8)

# Group headers over each pair of columns (dependent variable)
groups = ["WML", "HML-d", "SMB", "WML+HML-d"]
group_row = " & " + " & ".join(rf"\multicolumn{{2}}{{c}}{{{g}}}" for g in groups) + r" \\" + "\n"
rules = "".join(rf"\cmidrule(lr){{{2 + 2*i}-{3 + 2*i}}}" for i in range(4)) + "\n"
tex_b1 = tex_b1.replace("\\toprule\n", "\\toprule\n" + group_row + rules, 1)

(TABLES / "tableB1.tex").write_text(tex_b1)
