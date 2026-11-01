# Official-source audit — 31 October 2026

The World Bank, Banco Central, IBGE, BIS and Federal Reserve inputs in the prepared archive are observed official-source series. Country flows, equity ownership positions, industrial state positions and municipal economic context are different measures.

## Municipal identification evidence

Banco Central's [census manual](https://bcb.gov.br/content/estabilidadefinanceira/cambiocapitais/Manual_CENSO.pdf), section 1.3, explains that public census statistics are aggregated and individual information remains confidential. Its [2018 investment report](https://www.bcb.gov.br/content/publicacoes/relatorioidp/RelatorioID2016/RelatorioIDP2016.pdf) explains the allocation of industrial investment positions by fixed-asset location. These sources do not provide an open annual register of first operational openings and untreated municipal histories.

Primary-source opening histories found:

- [Hyundai's Brazilian history](https://www.hyundai.com.br/a-hyundai.html/): production at Piracicaba began in September 2012. The later inauguration ceremony must not replace that operational date.
- [BMW Araquari's timeline](https://www.bmwgroup-werke.com/araquari/en/timeline.html): logistics and assembly production began in September 2014; construction and announcement dates are separate events.
- [Toyota's own foundation](https://fundacaotoyotadobrasil.org.br/toyota-do-brasil-apresenta-relatorio-de-sustentabilidade-com-destaque-para-lancamento-do-etios-primeiro-compacto-da-empresa-no-pais/) describes an operating Sorocaba plant inaugurated in August 2012. Its [unit inventory](https://www.toyotacomunica.com.br/companhia/unidades/) provides corroborating location and production information.

These are candidate case-study records, not an exhaustive treatment registry. No municipality is classified as never treated simply because it is absent from this list. Historical foreign ownership, earlier qualifying openings, incentives, anticipation and supplier spillovers still require audit. No municipal causal estimate is released on these examples alone.

## Outcome sources

- IBGE table 5938 supplies municipal GDP and sector GVA, with actual sector gaps in 2022–2023. Revised GDP per capita indicator 47001 has its own coverage and must not be silently joined to an incompatible vintage.
- [MTE's microdata portal](https://www.gov.br/trabalho-e-emprego/pt-br/assuntos/estatisticas-trabalho/microdados-rais-e-caged) is the source for RAIS employment and earnings. A harmonized municipal panel has not yet been verified. CAGED admissions wages are not a substitute for average earnings of the employed stock.
- [Ministry of Health population sources](https://www.gov.br/saude/pt-br/composicao/seidigi/demas/dados-populacionais/dados-populacionais) identify municipal age/sex estimates. Working-age denominators require matching reference dates and boundary vintages.
- IPEA's documented [API](https://www.ipeadata.gov.br/api/) metadata inventory was downloaded and checksummed. No metadata record explicitly referencing RAIS was found; no guessed series identifier was used.

## Causal workflow

The user specifically requested Matheus Facure's [Causal Inference for the Brave and True](https://matheusfacure.github.io/python-causality-handbook/landing-page.html) in both analytics and models. Chapters 4, 12 and 24 guide the graphical assumptions, nuisance-model checks and staggered-treatment design in `causal-design.json`. The primary municipal estimator remains Callaway–Sant’Anna DR DiD. Its causal interpretation needs substantive identification evidence; predictive fit, a named estimator and a non-significant pretrend test are insufficient.

Status: national computation completed and independently backed up; municipal empirical identification remains blocked by the audited data prerequisites. No public release is authorized.
# Python data-access extension, verified 31 October 2026

The author's **pySidraData 0.1.0**, pinned to commit
`85a2b39c0cc5eec56d0a3605bbfa1d497899cc8e`, was inspected and installed in
isolated environments. Its Client retrieved SIDRA metadata and an actual São Paulo
2025 population observation. Table 6579, variable 9324 matches the preserved
official API response. There are 116,908 observed municipal population values
over 21 published years within 2001–2025. Eighty-three nonnumeric observations
remain missing; 2007, 2010, 2022 and 2023 are not filled from adjacent years.
The raw 111 responses and their retrieval/hash manifest were saved locally,
uploaded into the approved private Drive folder, CRC/member-hash checked and
reprocessed on Colab CPU. Original raw source hashes matched after transfer.

BCB FDI, IBGE economic outcomes and resident population retain distinct source
definitions. Population is neither working-age population nor municipal FDI.
The library supplies data access, not a causal treatment registry.
