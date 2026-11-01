"""Build a separately versioned teaching/claims layer from unchanged saved outputs."""
from pathlib import Path
import hashlib, json

ROOT = Path(__file__).resolve().parents[1]
PARENT = '4b63a4eef4770644f07f41375529d7123116a72ce633799510dccac397fbc0c4'

def build():
    public = ROOT/'web/public/data/fdi'
    b = json.loads((public/'observatory.json').read_text(encoding='utf8'))
    t = json.loads((public/'temporal.json').read_text(encoding='utf8'))
    assert b['identity'] == t['parent'] == PARENT
    m = b['national']
    papers = json.loads((ROOT/'research/fdi/causal-literature.json').read_text(encoding='utf8'))
    applications = [
        'LP and VAR can target the same population response. Agreement is not independent causal identification; finite lag choices matter.',
        'Lag-augmented LP inference needs its own conditions. The published baseline HAC/VAR-bootstrap implementation is not automatically this procedure.',
        'Compare finite-sample bias, variance and coverage across several data-generating processes, rather than treating LP as universally superior.',
        'Use cohort-time treatment effects and eligible comparisons when opening dates differ. This is the primary municipal design, not an estimated result yet.',
        'Doubly robust means consistency if one of two nuisance models is correct under the design assumptions. It does not remove unobserved confounding or guarantee inference.',
        'Avoid a naive common-effect, two-way fixed-effects event study: heterogeneous effects can contaminate leads and lags.',
        'A non-significant pretrend can reflect low power. Do not select the reported specification because it passes a pretest.',
        'Assess how conclusions change under bounded departures from parallel trends. A validated Python sensitivity implementation remains pending.',
        'US worker–firm evidence motivates direct and indirect channels. Its estimates are not Brazilian effects or a calibration for our municipalities.',
        'Costa Rican supplier-link evidence motivates supply-chain mechanisms. Evaluate its identification separately; do not transplant its coefficients or comparison design.'
    ]
    for p, application in zip(papers, applications): p['application'] = application
    books = [
        {'title':'The Book of Why: The New Science of Cause and Effect', 'authors':'Judea Pearl and Dana Mackenzie', 'edition':'First edition, Basic Books, 2018', 'sections':'Chapter 1 (PDF pp. 34–37); Chapter 4 (PDF pp. 143, 148–152). PDF pagination refers to the inspected reflowed copy, not print pages.', 'application':'Distinguish seeing from doing and counterfactual questions. Draw common causes, mediators and colliders before choosing controls. The diagram expresses assumptions; it does not verify them.', 'url':'https://www.hachettebookgroup.com/titles/judea-pearl/the-book-of-why/9780465097616/'},
        {'title':'Statistical Models: Theory and Practice', 'authors':'David A. Freedman', 'edition':'Revised edition, Cambridge University Press, 2009', 'sections':'Chapter 1, pp. 1–14; Chapter 6, pp. 81–87; Chapter 8, pp. 155–156.', 'application':'Ask whether a fitted relationship would remain stable under an intervention. Report the economic size of a one-standard-deviation shock. Distinguish 2,000 simulated bootstrap draws from 119 observed quarters.', 'url':'https://www.cambridge.org/9780521112437'},
        {'title':'A Guide to Modern Econometrics', 'authors':'Marno Verbeek', 'edition':'Fifth edition, Wiley, 2017', 'sections':'Section 2.5.7, pp. 30–31; Section 5.2.4, p. 148; Section 9.2, p. 363.', 'application':'Explain p-values and power, reverse causality and the predictive meaning of Granger tests. A small p-value or an ability to predict does not itself establish an intervention effect.', 'url':'https://www.wiley.com/en-us/A+Guide+to+Modern+Econometrics%2C+5th+Edition-p-9781119401155'}
    ]
    def response(shock, outcome):
        return {'horizon':4,'estimate':m['irf'][4][outcome][shock], 'lower':m['irf_intervals']['0.025'][4][outcome][shock], 'upper':m['irf_intervals']['0.975'][4][outcome][shock], 'unit':m['units'][outcome], 'impact':m['impact_matrix'][shock][shock]}
    robustness=json.loads((public/'robustness.json').read_text(encoding='utf8'))
    assert robustness['parent']==PARENT and robustness['state']=='complete'
    sources={name:hashlib.sha256((public/name).read_bytes()).hexdigest() for name in ['observatory.json','temporal.json','robustness.json']}
    out={'schema_version':1,'version':'2026-11-01-transparency-2','parent':PARENT,'source_sha256':sources,'robustness_identity':robustness['identity'],
         'hypothesis_status':'Retrospective explanation of completed analyses; not a claim of preregistration. The new checks were specified before their execution, after the original baseline had been observed.',
         'gdp_response_to_fdi':response(4,1),'fdi_response_to_us_conditions':response(0,4),
         'papers':papers,'books':books,'origin_comparison':{basis:sorted([r for r in b['origins'] if r['year']==2025 and r['basis']==basis and r['country']],key=lambda r:-r['value_usd'])[:3] for basis in ['immediate','ultimate']},
         'supersession':{'frozen_specification':'The original study archive is preserved. Its unexecuted R municipal plan and unrecovered-poster wording are historical metadata, not the active implementation or current evidence.', 'legacy_eligibility_flag':'The frozen national causal_release_eligible flag records the original diagnostic gate, not certification of economic identification. The active public claim remains conditional on explicit restrictions.', 'publication_policy':'The frozen original release-policy wording is historical. The available-data website is authorized for release; the LinkedIn article remains an unpublished draft.', 'active_municipal':'Python ModernDiD 0.4.0 / Callaway–Sant’Anna doubly robust design; no empirical municipal ATT has been estimated.', 'poster':'The original PUC-SP poster is recovered. The original underlying data, code and full manuscripts remain unrecovered.', 'fevd':'The reviewed public FEVD already uses responses 0 through h−1 for an h-quarter forecast. The native archive summary is retained unchanged; do not export it directly as the reviewed series.', 'robustness':'Additional Python robustness notebook is prepared, not a completed sensitivity or Monte Carlo study.'}}
    out['supersession']['robustness']='Four additional CPU Python stages are now complete in separate run '+robustness['run_identity'][:16]+': residual diagnostics, lag-augmented LP sensitivity, saved-draw conversions and 8,000 synthetic replications. The original results are preserved. Conditional HAC and high-dimensional diagnostic limitations remain; synthetic undercoverage is a warning, not validation of Brazilian causal effects. The downloadable clean notebook remains a reproducibility template, distinct from the private executed history.'
    out['identity']=hashlib.sha256(json.dumps(out,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    target=public/'transparency.json';target.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
    assert json.loads(target.read_text(encoding='utf8'))==out
    print(out['identity'])

if __name__=='__main__':build()
