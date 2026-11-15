from pathlib import Path
import pandas as pd
import statsmodels.formula.api as smf

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "processed"
TABLES = ROOT / "output" / "tables"
MONTHLY_FILE = PROCESSED / "monthly.csv"

monthly = pd.read_csv(MONTHLY_FILE, index_col="month")


# Building Table 3: Market timing results
specs = {
    "(1)" : "wml ~ mkt_rf",
    "(2)" :  "wml ~ mkt_rf + bear + bear:mkt_rf",
    "(3)" :  "wml ~ mkt_rf + bear + bear:mkt_rf + bear:up:mkt_rf",
    "(4)" :  "wml ~ mkt_rf + bear:mkt_rf + bear:up:mkt_rf"
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
params = params.reindex(["Intercept", "bear", "mkt_rf", "bear:mkt_rf", "bear:up:mkt_rf"])
# print(params)

tvals = tvals.reindex(["Intercept", "bear", "mkt_rf", "bear:mkt_rf", "bear:up:mkt_rf"])
# print(tvals)

rows = {}
for var in params.index:
    rows[var] = params.loc[var].map(lambda x: f"{x:.3f}" if pd.notna(x) else "")
    rows[f"t_{var}"] = tvals.loc[var].map(lambda x: f"({x:.1f})" if pd.notna(x) else "")
rows["R2"] = pd.Series(r2).map(lambda x: f"{x:.3f}" if pd.notna(x) else "")

table3 = pd.DataFrame(rows).T
print(table3)

# Display labels for LaTeX
row_labels = {
    "Intercept"        : r"$\hat\alpha_0$",
    "t_Intercept"      : r"",
    "bear"             : r"$\hat\alpha_B$",
    "t_bear"           : r"",
    "mkt_rf"           : r"$\hat\beta_0$",
    "t_mkt_rf"         : r"",
    "bear:mkt_rf"      : r"$\hat\beta_{B}$",
    "t_bear:mkt_rf"    : r"",
    "bear:up:mkt_rf"   : r"$\hat\beta_{B,U}$",
    "t_bear:up:mkt_rf" : r"",
    "R2"               : r"$R^2_{\text{adj}}$",
}

var_labels = {
    "Intercept"      : r"$1$",
    "bear"           : r"$I_{B,t-1}$",
    "mkt_rf"         : r"$\tilde{R}^e_{m,t}$",
    "bear:mkt_rf"    : r"$I_{B,t-1}\tilde{R}^e_{m,t}$",
    "bear:up:mkt_rf" : r"$I_{B,t-1}I_{U,t}\tilde{R}^e_{m,t}$",
}
table3.insert(0, "Variable", table3.index.map(lambda r: var_labels.get(r, "")))

table3_tex = (table3.rename(index=row_labels)
              .rename_axis(columns="Coefficient"))
table3_tex.to_latex(TABLES / "table3.tex", column_format="lcccccccccccc")



# Table 4: Momentum portfolio optionality
deciles = [f"d{i}" for i in range(1, 11)]
y = monthly[deciles].sub(monthly["rf"], axis=0) 
y["WML"] = monthly["wml"]


data = y.join(monthly[["mkt_rf", "bear", "bull", "up"]])

def panel(ind):
    params, tvals = {}, {}
    for col in y.columns:
        formula = f"{col} ~ {ind} + mkt_rf + {ind}:mkt_rf + {ind}:up:mkt_rf"
        res = smf.ols(formula, data=data).fit()
        params[col] = res.params
        tvals[col] = res.tvalues
    params, tvals = pd.DataFrame(params), pd.DataFrame(tvals)
    params.loc[["Intercept", ind]] *= 100
    
    order = ["Intercept", ind, "mkt_rf", f"{ind}:mkt_rf", f"{ind}:up:mkt_rf"]
    params = params.reindex(order)
    tvals = tvals.reindex(order)

    rows = {}
    for var in params.index:
        rows[var] = params.loc[var].map(lambda x: f"{x:.3f}" if pd.notna(x) else "")
        rows[f"t_{var}"] = tvals.loc[var].map(lambda x: f"({x:.1f})" if pd.notna(x) else "")
    table4 = pd.DataFrame(rows).T

    s = "B" if ind == "bear" else "L"
    row_labels = {
        "Intercept"          : r"$\hat\alpha_0$",
        ind                  : rf"$\hat\alpha_{s}$",
        "mkt_rf"             : r"$\hat\beta_0$",
        f"{ind}:mkt_rf"      : rf"$\hat\beta_{s}$",
        f"{ind}:up:mkt_rf"   : rf"$\hat\beta_{{{s},U}}$",
    }

    table4 = table4.rename(index=lambda r: row_labels.get(r, ""))
    return table4

col_labels = {f"d{i}": f"$d_{{{i}}}$" for i in range(1, 11)}

panel_a = panel("bear")
panel_b = panel("bull")

def header(text):
    """A row with the panel title and empty cells."""
    return pd.DataFrame([[""] * len(panel_a.columns)], index=[rf"\textit{{{text}}}"],
                        columns=panel_a.columns)

table4 = pd.concat([header("Panel A: Optionality in bear markets"), panel_a,
                    header("Panel B: Optionality in bull markets"), panel_b])
table4 = (table4.rename(columns=col_labels)
                .rename_axis(columns="Coefficient"))
tex = table4.to_latex(column_format="l" + "c" * 11)

# Horizontal lines around the panel titles
for title in ["Panel A", "Panel B"]:
    start = tex.index(rf"\textit{{{title}")
    end = tex.index("\n", start) + 1
    line = tex[start:end]
    # Let the title span all columns so it does not widen the first column
    text = line.split("&")[0].strip()
    title_row = rf"\multicolumn{{12}}{{l}}{{{text}}} \\" + "\n"
    new = title_row + "\\midrule\n" if title == "Panel A" else "\\midrule\n" + title_row + "\\midrule\n"
    tex = tex.replace(line, new)

(TABLES / "table4.tex").write_text(tex)
