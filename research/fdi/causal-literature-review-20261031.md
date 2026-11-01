# Brazil FDI Observatory: causal identification and literature audit

**Fernando Barbosa research programme · Review dated 31 October 2026**

## Executive assessment

The observatory is a reproducible descriptive and conditional structural-analysis platform. It does not yet identify the general causal effect of foreign investment on Brazilian development. Its national SVAR supplies responses under specified recursive restrictions; its local projections reuse those restrictions; its municipal causal design has not been estimated on Brazilian treatment/outcome data.

The route from a working “6/10” to a demanding “10/10” standard is stronger identification, calibrated uncertainty and a visible chain from sources to claims. The numbers are an editorial rubric, not a statistically measured quality score. No checklist can guarantee that observational causal assumptions are true. A very rigorous study may conclude that an effect remains unidentified.

**Scope.** I inspected the current preparation, restricted VAR, local-projection, bootstrap, export-review and Python municipal-estimation code; frozen native and public outputs; configuration and simulation checks; and the recovered PUC-SP poster. This is a targeted methodological review with ten selected peer-reviewed articles published in 2020–2024, not an exhaustive systematic review. Publisher/author records establish bibliographic details; abstracts and accessible methods establish the limited claims summarized below. It is not a claim that every appendix of every paper was independently replicated.

**No new empirical estimation was run.** The numerical audit below is algebra on saved impulse responses. No national bootstrap, Financial Intelligence inference, LangSmith experiment, website publication or LinkedIn publication was performed for this review.

## What actually ran, and what did not

- National sample: 119 quarterly observations, 1996Q2–2025Q4; 118 estimation rows at the selected one-quarter lag.
- BIC compared lags 1–4 on a common 115-row sample, then the selected model was refitted on its available sample.
- Endogenous order: US NFCI, Brazilian real GDP log growth, real GFCF log growth, REER log change, inward FDI/quarterly nominal GDP.
- Contemporaneous controls: US real GDP log growth, change in effective federal funds rate, and quarterly indicators.
- The NFCI equation excludes lagged Brazilian variables. Other equations include the full endogenous lag block.
- 2,000 residual-vector bootstrap draws completed, with no rejected draws in this run. The selected lag and exogenous path stay fixed, and the system and impact matrix are re-estimated within each draw.
- The saved stability radius is 0.82105. The implemented eight-quarter portmanteau test gives p=0.06716. ADF/KPSS checks pass the configured rule. These are specification diagnostics, not tests of economic identification.
- The displayed uncertainty bands are pointwise. They are not simultaneous bands for the whole response path.
- Municipal Callaway–Sant’Anna doubly robust DiD is a Python ModernDiD 0.4.0 design with a successful generated-data validation. Its Brazilian empirical status is **unavailable**.

### An important code-audit correction

The frozen native model summarizes FEVD with an off-by-one forecast horizon. However, the existing public export-review layer already corrects this using responses from impact through h−1. The public bundle’s maximum absolute difference from that standard formula is **0.0** in this audit. A dedicated test also checks the one-step case.

For the FDI equation, the native first labelled horizon attributes 96.1448% to the own shock; the standard one-step figure is 97.0739%, and the public export uses the corrected convention. This is a native/export provenance issue, **not a newly discovered error in the displayed public FEVD**. Future releases must preserve that correction and clearly identify the authoritative export.

## Ten priorities for review

### 1. Define the causal intervention before choosing variables

**Status: essential identification clarification.**

The national treatment-like variable is a net financial-flow ratio. It combines equity excluding reinvestment, reinvested earnings and intercompany debt. It is not a count of new plants or an externally assigned investment budget. Financial direct-investment relationships and operational establishment openings are different treatments.

The municipal estimand should remain the effect of a **first verified qualifying foreign-invested operational opening**, relative to its specified comparison path. That does not isolate “foreignness” relative to an otherwise identical domestic opening. It may include construction, infrastructure, tax incentives and supplier changes bundled with the project.

