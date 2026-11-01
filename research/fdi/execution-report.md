# Brazil FDI Observatory execution report

Study date: 31 October 2026, São Paulo. Final verification continued into
1 November UTC. Overall implementation remains in progress; the completed
national study and available-data exports are validated.

## Completed with actual data

- Dedicated private free-CPU Colab notebook; no GPU, purchases or R model run.
- 196 frozen official source records; source/numeric validation passed with no
  reconciliation notes. 217 economies and 6,510 country-year rows include
  explicitly missing observations. There are 12,807 published country-sector
  cells, 27 states and 5,571 municipalities in current geographic metadata.
- National SVAR and identified-shock local projections: 119 comparable quarters,
  1996Q2–2025Q4; BIC lag 1; 2,000/2,000 valid bootstrap draws, zero rejected.
  Spectral radius 0.82104939; portmanteau p 0.06715543. Identification remains
  conditional on the frozen structural restrictions.
- Strict saved-result review reproduced the national coefficients, responses,
  HAC quantities, bootstrap quantiles and historical reconciliation. It derived
  the correct 1–12-step FEVD from saved responses without repeating bootstraps.
- Python ModernDiD 0.4.0 implements the primary staggered DR DiD design.
  The labeled 800-unit known-effect test recovered 1.80622 for an effect of 1.8,
  clustered SE 0.01145, and passed deterministic replay. This is estimator
  validation, not a Brazil finding.
- pySidraData 0.1.0 at commit
  `85a2b39c0cc5eec56d0a3605bbfa1d497899cc8e`, with sidrapy 0.1.4, retrieved real
  metadata/observations. Colab reprocessed the 111-response preserved IBGE cache:
  116,908 observed population values, 83 nonnumeric values retained as missing,
  over 21 published years. São Paulo 2025 matched across the package and official
  API. Population is not a working-age denominator or a municipal FDI measure.

## Durable evidence

National identity:
`4b63a4eef4770644f07f41375529d7123116a72ce633799510dccac397fbc0c4`.
National archive SHA256:
`98bf3b3bac8d3265416a07a764f2e46ab494f0a978cbb8750f0751f27ad6e4c0`.

Final reviewed Python archive: 34,580,928 bytes; 2,487 manifest members.
SHA256: `df6a2ceff0b5d416b72cbaa0cf497d8de620fad3d7b8796973735c871fed1103`.
The full archive is retained privately in the approved Drive project.
Independent local copy: `artifacts/local/fdi/backups/fdi-4b63a4eef4770644-reviewed-full-python.zip`.
CRC and every member hash passed. Strict import confirmed 2,259 immutable
national input/result members unchanged. Raw/full archives remain private.

Reviewed export identity:
`c10d6d98934426b664c224913c8bdb20f15730cee45c013485fe1e8ea2701834`.
Python extension SHA256:
`4d167b8b53a3820f19a98f95507461f3bda583bbdd8a2b58e90ec2e02ae7e9e1`.
Municipal audit identity:
`3a72531b13f5c645f35b43c38a4cae32f8288e4616de96be97c6791789e6687e`.

The cleaned 49-cell private notebook was replaced in place and read back
byte-identically. Template SHA256:
`9cf676280c411b5b460ac2e5e86c0001ac74fb54692d957f30fe658e0ad7c0fe`.
There are zero active Rscript cells. Executed notebook history was preserved
privately before replacement, SHA256
`096cefe9bb750be5084d5c0daa82516c5063430a70e9cd7dc27c8f69ceaa1b70`.

## Validation and presentation

Twelve Python model/storage/audit tests, 31 web tests, TypeScript and production
build passed. Desktop/mobile review and exact CSV/SVG/notebook downloads were
verified; see `design-qa.md`. All nine preserved Financial Intelligence data
artifacts match the original SHA256 baseline. No FI inference or LangSmith
experiment was run.

Three principal publication figures and an approximately 1,500-word LinkedIn
draft are prepared. The third figure shows the actual national response and
uncertainty; no municipal event-study figure was manufactured.

## Unfinished requirements

The municipal causal study is unavailable: verified first qualifying operational
opening histories, defensible comparison histories and a harmonized IBGE/RAIS
outcome panel are absent. BCB individual census records are confidential;
published aggregates and a short list of plant histories do not identify
never-treated municipalities. This is not evidence of a zero treatment effect.

The broader atlas still needs the planned bilateral-equity-flow mode, extended
sector-history presentation, employment/earnings layers with correct denominators,
and the expanded observed/provisional/suppressed/incompatible coverage taxonomy.
These remain implementation/source tasks, not completed features.

Website publication is now authorized after both requested chart additions pass validation. Deployment verification is recorded separately. The LinkedIn article remains a local draft; it has not been published or scheduled. Financial Intelligence results and source URLs remain intact.

## Requested chart additions and publication authorization

The user authorized website publication after both additions. A BCB-sourced persistent note explains negative reinvested earnings, net debt repayments and equity withdrawals beneath the component chart. The time-series laboratory directly below the trajectory adds five monetary/scale views, period selection, a three-year trend, guarded annualized change, annual differences, five-year dispersion, and separate FX/IPCA context charts.

A separately hashed Python stage actually ran in the CPU Colab. Its archive was read back in Drive, downloaded independently and verified by SHA256, CRC and every member; all6,510rows reproduced locally. See temporal-methods.md. The clean51-cell notebook was read back byte-identically (SHA2566cd4f89d69a1f17c7e45a676a98cec6dff3371f562b000d661010eb916f5ccb4); executed history remains private. Fourteen Python tests and33web tests passed; desktop/mobile controls, layouts and deep links were reviewed. Financial Intelligence's nine public files remain byte-identical.

The available-data website is the authorized release scope. The missing municipal identification evidence and remaining atlas features above remain explicitly unavailable/incomplete. The local LinkedIn article is excluded from this website release.
