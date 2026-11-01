# Brazil FDI Observatory design QA

**Final result: passed**

This result covers the visual and interaction review of the implemented views
using available observations and completed national estimates. It does not mean
the municipal causal study or the entire research plan is complete.

## Visual truth and evidence

Selected source: `../../output/brazil-fdi-observatory-20261031/mockups/01-global-first-atlas.png`.
Source pixels: 1487 × 1058. Desktop CSS viewport requested: 1487 × 1058;
captured content: 1472 × 1047. The source was normalized to the captured content
size for the final comparison; browser chrome was excluded. Mobile CSS target:
390 × 844, with native browser capture scaling recorded in the PNGs.

Implementation: local `#/fdi/overview`, year 2025, Brazil, inward FDI/GDP.
Full comparison: `../../output/brazil-fdi-observatory-20261031/qa/comparison-final-verified.png`.
Focused typography/controls comparison:
`../../output/brazil-fdi-observatory-20261031/qa/comparison-header-final.png`.
Rendered desktop: `../../output/brazil-fdi-observatory-20261031/qa/desktop-final-verified.png`.
Rendered mobile: `../../output/brazil-fdi-observatory-20261031/qa/mobile-overview-final.png`.
Model and causal-diagram evidence: `desktop-irf-verified.png`,
`mobile-models-final.png`, `mobile-causal-dag-final.png` in the same QA folder.

## Findings and iteration history

- P2, first comparison: spurious map legend symbols and excess chart density.
  Removed automatic legend symbols and reduced above-the-fold content.
  Evidence: `comparison-first.png` → `comparison-revised.png`.
- P2, responsive map: forcing all geographic edges distorted mobile geography.
  Replaced stretching with geographic aspect preservation and bounded map size.
  The first correction made the desktop world too small; a second enlargement
  clipped high latitudes. Final sizing constrains width and height together.
  Evidence: `mobile-revised.png`, `comparison-final.png`,
  `desktop-map-fixed.png`, then `desktop-final-verified.png` and
  `mobile-overview-final.png`. Full geography and numeric legend categories are
  visible in the final captures.
- P2, small responses: one-decimal tick formatting produced duplicate labels.
  Added magnitude-aware precision and a regression test. The actual downloaded
  SVG contains distinct small-response labels.
- P2, mobile causal diagrams: white labels and view-box stretching made nodes
  unreadable. Kept node aspect ratios, moved dark labels below nodes and wrapped
  edge labels narrowly. Final mobile captures show the full causal labels.
- P2, uncertainty/export consistency: added LP 68%/95% bands, matched legend
  colors to shading, and included plotted intervals, historical components and
  the baseline robustness estimate in their CSV data.

## Required fidelity surfaces

Typography: Georgia display headings and Segoe UI/Arial interface text preserve
the selected economic-atlas hierarchy. Desktop display type was enlarged;
selectors use readable 14px text. Mobile headings wrap without hiding controls.

Spacing: fixed desktop navigation, a large map beside a ranking, then the
investment trajectory. Mobile navigation collapses and closes on selection;
maps, controls and accessible tables remain inside the viewport.

Tokens: restrained navy `#081b41`, teal `#167c80`, light gray boundaries and
diverging purple for negative flows. Missing observations remain gray.

Assets: maps use real Natural Earth/IBGE boundaries rather than the illustrative
mockup geography. The existing typographic author identity and icon library are
retained. Publication PNG/SVG figures were rendered from reviewed actual data
and visually inspected.

Content: illustrative mockup amounts/rankings were replaced by official source
observations. Additional source captions, CSV/SVG controls and data tables are
intentional. Municipal effects are explicitly unavailable, never illustrated
with generated estimates.

## Interaction and verification

Tested desktop/mobile navigation; ownership attribution; investor-country
filtering of published joint cells; maximum-four peer controls; municipal search
and accessible three-city comparison; selected-year deep links; the missing 2023
population state; national response/decomposition views; source disclosures;
and the Financial Intelligence workspace switch.

Actual browser downloads were independently read back: the notebook was
byte-identical, response CSV contained all 13 horizons/seven fields matching the
saved model to 1e-12, and SVG contained the expected uncertainty/axis labels.

Fresh-page console review found no runtime errors or warnings. Earlier React
Fast Refresh warnings followed a development-time dependency-array edit and did
not recur after a clean reload. Production TypeScript/Vite build passed; the
lazy FDI chart chunk retains a nonblocking size warning.

## Remaining research and implementation scope

Verified first-opening/comparison histories and harmonized RAIS outcomes remain
missing. Municipal event-study results and a treatment/comparison map cannot be
released. The remaining bilateral-flow mode, expanded sector-history view and
full coverage-status taxonomy are tracked separately from this visual QA pass.
No deployment or article publication occurred.

P3 follow-up: further chunk splitting and typographic refinement of long mobile
diagram labels. No actionable P0/P1/P2 visual findings remain in the reviewed
available-data views.

## 31 October requested additions

Negative-flow note visually checked beneath C2 on desktop and390pxmobile, with BCB methodology link. The C1 time-series laboratory was checked with constant-dollar and IPCA-adjusted reais views,2010–2020filter, trendoffdeep link/reload, reset, descriptive context disclosure, actualSVG rendering and persistentCSV/SVGlinks. A desktop control-row overflow was corrected with wrapping; the mobile component legend now scrolls instead of overlapping the zoom slider. Mobile content width375within390viewport; chart343px. Evidence: temporal-desktop.png, temporal-mobile.png, temporal-controls-mobile.png, negative-flow-note-desktop.png and negative-flow-note-mobile.png in the task QA directory. No national/FI models were rerun. All33webtests/14Pythontests pass. Website publication specifically authorized after both additions; LinkedIn draft stays local.
