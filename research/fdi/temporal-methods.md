# Monetary comparisons and time-series analytics

Prepared and validated in the dedicated free-CPU Colab on 31 October 2026 (1 November UTC). No national estimation or Financial Intelligence inference was repeated.

## Questions and units

- **Current USD:** frozen WDI annual net inflows, unchanged from the reviewed observatory.
- **Constant 2025 USD:** current USD × annual 2025 US GDP implicit price deflator / the observation-year index. BEA annual series A191RD3A086NBEA via FRED, originally 2017=100. This is a US price basis, not PPP, a Brazilian domestic price index or a physical capital-volume measure.
- **Constant USD per resident:** the constant-dollar amount / observed WDI SP.POP.TOTL for the same country/year. No population extrapolation.
- **FDI/GDP:** the frozen WDI ratio. This compares economic scale; it is not dollar deflation.
- **Constant 2025 BRL, Brazil only:** sum across 12 months of BCB SGS22885 USD-million net inflows × 1,000,000 × SGS3698 monthly average BRL/USD × mean monthly IPCA in 2025 / monthly IPCA. IBGE SIDRA1737 variable2266, December1993=100. All 12 observations must exist for all inputs. Consumer prices are one purchasing-power perspective; IPCA is not an investment-goods deflator. Annual WDI and monthly BCB series keep separate vintages and need not coincide.

## Descriptive statistics

The three-year trailing mean and five-year sample standard deviation require consecutive complete annual windows. Their windows can extend before the displayed start year, as stated beside the charts. Dispersion is in level units, not financial-return volatility or an uncertainty band.

Annual changes are differences in the selected units (percentage points for FDI/GDP). Percent growth is omitted where net flows make its interpretation unsafe. Endpoint CAGR requires at least two years, every selected year observed and strictly positive; it is not an investment return. For GDP shares the summary instead reports the mean of observed years. Missing observations and negative flows remain visible.

The URL preserves monetary basis, start/end years, country and trend toggle. Each chart includes a data table and filtered CSV/SVG export. A separate pair of charts presents annual-mean BRL/USD and IPCA December/December inflation without a dual axis.

## Official sources

- [BEA/FRED annual GDP deflator](https://fred.stlouisfed.org/series/A191RD3A086NBEA).
- [IBGE IPCA table1737](https://sidra.ibge.gov.br/tabela/1737).
- [World Bank total population](https://data.worldbank.org/indicator/SP.POP.TOTL).
- [BCB SGS monthly net inward FDI](https://api.bcb.gov.br/dados/serie/bcdata.sgs.22885/dados?formato=json).
- [BCB SGS average BRL/USD](https://api.bcb.gov.br/dados/serie/bcdata.sgs.3698/dados?formato=json).
- [BCB Direct Investment Report2025](https://www.bcb.gov.br/content/publicacoes/relatorioidp/RelatoriaID2024/RID_2025.pdf), pp10,42–43: net debt repayments, reinvested losses/distributions and the distinction between transactions and positions.

Original responses, retrieval times, sizes and hashes are retained privately. Public temporal.json contains only prepared aggregates and source provenance, not raw employment records or private research archives.

## Execution evidence

Comparison identity: `a14c692bbac6643746bed5642204e0a19f1b634bd38f34c9d1e1d9a512dff5e8`.
Colab archive: 2,702,381bytes,13members (12payload records plus manifest).
SHA256: `57aeadef54460e503adc2fb0190bda750f7686bda6feabe0d8d6c79f1d720475`.
Drive copy was read back, independently downloaded, SHA/CRC/member-verified and all6,510rows independently reproduced locally to relative tolerance1e-12. All30Brazilian annual real-BRL observations have complete monthly inputs. This is descriptive preparation, not a new causal result.
