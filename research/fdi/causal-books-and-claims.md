# Causal interpretation and transparency extension — 31 October 2026

This note supersedes the wording of historical metadata without changing the frozen national specification, coefficients, saved draws or original archive. It does not announce a newly completed causal study.

## Sources actually inspected

Relevant sections of these books were read from the researcher's private Drive library. Full copies and extracted text remain in ignored local storage. Public references are bibliographic; we do not redistribute the books.

- Pearl, Judea, and Dana Mackenzie (2018). *The Book of Why: The New Science of Cause and Effect*. First edition, Basic Books. Chapter 1 (inspected reflowed PDF pages 34–37) distinguishes observation, intervention and counterfactual queries. Chapter 4 (PDF pages 143 and 148–152) addresses confounding, back-door paths, mediators and collider conditioning. These PDF page numbers are not print page references.
- Freedman, David A. (2009). *Statistical Models: Theory and Practice*, revised edition, Cambridge University Press. Chapter 1 (pp. 1–14), Chapter 6 (pp. 81–87) and Chapter 8 (pp. 155–156). Applications here: response stability under interventions, interpretable shock units, and the distinction between real observations and bootstrap replicates.
- Verbeek, Marno (2017). *A Guide to Modern Econometrics*, fifth edition, Wiley. Section 2.5.7 (pp. 30–31), Section 5.2.4 (p. 148) and Section 9.2 (p. 363). Applications: p-values are not null probabilities; reverse causality; Granger prediction does not by itself establish an intervention effect.
- Facure, Matheus. *Causal Inference for the Brave and True*. Graphical Causal Models; Doubly Robust Estimation; The Difference-in-Differences Saga. Python teaching companion, alongside the specific modern DiD papers and estimator documentation.

The ten recent journal papers and their exact applications are in causal-literature.json and references-2020-onward.bib. This is a focused review, not an exhaustive systematic review.

## The claim boundary

1. Descriptive observations and accounting comparisons do not receive invented causal tests.
2. A national recursive response is conditional on the declared ordering, dynamic model, fixed US controls and resampling assumptions. FDI/GDP is an endogenous financial ratio, not an independently measured external dollar shock.
3. Contemporaneous zero responses implied by FDI-last ordering are restrictions, not findings.
4. The focal quarter-4 GDP-growth interval spans zero. That does not prove zero effect, and no exact bootstrap null-test p-value was computed. This focal example is retrospective, not a preregistered primary endpoint.
5. Local projections reuse baseline estimated shocks. Their bands were generated under the fitted VAR. Agreement is not separate identification or general misspecification robustness.
6. Municipal ATT remains unavailable. Missing exposure/comparison histories and harmonized outcomes are hard dependencies; simulations are not empirical substitutes.
7. The municipal target is an opening effect on eligible treated municipalities. It is not the return to every FDI dollar or the effect of foreignness isolated from opening a plant.
8. Conditional parallel trends, anticipation, overlap, spillovers and measurement comparability are assumptions to defend. Passing a pretrend test cannot prove them. No validated Python HonestDiD equivalent is claimed.
9. The reviewed public FEVD already uses horizons 0 through h−1. The native archive's summary is historical and must not bypass the reviewer.
10. The original PUC-SP poster is recovered. Original data, code and full manuscripts remain unrecovered. The contemporary study is not a replication.

## Measurement and inference

The browser now explains inflation adjustments, base/reference years versus comparison benchmarks, calendar seasonality, growth conventions, FX direction, denominator effects, missing/suppressed observations, signed net flows, ownership attribution, source vintages and geographic changes. It distinguishes accounting reconciliation, model diagnostics, effect uncertainty and causal identification. The ADF and KPSS nulls differ; KPSS p=0.10 is an upper reporting boundary. The portmanteau p≈0.067 does not reject at 5% but does at 10%. Neither threshold validates economic identification. All national bands are pointwise.

## Python robustness extension: prepared, not a completed empirical study

A separate private CPU notebook packages executable code for residual seasonal/dependence diagnostics, lag-augmented conditional-HAC LP comparisons, draw-wise fixed-unit normalization and cumulative growth conversion, plus a small repeated synthetic VAR/VARMA benchmark. Input/configuration/code/dependency hashes isolate new stages. Completed stages require hash-verified reuse; ZIP CRC and all member hashes are read back. The notebook defaults to no new check execution and does not start a baseline bootstrap or Financial Intelligence/LangSmith work.

The full synthetic battery, new empirical sensitivity results, municipal Monte Carlo validation, parallel-trends sensitivity implementation, new deflator variants and omitted-variable specifications have not been completed. In particular, the conditional HAC comparison does not propagate all generated-shock uncertainty or establish the cited uniform-inference result.

Test runs use synthetic data and validate code mechanics, deterministic seeds, input identity changes, gap rejection, baseline preservation and archive restoration. They are not a coverage claim. Preserve this distinction in articles, UI labels and release reports.

