# Replication notes

Deviations from the paper, to be described in the report.

## General: data versions and standard errors

The momentum decile returns are the authors' own files (DM_data_2014_02), so
all WML and decile series are identical to those in the paper (e.g. the 15
worst WML months in Table 2 match exactly). The market return, risk-free rate,
SMB and HML come from the July 2013 version of Kenneth French's monthly
factors. The paper uses the CRSP value-weighted index for the market; the
current CRSP (CIZ) version of that index gives 186 bear months instead of 183
(the differing months 1940-07, 1941-05 and 1971-06 all have 24-month returns
close to zero), while French 2013 reproduces the paper's 183 bear, 618 up and
417 down months exactly. We therefore use French 2013 throughout. Remaining
small differences in market-based numbers (e.g. a mean excess market return of
7.6% vs. 7.7% p.a. in Table 1, and a final value of \$2,903 vs. \$2,943 for
the market in Figure 1) reflect this choice and later CRSP revisions. The
paper does not say which standard errors it uses; conventional OLS
$t$-statistics reproduce the reported ones in Tables 1, 3, 4, 5, 6 and B1, so
we report those.

## Table 3

All coefficients are within 0.01 of the paper except $\hat\alpha_B$ in
column 2 ($-2.099$ vs. $-2.040$) and column 3 ($0.511$ vs. $0.583$). The
bear-market intercept is the coefficient most sensitive to the exact market
series, because it is identified from only 183 months.

## Table 4

Panel A matches the paper closely for all eleven portfolios. In Panel B the
slope coefficients are close ($\hat\beta_{L,U}$ for WML is $-0.242$ in both),
but the split of the intercept between $\hat\alpha_0$ and $\hat\alpha_L$ is
not: for WML we obtain $-0.121$ and $2.510$ against $0.347$ and $2.029$. The
sum $\hat\alpha_0 + \hat\alpha_L$, i.e. the alpha in bull markets, does match
($2.389$ vs. $2.376$ for WML, $-1.382$ vs. $-1.395$ for decile 1). Moreover,
in the specification stated in the paper, $\hat\alpha_0$ in Panel B is the
alpha in bear markets, which the paper's own Table 3 puts at
$1.976 - 2.040 = -0.064$ for WML, close to our $-0.121$ and far from
$0.347$. We tried several alternative specifications (adding $I_{U,t}$ or
$I_{U,t}\tilde R^e_{m,t}$ as separate regressors) without reproducing the
reported Panel B intercepts, and conclude that Panel B was likely estimated
with a slightly different specification than the one written in the table
note. We report the specification as written.

## Table 5

All coefficients are within about 0.04 of the paper and the $t$-statistics
agree. The sample is 1927:07–2013:03 ($N = 1{,}029$) because the 126-day
variance window first fills in June 1927. The only sign difference is
$\hat\gamma_B$ in column 5 ($-0.022$ vs. $0.023$), where both estimates are
essentially zero ($t = 0.0$).

## Figure 3

The rolling 126-day loser beta becomes negative around 1950 (minimum about
$-0.20$). The paper's Panel B has a vertical axis starting at zero, so these
estimates are not visible there. Like the paper, our figure starts the
vertical axis at zero, so these few negative values are not shown either. This
only affects the display, not the estimates.

## Figure 4

Panel A (1927–1939) reproduces the paper: the ex post hedged portfolio is far
above the unhedged one, and the ex ante hedged portfolio does worse than
unhedged around the 1932 crash. In Panel B the ex ante hedged portfolio ends
above the unhedged one from around 1948, while in the paper it stays below
until about 1990. We tested hedging with a daily and a monthly updated beta,
with and without an intercept, with only the contemporaneous market return,
and with lag-by-lag hedging; none of these reproduces the paper's Panel B. The
42-day beta, estimated as the sum of eleven coefficients, is noisy and has a
negative mean in several decades, so the long-run performance of the ex ante
hedge is sensitive to small differences in the inputs. The qualitative point
of the figure, that ex post hedging greatly overstates what an investor could
achieve in real time, holds in both our panels. We also report a version with
a monthly updated hedge ratio as a robustness check.

## Variance-swap return (Appendix A.2)

The paper writes the discount factor as $D_t = (1 + r_{1m})^{20/252}$. A
discount factor must be below one, so we use the exponent $-20/252$, which
with French's daily risk-free rate equals $(1 + r_{f,t})^{-20}$. The effect
on the results is negligible.

## Table B1

The paper states a sample start of January 1927, but the panic variable
$I_{B\sigma^2}$ requires 126 days of daily returns and is first available in
July 1927, so $N = 1{,}029$ for the WML and SMB columns and $N = 1{,}026$ for
the HML-devil columns (which end in December 2012 as in the paper). Columns
1, 2, 5 and 6 match the paper closely. For columns 3, 4, 7 and 8 we use the
current vintage of the HML-devil factor from the AQR data library; AQR has
revised the series since 2013, so these columns deviate more (e.g. the
coefficient on $I_{B\sigma^2}$ for HML-d is $11.73$ vs. $9.32$), but all signs
and significance levels are the same.

## Table 6: WML on variance-swap returns

Our estimates of Table 6 are close to, but not identical with, those in the
paper. The intercepts and the coefficients on $I_{B\sigma^2}$ deviate by 2–4%
(e.g. $-56.32$ vs. $-58.62$ in column 1), the interaction with the market
return by up to 8% ($-0.56$ vs. $-0.52$), while the interaction with the
variance-swap return is identical ($-0.10$). The $t$-statistics agree to within
about $\pm 0.3\%$. Since the WML returns are the authors' own data, the
differences come from the explanatory variables. First, the 126-day market
variance is computed from the current vintage of Kenneth French's daily
factors, whereas the authors most likely used the CRSP value-weighted index as
of 2013; CRSP has revised its historical data since then. Second, the VIX and
S&P 500 series are current WRDS downloads, and VIX is missing on three trading
days (1991-03-01, 1997-01-31, 1997-11-26), which removes seven observations
from column 3. Third, the paper does not state over which sample the
normalizing constant $\bar v_B$ is computed. We compute it as the mean of
$\hat\sigma^2_{m,t-1}$ over bear-market days in the 1990–2013 regression
sample; using the full 1927–2013 sample instead lowers the $I_{B\sigma^2}$
coefficients by about 15% but leaves the $t$-statistics unchanged, since the
normalization only rescales the regressor. Finally, the variance-swap return
is divided by 10,000 so that it is measured in decimal variance units, which
matches the scale of the coefficients in the paper. The only sign difference
is the coefficient on $\tilde r_{vs,t}$ alone in column 3 ($0.01$ vs.
$-0.02$), and both estimates are insignificant ($t = 0.2$ vs. $-0.4$). All
conclusions of the paper are unchanged: WML earns about 30% per year outside
panic states, significantly less in panic states, its market beta falls
sharply in panic states, and it loads negatively on variance-swap returns only
in panic states.
