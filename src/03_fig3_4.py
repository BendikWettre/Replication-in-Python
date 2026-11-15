from pathlib import Path
import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.rolling import RollingOLS
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "processed"
FIGURES = ROOT / "output" / "figures"

DAILY_FILE = PROCESSED / "daily.csv"
daily = pd.read_csv(DAILY_FILE, index_col="date", parse_dates=["date"])


# Regression for figure 3

# Creating a DataFrame for the explanatory variables (1, mkt_rf_1,...,mkt_rf_{10})
X = pd.concat({f"lag{k}": daily["mkt_rf"].shift(k) for k in range(11)}, axis=1)
X = sm.add_constant(X) 

deciles = ["d1", "d10"]
excess_d1_d10 = daily[deciles].sub(daily["rf"], axis=0) 
beta = {}

for col in excess_d1_d10.columns:
    params = RollingOLS(excess_d1_d10[col], X, window=126).fit().params
    beta[col] = params.drop(columns="const").sum(axis=1, min_count = 11)
beta = pd.DataFrame(beta)


# Plots:
def plot_betas(ax, beta, start_day, end_day):
    """Plot loser and winner betas between start_day and end_day."""
    beta = beta.loc[start_day:end_day]
    ax.plot(beta.index, beta["d1"], label="Loser decile",
            linestyle="-", linewidth=0.6, color="black")
    ax.plot(beta.index, beta["d10"], label="Winner decile",
            linestyle=":", linewidth=0.8, color="black")
    ax.set_xlim(beta.index[0], beta.index[-1])
    ax.set_ylim(bottom=0)
    ax.set_ylabel("126-day (rolling) beta")
    ax.grid(linestyle=":", linewidth=0.5)
    return beta


# Figure 3: three non-overlapping subsamples
PANELS = [
    ("Panel A: 1927:06-1939:12", "1927-06", "1939-12", 2),
    ("Panel B: 1940:01-1999:12", "1940-01", "1999-12", 10),
    ("Panel C: 2000:01-2013:03", "2000-01", "2013-03", 2),
]

fig, axes = plt.subplots(3, 1, figsize=(8, 10))
for ax, (title, start_day, end_day, tick_years) in zip(axes, PANELS):
    plot_betas(ax, beta, start_day, end_day)
    ax.set_title(title, loc="left")
    ax.xaxis.set_major_locator(mdates.YearLocator(tick_years))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
axes[0].legend(loc="upper left")

fig.tight_layout()
fig.savefig(FIGURES / "figure3.pdf", bbox_inches="tight")




# Fig 4
Period_A = ("1927-06-01", "1939-12-30")
Period_B = ("1927-06-01", "2013-01-31")
WML, RF, MKT_RF = daily["wml"], daily["rf"], daily["mkt_rf"]

params_wml = RollingOLS(WML, X, window=42).fit().params
beta_wml = params_wml.drop(columns="const").sum(axis=1, min_count = 11)

unhedged = WML + RF
ex_post_hedged = WML - beta_wml.shift(-42) * MKT_RF + RF
ex_ante_hedged = WML - beta_wml.shift(1) * MKT_RF + RF

def plot_cumulative(ax, returns):
    wealth = (1 + returns).cumprod()
    start_day = wealth.index[0] - pd.Timedelta(days=1)
    start = pd.DataFrame(1.0, index=[start_day], columns=wealth.columns)
    wealth = pd.concat([start, wealth])

    ax.plot(wealth.index, wealth["Unhedged"], label="Unhedged",
            linestyle="-", linewidth=0.6, color="black")
    ax.plot(wealth.index, wealth["Ex post hedged"], label="Ex post hedged",
            linestyle=":", linewidth=0.6, color="black")
    ax.plot(wealth.index, wealth["Ex ante hedged"], label="Ex ante hedged",
            linestyle="--", dashes=(5, 4), linewidth=0.8, color="black")
    ax.set_xlim(wealth.index[0], wealth.index[-1])
    ax.set_yscale("log")
    ax.set_ylabel("Portfolio value")
    return wealth


def plot_figure4(hedge, filename):
    """Panel A (1927-1939) and Panel B (full sample) of Figure 4."""
    fig, (ax_a, ax_b) = plt.subplots(2, 1, figsize=(8, 10))

    plot_cumulative(ax_a, hedge.loc[Period_A[0]:Period_A[1]])
    ax_a.set_title("Panel A: Cumulative daily returns to momentum strategies, "
                   "1927:06-1939:12", loc="left")
    ax_a.xaxis.set_major_locator(mdates.YearLocator(2))
    ax_a.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax_a.legend(loc="upper left")

    plot_cumulative(ax_b, hedge.loc[Period_B[0]:Period_B[1]])
    ax_b.set_title("Panel B: Cumulative daily returns to momentum strategies, "
                   "1927:06-2013:01", loc="left")
    ax_b.xaxis.set_major_locator(mdates.YearLocator(10))
    ax_b.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax_b.legend(loc="upper left")

    fig.tight_layout()
    fig.savefig(FIGURES / filename, bbox_inches="tight")


# Hedge ratio updated every day
hedge = pd.DataFrame({"Unhedged": unhedged,
                      "Ex post hedged": ex_post_hedged,
                      "Ex ante hedged": ex_ante_hedged})
plot_figure4(hedge, "figure4.pdf")

# Hedge ratio updated monthly
month = daily.index.to_period("M")

# Ex ante: beta from the last 42 days before the month starts
beta_ante_m = beta_wml.groupby(month).last().shift(1)

# Ex post: beta from the first 42 days starting on the first day of the month
beta_post_m = beta_wml.shift(-41).groupby(month).first()

# Give every day the beta of its month
beta_ante_d = pd.Series(beta_ante_m.reindex(month).to_numpy(), index=daily.index)
beta_post_d = pd.Series(beta_post_m.reindex(month).to_numpy(), index=daily.index)

hedge_monthly = pd.DataFrame({"Unhedged": unhedged,
                              "Ex post hedged": WML - beta_post_d * MKT_RF + RF,
                              "Ex ante hedged": WML - beta_ante_d * MKT_RF + RF})
plot_figure4(hedge_monthly, "figure4_monthly_hedge.pdf")