For each analysis, freeze a statement of population, treatment, comparison, outcome, horizon and assumptions. Separate greenfield openings, acquisitions and financial transactions where the data genuinely permit that distinction. Do not present an ATT per opening as a return per dollar.

The BCB’s accounting definitions support the distinction between equity, reinvested earnings and debt. Reinvestment may occur without a new cross-border cash transfer. [BCB Direct Investment Report](https://www.bcb.gov.br/content/publications/directinvestmentreport/2024/DIR_2025.pdf).

### 2. Defend the recursive SVAR restrictions economically

**Status: assumptions implemented; their economic credibility remains open.**

With FDI ordered last, an FDI innovation has zero impact on contemporaneous output, fixed investment and the exchange rate. Those zeros follow from the identification scheme, not from an empirical finding that those variables are unresponsive.

Quarterly financial decisions and exchange rates can adjust quickly. FDI may also anticipate future production or reflect earnings generated by current production. The residual labelled “FDI shock” need not be an exogenous supply of productive capital; it can contain omitted domestic shocks and measurement error.

Retain the baseline as a conditional scenario. Compare economically motivated alternative orders and sign/narrative restrictions, and report where conclusions depend on them. Ordering sensitivity assesses assumptions; it cannot choose the true order by goodness of fit. Sign restrictions also need justification and can leave effects set-identified.

An external-instrument design would require independently documented relevance and exclusion. A policy announcement, global shock or shift-share measure is a candidate research design, not an automatically valid instrument.

### 3. Reassess the US block, controls and omitted common causes

**Status: credible variable labels; insufficient identification by proxy alone.**

NFCI measures **US financial conditions**, not an observed global FDI supply shock. Its first position and exclusion of Brazilian lags implement a small-open-economy restriction; they do not establish that NFCI captures all common international shocks. [Chicago Fed definition](https://www.chicagofed.org/research/data/nfci/about).

Audit US output, US monetary policy, commodity prices/terms of trade, Chinese demand, Brazilian monetary policy and fiscal/institutional changes against a causal graph. SELIC and inflation are absent from the current national endogenous block. That is a reason to examine omitted channels, not to add every available series mechanically.

The existing IRFs keep the contemporaneous exogenous US controls’ path fixed. An NFCI response is therefore conditional on those controls, not necessarily the total response to an international financial disturbance that also changes US output and policy.

For every control, state whether it is a common cause, a proxy, a mediator, an outcome or part of a jointly determined system. A larger regression is not automatically better identified.

### 4. Audit the FDI/GDP denominator, FX conversion and transformations

**Status: preparation is explicit; interpretation needs sensitivity checks.**

The national series is constructed as:

\[
f_q=100\frac{\sum_{m\in q}F^{USD}_m e_m}{GDP^{BRL}_q},
\]

where monthly FDI and quarterly GDP use matching million-currency units and \(e_m\) is BRL per US dollar. Multiplying a monthly flow by a monthly average exchange rate is a transparent conversion convention, not transaction-level valuation.

Holding converted FDI constant,

\[
\frac{\partial f_q}{\partial GDP_q^{BRL}}
=-100\frac{F_q^{BRL}}{(GDP_q^{BRL})^2}.
\]

Thus, a fall in the denominator can raise the ratio without a rise in the numerator. Exchange-rate changes also alter the converted numerator. This does not invalidate the ratio; it changes what its innovations mean.

Audit alternative scale measures and component-specific flows where definitions are comparable. A lagged-GDP normalization changes the estimand and does not eliminate endogeneity. Signed flows must not be logged mechanically. Distinguish nominal transaction amounts, price-basis adjustments, positions and physical investment volume. Confirm BPM vintages, source revisions, seasonal treatment and REER direction.

### 5. Separate confounders, mediators, colliders and outcome composition

**Status: municipal DAG is a useful start, not proof that adjustment suffices.**

Let \(D\) be an opening, \(Y\) an outcome, \(C\) pretreatment conditions, \(U\) unobserved changing prospects and \(M\) a post-opening mechanism:

\[
C\to D,\quad C\to Y,\quad U\to D,\quad U\to Y,\quad D\to M\to Y.
\]

The existing baseline population, GDP per capita, industry share and employment intensity address observed differences. They do not close the path through \(U\). Subsidies, infrastructure plans or expected demand may influence both location choice and outcomes.

For a total opening effect, do not automatically control for post-opening jobs, investment or sector shares: these may mediate the effect. Conditioning on post-treatment selection can also induce bias. Pretreatment measurement alone does not prove that a variable is sufficient for adjustment.

An effect on GDP per capita is not labor productivity, average earnings are not household income, and a change in the average wage can reflect worker composition. Municipality-based jobs and resident working-age denominators describe different populations. Define both the geographic and population estimand before interpreting the ratio.

### 6. Establish first exposure, anticipation and genuine comparison histories

**Status: principal empirical gate; currently not satisfied.**

A short list of foreign plants does not identify untreated municipalities. Verify ownership, prior operations, acquisitions, construction and operational dates, multiple projects and left-censored exposure. “First in our list” is not necessarily first exposure.

With opening cohort \(g\), two-year anticipation and universal reference \(b=g-3\), five clean preperiods are event years −7 through −3. Years −2 and −1 must not be treated as clean pretrends. Construction or infrastructure effects may begin even earlier.

Require verified never-treated or not-yet-treated controls outside their own anticipation windows. Freeze rules before examining outcomes, test reasonable anticipation alternatives, and retain an event-source audit trail. For a five-year post window ending in 2023, a cohort cannot open later than 2018; every outcome requires its own actual coverage calculation.

Do not estimate the Brazilian causal panel until these histories and harmonized outcomes exist.

### 7. Keep heterogeneous cohort effects, support and aggregation explicit

**Status: appropriate estimator selected; empirical support still unknown.**

The relevant building block is:

\[
ATT(g,t)=E[Y_{it}(g)-Y_{it}(\infty)\mid G_i=g].
\]

Here, \(Y(g)\) denotes adoption at \(g\), and \(Y(\infty)\) no qualifying opening through the relevant horizon. Identification requires a defensible conditional untreated-trend comparison, not simply a statistically significant coefficient.

Avoid a naive staggered two-way fixed-effects coefficient when effects vary by cohort and event time. The existing Python cohort-time design is preferable, but its aggregation weights still need publication.

For the principal summary, explicitly choose:

\[
\theta_{1:5}=\sum_g w_g\left[\frac15\sum_{e=1}^{5}ATT(g,g+e)\right],
\qquad w_g\ge0,\quad\sum_gw_g=1.
\]

Equal-municipality, population and employment weights answer different questions. Balanced event windows also change which cohorts enter the target population. Report this change.

Show overlap distributions, covariate balance, weight concentration and \(ESS=(\sum_iw_i)^2/\sum_iw_i^2\). Numerical minimum-count rules are guardrails, not proofs of adequate support. Do not silently trim or clip the estimand into apparent success.

### 8. Replace pretrend “passes” with sensitivity analysis and model interference

**Status: design acknowledges the risks; formal sensitivity results are absent.**

A nonsignificant pretrend test does not establish parallel trends; low power and selection after pretesting matter. Report the full pretreatment path, uncertainty and the magnitude of deviations the design could detect. Do not search specifications until their pretrend tests pass. Roth (2022) and Rambachan–Roth (2023) directly inform this requirement.

A useful sensitivity representation is:

\[
\widehat\beta_e\approx\tau_e+\delta_e,
\]

where \(\delta_e\) represents departure from the untreated-trend comparison. Report robust sets under economically defensible restrictions on the evolution of \(\delta_e\), not only the special case \(\delta_e=0\).

Local spillovers also challenge the no-interference assumption. With exposure \(S_i=\sum_{j\ne i}w_{ij}D_j\), the relevant potential outcome may be \(Y_i(d_i,S_i)\). Neighboring municipalities may gain suppliers or lose workers. Compare predeclared exposure definitions, commuting/functional regions and verified neighbor exclusions. Excluding neighbors changes the estimand and cannot prove that remaining spillovers are zero.

Keep this work Python-only. Verify a maintained implementation or validate a transparent translation against published reference outputs; do not label an unverified approximation as an implemented sensitivity method.

### 9. Strengthen inference beyond the fitted VAR and a single simulated panel

**Status: important implementation/inference limitation confirmed by code inspection.**

The national bootstrap resamples entire residual vectors independently across time. This preserves contemporaneous cross-equation covariance but not general conditional heteroskedasticity or temporal dependence. It simulates from the fitted VAR with fixed lag and exogenous paths, then re-identifies shocks.

That is a coherent model-based procedure under its assumptions. It is not a general robustness guarantee. In particular, LP bootstrap bands generated under the fitted VAR may not be calibrated when the true dynamics depart from that VAR.

Compare theoretically justified lag-augmented LP inference and appropriately justified robust resampling, using the right score/dependence assumptions and generated-shock uncertainty. “Use HAC,” “use a wild bootstrap” or “use more draws” is not a complete inference design.

Run a separate Monte Carlo validation project with actual-sample-sized dynamic systems, omitted lags/VARMA behavior, volatility shifts, persistence and weak instruments if used. For municipal designs, include zero effects, heterogeneous effects, anticipation, selective timing, poor overlap and spillovers.

The current municipal generated-data check uses one seeded panel of 800 municipalities with a 1.8-unit effect and 199 bootstrap replications. It checks implementation and determinism; it does not estimate coverage across repeated datasets.

Measure bias, RMSE, rejection rates and interval coverage. With \(R=1{,}000\) independent Monte Carlo datasets and true coverage 0.95, coverage MC standard error is about \(0.0069\). This is a proposed validation scale, not a completed result.

### 10. Audit claims, decomposition provenance and the complete specification record

**Status: strong preservation infrastructure; transparency and claim discipline can improve now.**

Keep pointwise and simultaneous uncertainty separate. Predeclare primary response pairs and horizons rather than highlighting whichever of 25 shock-response pairs across 13 horizons looks compelling. Stability, stationarity and residual tests do not certify exogeneity.

The four-quarter GDP-growth response to the standardized FDI innovation is approximately −0.01134 percentage points, with pointwise 95% interval [−0.04024,+0.00502]. This does not establish zero effect, and it is not a GDP-level effect or a policy multiplier.

The FDI impact innovation is approximately 1.17793 percentage points of quarterly FDI/GDP. State that scale when interpreting the response. One-standard-deviation normalization is not an intervention of one dollar or one percent.

Retain the immutable native archive and reviewed export as separately identified objects. The native FEVD convention is corrected in the public layer and tested; a future bypass must fail validation. Historical decomposition identities do not prove that named shocks are causal explanations.

Some frozen specification text still names the unexecuted R municipal design; the active separately hashed design and public metadata use Python. Likewise, the recovered original poster supersedes blanket historical-artifact-unavailable text. Publish a versioned supersession registry rather than editing the frozen record to look as though plans never changed.

## The mathematics behind the causal claims

### A. Covariance fit does not uniquely identify structural shocks

Write the fitted reduced form as:

\[
z_t=c+\sum_{\ell=1}^{p}A_\ell z_{t-\ell}+\Gamma x_t+u_t,
\qquad E[u_tu_t']=\Sigma_u.
\]

Structural identification writes:

\[
u_t=B\varepsilon_t,\qquad E[\varepsilon_t\varepsilon_t']=I,
\qquad\Sigma_u=BB'.
\]

For an orthogonal matrix \(Q\), \(BQ(BQ)'=BB'\). Thus the same residual covariance admits different structural decompositions. Cholesky supplies one \(B\) by imposing a recursive structure. Statistical fit cannot select its causal interpretation on its own.

Our order is \(z=(NFCI,g^{GDP},g^{GFCF},\Delta\log REER,FDI/GDP)'\). With the fifth shock last, \(B_{1:4,5}=0\). The impact zero for GDP is therefore imposed.

The moving-average recursion is:

\[
\Phi_0=I,\qquad
\Phi_h=\sum_{\ell=1}^{\min(p,h)}A_\ell\Phi_{h-\ell},
\qquad IRF_j(h)=\Phi_hBe_j.
\]

These formulas propagate a structurally interpreted innovation while the specified exogenous path is held fixed. The interpretation is conditional on the model and restrictions.

An external instrument \(q_t\) would need, at minimum:

\[
E[q_t\varepsilon_{F,t}]\ne0,\qquad
E[q_t\varepsilon_{k,t}]=0\quad(k\ne F).
\]

The first is relevance; the second is exclusion/orthogonality to other structural disturbances. NFCI, commodity shocks and historical investment shares do not automatically satisfy them. Weak identification requires inference designed for weak instruments.

### B. Local projections change the dynamic approximation, not the identifying event

The implemented form is represented by:

\[
z_{j,t+h}=\alpha_{j,h}+\beta_{j,h}'\widehat\varepsilon_t
+\sum_{\ell=1}^{p}\Lambda_{j,h,\ell}z_{t-\ell}
+\Pi_{j,h}x_t+v_{j,t+h}.
\]

The shocks \(\widehat\varepsilon_t=\widehat B^{-1}\widehat u_t\) come from the same fitted system. They are generated regressors, not independently randomized treatments. Agreement with the SVAR is informative about dynamic approximations, not independent confirmation of exogeneity. The population-equivalence literature does not imply exact equality of short-lag finite-sample estimates.

### C. GDP growth and the GDP level are different response objects

If \(g_t=100\Delta\log Y_t\), a shock’s cumulative log-level response through \(H\) is:

\[
L_H=\sum_{h=0}^{H}IRF_g(h),
\qquad
\%\Delta Y_H=100\left[\exp(L_H/100)-1\right].
\]

Construct an interval for \(L_H\) using the cumulative response within each valid bootstrap draw. Summing pointwise lower and upper bounds is not a valid substitute because cross-horizon dependence matters.

### D. FEVD is a forecast-error partition under the identification

With orthogonal structural shocks and \(\Psi_s=\Phi_sB\):

\[
FEVD_{jk}(h)=
\frac{\sum_{s=0}^{h-1}(\Psi_s)_{jk}^{2}}
{\sum_{r=1}^{K}\sum_{s=0}^{h-1}(\Psi_s)_{jr}^{2}},
\qquad h\ge1.
\]

The sum over \(k\) equals one. This is a partition of model forecast uncertainty, not a welfare decomposition, share of economic “importance” or proof of the causal restrictions. The public export uses the formula above.

### E. What doubly robust DiD does and does not protect against

For a cohort-time comparison, restrict attention to cohort \(g\) and its eligible controls. Let \(D=1\) for cohort \(g\), \(b=g-3\), \(\Delta Y=Y_t-Y_b\), \(p(X)=P(D=1\mid X)\), and \(m_0(X)=E[\Delta Y\mid D=0,X]\).

Conditional parallel trends requires:

\[
E[Y_t(\infty)-Y_b(\infty)\mid G=g,X]
=E[Y_t(\infty)-Y_b(\infty)\mid C_{g,t}=1,X].
\]

With normalized weights:

\[
w_1=\frac{D}{E[D]},\qquad
w_0=\frac{(1-D)p(X)/(1-p(X))}
{E[(1-D)p(X)/(1-p(X))]},
\]

a panel DR building block is:

\[
\tau^{DR}_{g,t}
=E\left[(w_1-w_0)\{\Delta Y-m_0(X)\}\right].
\]

Under the identifying assumptions and regularity conditions, consistency can survive misspecification of one nuisance model if the other is correct. It cannot survive arbitrary unobserved trend differences, treatment misclassification, interference or lack of overlap. Robustness of consistency and robustness of inference are separate properties; generic machine-learning replacements require their own conditions and validation.

### F. Pointwise and simultaneous uncertainty

A pointwise statement concerns one fixed horizon:

\[
P\{\theta_h\in CI_h\}\approx0.95.
\]

A simultaneous band targets:

\[
P\{\theta_h\in CB_h\text{ for every }h\in\mathcal H\}\approx0.95.
\]

The second generally requires a larger critical value calibrated for the joint path. A max-statistic based on a valid joint resampling procedure is one approach. Changing the label on pointwise bands does not create simultaneous coverage.

For simulation validation:

\[
\widehat{Coverage}=\frac1R\sum_{r=1}^{R}
\mathbf1\{\theta_0\in CI_r\},\qquad
MCSE\approx\sqrt{\frac{\widehat C(1-\widehat C)}R}.
\]

The bootstrap replication count is not the number of independently generated Monte Carlo datasets. Neither quantity measures the truth of an identification assumption.

## Ten peer-reviewed articles to add to the research

Publication years below refer to journal publication, even where working-paper versions are older. These are eight methodology papers and two direct multinational-investment applications. US and Costa Rican treatment effects are not Brazilian estimates.

### 1. Plagborg-Møller and Wolf (2021)

**Local Projections and VARs Estimate the Same Impulse Responses. Econometrica 89(2), 955–980.** DOI: [10.3982/ECTA17813](https://doi.org/10.3982/ECTA17813). [Author-hosted published paper](https://economics.mit.edu/sites/default/files/publications/lp_var.pdf).

Why it belongs: separates identification from the choice of dynamic estimator. Our LP/SVAR comparison shares shocks and is not two independent causal designs. The equivalence result uses unrestricted lag structures; it must not be oversold as equality of our finite-sample one-lag estimates. Add to National Identification and Robustness.

### 2. Montiel Olea and Plagborg-Møller (2021)

**Local Projection Inference Is Simpler and More Robust Than You Think. Econometrica 89(4), 1789–1823.** DOI: [10.3982/ECTA18756](https://doi.org/10.3982/ECTA18756). [Author paper](https://joseluismontielolea.com/lp_inference_ecta.pdf).

Why it belongs: evaluates persistence and response-horizon inference using lag-augmented LPs. It motivates a precisely specified inference comparison, not a blanket claim that our current HAC or VAR-bootstrap intervals inherit its theorem. Its central marginal-inference result is not a simultaneous-band guarantee. Add to Statistical Inference.

### 3. Li, Plagborg-Møller and Wolf (2024)

**Local Projections vs. VARs: Lessons from Thousands of DGPs. Journal of Econometrics.** Article 105722. DOI: [10.1016/j.jeconom.2024.105722](https://doi.org/10.1016/j.jeconom.2024.105722). [Authors’ working-paper record](https://arxiv.org/abs/2104.00655).

Why it belongs: emphasizes finite-sample bias–variance trade-offs across many data-generating processes. It is the methodological benchmark for moving beyond our single favorable simulation. The study’s US-macro calibration is not automatic calibration for Brazil. Add to Estimator Validation and Finite-Sample Robustness.

### 4. Callaway and Sant’Anna (2021)

**Difference-in-Differences with Multiple Time Periods. Journal of Econometrics 225(2), 200–230.** DOI: [10.1016/j.jeconom.2020.12.001](https://doi.org/10.1016/j.jeconom.2020.12.001).

Why it belongs: provides cohort-time effects, conditional comparisons, aggregation and simultaneous inference for staggered treatment. It directly supports our chosen municipal estimand. The paper does not establish that our opening registry or control municipalities meet its assumptions. Add to Municipal Identification.

### 5. Sant’Anna and Zhao (2020)

**Doubly Robust Difference-in-Differences Estimators. Journal of Econometrics 219(1), 101–122.** DOI: [10.1016/j.jeconom.2020.06.003](https://doi.org/10.1016/j.jeconom.2020.06.003).

Why it belongs: explains what the outcome and propensity-score models protect against, and distinguishes robustness for consistency from inference. It prevents the erroneous claim that “doubly robust” means immune to unobserved confounding. Add to Estimation and Nuisance-Model Specification.

### 6. Sun and Abraham (2021)

**Estimating Dynamic Treatment Effects in Event Studies with Heterogeneous Treatment Effects. Journal of Econometrics 225(2), 175–199.** DOI: [10.1016/j.jeconom.2020.09.006](https://doi.org/10.1016/j.jeconom.2020.09.006).

Why it belongs: demonstrates contamination of conventional lead/lag TWFE event-study coefficients under heterogeneous timing effects. It motivates reporting supported cohort effects and transparent event-time aggregation rather than a naive fixed-effects event plot. Add to Heterogeneity and Event-Study Interpretation.

### 7. Roth (2022)

**Pretest with Caution: Event-Study Estimates after Testing for Parallel Trends. American Economic Review: Insights 4(3), 305–322.** DOI: [10.1257/aeri.20210236](https://doi.org/10.1257/aeri.20210236). [Publisher record](https://pubs.aeaweb.org/doi/10.1257/aeri.20210236).

Why it belongs: low power and selection after pretesting undermine “the pretrend test passed, therefore causality” reasoning. Keep design checks, but report sensitivity and avoid selective reporting conditional on p-values. Add to Pretreatment Diagnostics and Researcher Degrees of Freedom.

### 8. Rambachan and Roth (2023)

**A More Credible Approach to Parallel Trends. Review of Economic Studies 90(5), 2555–2591.** DOI: [10.1093/restud/rdad018](https://doi.org/10.1093/restud/rdad018). [Author-hosted published paper](https://www.jonathandroth.com/assets/files/HonestParallelTrends_Main.pdf).

Why it belongs: formalizes inference allowing bounded departures from parallel trends and makes identification uncertainty visible. Use economically motivated sensitivity restrictions, disclose their meaning and report breakdown of substantive conclusions. A software port must be verified before claiming implementation. Add to Sensitivity and Partial Identification.

### 9. Setzler and Tintelnot (2021)

**The Effects of Foreign Multinationals on Workers and Firms in the United States. Quarterly Journal of Economics 136(3), 1943–1991.** DOI: [10.1093/qje/qjab015](https://doi.org/10.1093/qje/qjab015). [NBER author manuscript](https://www.nber.org/system/files/working_papers/w26149/w26149.pdf).

Why it belongs: connects foreign ownership, linked employer–employee data, direct wage outcomes and local spillovers. It illustrates the microdata and identification architecture needed for a stronger local-effects chapter. Its US estimates cannot be transferred to Brazil or municipal GDP by analogy. Add to Mechanisms, Outcomes and External Validity.

### 10. Alfaro-Ureña, Manelici and Vasquez (2022)

**The Effects of Joining Multinational Supply Chains: New Evidence from Firm-to-Firm Linkages. Quarterly Journal of Economics 137(3), 1495–1552.** DOI: [10.1093/qje/qjac006](https://doi.org/10.1093/qje/qjac006). [Publisher record](https://academic.oup.com/qje/article/137/3/1495/6517334).

Why it belongs: uses Costa Rican firm-to-firm transaction data to study entry into multinational supply chains. It motivates measuring supplier relationships rather than assuming technology spillovers from aggregate inflows. Supplier selection and identifying comparisons still require critical assessment; neither a top journal nor a positive result removes assumptions. Add to Linkages and Mechanism Measurement.

### Supporting references that are not part of the ten-article count

- [Matheus Facure, Causal Inference for the Brave and True](https://matheusfacure.github.io/python-causality-handbook/landing-page.html): teaching structure for DAGs, adjustment, counterfactuals and doubly robust reasoning. It complements the primary econometrics papers; it does not certify this application.
- [Chicago Fed NFCI documentation](https://www.chicagofed.org/research/data/nfci/about): definition and scope of the US index.
- [BCB Direct Investment Report](https://www.bcb.gov.br/content/publications/directinvestmentreport/2024/DIR_2025.pdf): financial-account definitions, components, immediate/ultimate ownership and reinvestment.
- [BCB direct-investment ownership threshold](https://www.bcb.gov.br/en/pressdetail/2375/nota): the statistical relationship is not equivalent to a greenfield opening.

## A concrete route from “6/10” to a demanding research standard

### Stage 1 — Transparency and honest claims, achievable with saved evidence

1. Freeze a claim-to-evidence register: source, variable, transformation, estimand, identification assumption, output and limitation for every figure and sentence.
2. State “conditional recursive structural response” on national causal displays. Keep municipal estimates unavailable and distinguish an opening effect from foreignness and a dollar return.
3. Add the ten-paper bibliography and variable-role/DAG register to Research & Methods. Label this review and all new specification decisions as post-results.
4. Register the native FEVD convention and corrected export as an explicit versioned transformation. Preserve the original hashes and rerun the small algebraic guard, not model inference.
5. Reconcile active Python specifications, superseded R metadata and recovered poster status without rewriting historical archives.

Acceptance: a reader can trace every substantive claim to an output and an assumption; the public display never silently falls back to an unreviewed native summary.

### Stage 2 — A defensible national structural paper

1. Write the economic argument for each ordering/restriction and the fixed US-control path. Predeclare primary response pairs, horizons, cumulative GDP-level summaries and economically meaningful effect scales.
2. Plan a new, separately versioned inference study for lag uncertainty, dynamic misspecification, persistence and heteroskedasticity. Compare justified LP and VAR procedures and calibrated simultaneous bands.
3. Report pre-pandemic and break-sensitive analyses as different target populations/regimes, not interchangeable estimates. Model-selection sensitivity must not choose a preferred result by significance.
4. If an instrument is proposed, document its construction, timing, relevance and exclusion, and assess weak identification. Otherwise keep the recursive conclusion explicitly conditional.
5. Preserve all old outputs and label the new run identity. Existing bootstrap draws are reusable for compatible algebraic summaries; they cannot impersonate a different DGP, estimator or resampling design.

Acceptance: the method’s operating characteristics are demonstrated near the actual sample design, and the economic identifying assumptions are defendable and exposed.

### Stage 3 — A genuine Brazilian municipal causal study

1. Acquire auditable establishment histories, ownership, dates, prior exposure, comparison histories and harmonized IBGE/RAIS outcomes under lawful access. Published national aggregates and pySidraData cannot supply missing ownership/treatment histories.
2. Freeze treatment eligibility and outcome coverage before fitting results. Explain simultaneous policy packages, anticipation, interference, project versions and weighting.
3. Report overlap, selection/exclusions, pretrend power, sensitivity to trend violations, supported cohort effects and plausible spatial exposure designs.
4. Validate the pinned Python estimator over adverse repeated simulations and published/reference calculations. Theoretical guarantees of a method are not evidence that a particular implementation is correct.
5. Invite an independent methodological replication. If the treatment history or counterfactual remains indefensible, publish a descriptive atlas and identification gap instead of manufacturing a causal estimate.

Acceptance: another researcher can reconstruct the risk sets, explain the counterfactual and reproduce the estimates and their uncertainty without hidden manual choices.

### A transparent ten-point rubric

Allocate 0–2 points to each of five dimensions: (i) estimand and economic identification, (ii) measurement and source provenance, (iii) statistical inference and finite-sample validation, (iv) robustness and sensitivity, and (v) reproducibility and claim transparency. A score of two means independently auditable evidence in that dimension, not simply a written promise. Do not average away a fatal identification failure.

Transparency can become excellent immediately. Causal credibility may require new data and a different design; no amount of polish or extra model complexity substitutes for it.

## Suggested language for the article and methods page

“The national analysis estimates dynamic responses under a stated recursive identification scheme. The FDI innovation is an unexpected component of a net financial-flow-to-GDP ratio, conditional on the included variables and restrictions; it is not directly observed exogenous investment supply. Local projections reuse the identified innovations and assess dynamic-specification sensitivity rather than provide independent identification. Reported national bands are pointwise and model-dependent. Municipal treatment effects remain unavailable pending verified exposure histories and a credible comparison design.”

The current first article already avoids claiming a completed municipal effect. These proposed additions strengthen the methods disclosure; this review does not authorize publishing or scheduling the LinkedIn draft.
