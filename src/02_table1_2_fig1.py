from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "processed"
TABLES = ROOT / "output" / "tables"
FIGURES = ROOT / "output" / "figures"

DAILY_FILE = PROCESSED / "daily.csv"
MONTHLY_FILE = PROCESSED / "monthly.csv"

monthly = pd.read_csv(MONTHLY_FILE, index_col="month")
daily = pd.read_csv(DAILY_FILE, index_col="date", parse_dates=["date"])


# Table 1: Creating a DataFrame for excess returns of all 10 momentum 
# decile portfolios, and adding WML and Market at the end
deciles = [f"d{i}" for i in range(1, 11)]
excess = monthly[deciles].sub(monthly["rf"], axis=0) 
excess["WML"], excess["Market"] = monthly["wml"], monthly["mkt_rf"]

mean = excess.mean() * 12 * 100 # % p.a
# print(mean)
sigma = excess.std() * 12 ** 0.5 * 100 # % p.a
# print(sigma)
SR = mean / sigma 
# print(SR)

# CAPM regression
X = sm.add_constant(monthly["mkt_rf"]) # Adding a column with only 1's (for alpha)
alpha, t_alpha, beta = {}, {}, {}

for col in excess.columns:
    res = sm.OLS(excess[col], X).fit()
    alpha[col] = res.params["const"] * 12 * 100   # % per år
    t_alpha[col] = res.tvalues["const"]
    beta[col] = res.params["mkt_rf"]

# Market regressed on itself: alpha = 0 and beta = 1 by construction
# (the t-statistic would only be numerical noise). Hence,
alpha["Market"], t_alpha["Market"], beta["Market"] = 0.0, 0.0, 1.0

# SK(m) and SK(d): skewness of monthly and daily log-returns (full period)
# Monthly:
log_returns_m =np.log1p(monthly[deciles])
log_returns_m["WML"] = np.log1p(monthly["wml"] + monthly["rf"])
log_returns_m["Market"] = np.log1p(monthly["mkt_rf"] + monthly["rf"])

# Daily:
log_returns_d =np.log1p(daily[deciles])
log_returns_d["WML"] = np.log1p(daily["wml"] + daily["rf"])
log_returns_d["Market"] = np.log1p(daily["mkt_rf"] + daily["rf"])

sk_m, sk_d = log_returns_m.skew(), log_returns_d.skew()

# Putting the above results in a DataFrame:
table1 = pd.DataFrame({
    "r - rf": mean, 
    "sigma": sigma,
    "Alpha": alpha,
    "t(Alpha)": t_alpha,
    "Beta" : beta,
    "SR": SR,
    "SK(m)": sk_m,
    "SK(d)" : sk_d    
    }).T

# The t-statistics in parentheses 
table1_fmt = table1.copy().astype(object)
table1_fmt.loc["t(Alpha)"] = table1.loc["t(Alpha)"].map(lambda x: f"({x:.2f})")

# Display labels for LaTeX
row_labels = {
    "r - rf":   r"$\overline{r - r_f}$",
    "sigma":    r"$\sigma$",
    "Alpha":    r"$\alpha$",
    "t(Alpha)": r"$t(\alpha)$",
    "Beta":     r"$\beta$",
}
col_labels = {f"d{i}": f"$d_{{{i}}}$" for i in range(1, 11)}

table1_tex = (table1_fmt
              .rename(index=row_labels, columns=col_labels)
              .rename_axis(columns="Return statistic"))
table1_tex.to_latex(TABLES / "table1.tex", float_format="%.2f", column_format="lcccccccccccc")


# Table 2: Rank of 15 worst monthly momentum returns for WML_t over the time
# 1927:01-2013:03 time period and tabulate the 2y market returns (Mkt-2y) 
# and the contemporaneous market return (Mkt_t)


worst = monthly.nsmallest(15, "wml")
table2 = worst[[ "wml", "mkt_24m", "mkt"]] * 100
table2 = table2.reset_index() 
table2.insert(0, "Rank", range(1, 16))

col_labels2 = {
    "month" : "Month", 
    "wml" : "WML$_t$", 
    "mkt_24m" : "MKT-2y", 
    "mkt" : "Mkt$_t$"
    }

table2_tex = (table2.rename(columns=col_labels2))

table2_tex.to_latex(TABLES / "table2.tex", float_format="%.2f", index=False, 
                    column_format="ccccc")



# Figure 1:

wealth = (1 + monthly[["rf", "mkt", "d1", "d10"]]).cumprod()
wealth.index = pd.to_datetime(wealth.index)
start = pd.DataFrame(1.0, index=[pd.Timestamp("1926-12-31")], columns=wealth.columns)
wealth = pd.concat([start, wealth])

fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(wealth.index, wealth["rf"], label="Risk-free", 
        linestyle = ":", linewidth = 0.6, color = "black")
ax.plot(wealth.index, wealth["mkt"], label="Market", 
        linestyle = "-.", linewidth = 0.6, color = "black")
ax.plot(wealth.index, wealth["d1"], label="Past losers", 
        linestyle = "-", linewidth = 0.6, color = "black")
ax.plot(wealth.index, wealth["d10"], label="Past winners",
        linestyle = "-", linewidth = 0.8, marker = "o", 
        markevery = 100, markersize = 4, color = "black")
ax.set_yscale("log")
ax.set_ylabel("Dollar value of investment")
last_value_d10 = wealth["d10"].iloc[-1]
ax.text(wealth.index[-1], last_value_d10, rf"${last_value_d10:,.0f}", va="center")
for col in ["rf", "mkt", "d1"]:
    last_value = wealth[col].iloc[-1]
    ax.text(wealth.index[-1], last_value, rf"${last_value:,.2f}", va="center")
ax.set_xlim(wealth.index[0], wealth.index[-1])
ax.legend()
fig.savefig(FIGURES / "figure1.pdf", bbox_inches="tight")
