"""Validate completed Colab outputs and export aggregate sensitivity evidence.

No estimator, acquisition, baseline bootstrap, or publication is invoked here.
The private archive includes per-replication evidence; the public bundle does not.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import io
import itertools
import json
import math
import zipfile

REPO = Path(__file__).resolve().parents[1]
BASELINE = {
    'models/national.json': 'eee06465aa0c4ee366e2476d1083902a4f3a3d1a7713d843e2ad239666a0cc82',
    'prepared/quarterly.csv': '10426ad1fef8fcec3a53ff94c1753d289de4faf908437b1ffc787ac3b0d56b8a',
}
PARENT = '4b63a4eef4770644f07f41375529d7123116a72ce633799510dccac397fbc0c4'
PACKAGES = {'numpy': '2.2.6', 'pandas': '2.2.3', 'scipy': '1.15.3', 'statsmodels': '0.14.5'}
STAGES = ('residuals', 'lp', 'saved-draws', 'simulation')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(raw):
    def invalid(value):
        raise ValueError('Non-finite JSON constant: ' + value)
    return json.loads(raw, parse_constant=invalid)


def read_archive(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        assert z.testzip() is None, 'Archive CRC failed'
        names = z.namelist()
        assert len(names) == len(set(names)), 'Duplicate archive member'
        for name in names:
            path = PurePosixPath(name)
            assert not path.is_absolute() and '..' not in path.parts and '\\' not in name
        manifest = load(z.read('file-manifest.json'))
        assert set(names) == set(manifest) | {'file-manifest.json'}
        members = {name: z.read(name) for name in manifest}
        for name, digest in manifest.items():
            assert sha(members[name]) == digest, 'Member hash mismatch: ' + name
    return members


def finite(value):
    if isinstance(value, dict):
        for item in value.values():
            finite(item)
    elif isinstance(value, list):
        for item in value:
            finite(item)
    elif isinstance(value, float):
        assert math.isfinite(value)


def shape(value, dimensions):
    assert isinstance(value, list) and len(value) == dimensions[0]
    if len(dimensions) > 1:
        for row in value:
            shape(row, dimensions[1:])
    else:
        assert all(isinstance(x, (int, float)) and math.isfinite(x) for x in value)


def validate_mc(members, simulation):
    expected = set(itertools.product((119, 240), (0., .5), (1, 2)))
    cells = simulation['cells']
    assert simulation['synthetic'] is True and len(cells) == 8
    assert {(c['n'], c['ma'], c['p']) for c in cells} == expected
    audited = 0
    for cell in cells:
        n, ma, p = cell['n'], cell['ma'], cell['p']
        assert cell['requested'] == 1000
        rows = []
        prefix = f'mc/n{n}-ma{ma}-p{p}/'
        assert {key for key in members if key.startswith(prefix)} == {
            prefix + f'{rep:05}.json' for rep in range(1000)
        }, 'Missing or extra replication'
        for rep in range(1000):
            checkpoint = load(members[prefix + f'{rep:05}.json'])
            result = checkpoint['result']
            assert checkpoint['sha256'] == sha(json.dumps(result, sort_keys=True).encode())
            finite(result)
            if 'failure' not in result:
                assert result['se'] > 0 and isinstance(result['covered'], bool)
                assert result['covered'] == (result['estimate'] - 1.96 * result['se'] <= result['truth'] <= result['estimate'] + 1.96 * result['se'])
                rows.append(result)
            audited += 1
        assert cell['valid'] == len(rows) and cell['failures'] == 1000 - len(rows)
        assert cell['valid'] + cell['failures'] == cell['requested']
        if rows:
            coverage = sum(r['covered'] for r in rows) / len(rows)
            bias = sum(r['estimate'] - r['truth'] for r in rows) / len(rows)
            se = math.sqrt(coverage * (1 - coverage) / len(rows))
            for actual, target in [(cell['conditional_coverage'], coverage), (cell['bias'], bias), (cell['mcse'], se)]:
                assert math.isclose(actual, target, abs_tol=1e-12, rel_tol=1e-10)
        else:
            assert all(cell[k] is None for k in ['conditional_coverage', 'bias', 'mcse'])
    assert audited == 8000
    return audited


def build(archive, baseline_dir):
    raw = Path(archive).read_bytes()
    members = read_archive(raw)
    plan = load(members['plan.json'])
    config = {key: value for key, value in plan.items() if key not in ['identity', 'observed_rows']}
    assert plan['identity'] == sha(json.dumps(config, sort_keys=True).encode())
    assert plan['baseline'] == BASELINE and plan['packages'] == PACKAGES
    assert plan['observed_rows'] == 119 and plan['horizons'] == list(range(13))
    assert plan['seed'] == 20261031 and plan['lp_extra_lags'] == [0, 1, 2]
    assert plan['simulation'] == {'fit_lags': [1, 2], 'ma': [0., .5], 'n': [119, 240], 'replications_per_cell': 1000}
    assert plan['code_sha256'] == sha(members['fdi_robustness.py']) == sha((REPO / 'scripts/fdi_robustness.py').read_bytes())
    for name, digest in plan['dependency_code'].items():
        assert sha((REPO / 'scripts/fdi' / name).read_bytes()) == digest
    for name, digest in BASELINE.items():
        assert sha((Path(baseline_dir) / name).read_bytes()) == digest
    original = load((Path(baseline_dir) / 'models/national.json').read_bytes())
    public_baseline = load((REPO / 'web/public/data/fdi/observatory.json').read_bytes())
    assert public_baseline['identity'] == PARENT
    stages = {}
    for name in STAGES:
        value = load(members[name + '.json'])
        status = load(members[name + '-status.json'])
        assert value['state'] == status['state'] == 'complete'
        assert status['sha256'] == sha(members[name + '.json'])
        finite(value)
        stages[name] = value
    residuals, lp, draws, simulation = [stages[key] for key in STAGES]
    variables = ['nfci', 'gdp_growth', 'gfcf_growth', 'reer_change', 'fdi_gdp']
    assert {r['variable'] for r in residuals['seasonal']} == set(variables)
    assert len(residuals['seasonal']) == 5 and len(residuals['serial']) == 10
    assert {(r['variable'], r['lag']) for r in residuals['serial']} == set(itertools.product(variables, [4, 8]))
    for row in residuals['seasonal'] + residuals['serial']:
        assert 0 <= row['p'] <= row['holm_p'] <= 1 and row['statistic'] >= 0
    assert [s['extra_lags'] for s in lp['specifications']] == [0, 1, 2]
    for spec in lp['specifications']:
        shape(spec['irf'], [13, 5, 5])
        shape(spec['pointwise_95_hac'], [13, 5, 5, 2])
        for horizon in spec['pointwise_95_hac']:
            assert all(ci[0] <= ci[1] for response in horizon for ci in response)
    difference = max(abs(a - b) for aa, bb in zip(lp['specifications'][0]['irf'], original['local_projections']['irf']) for ar, br in zip(aa, bb) for a, b in zip(ar, br))
    assert difference < 1e-10, 'Zero-extra-lag point estimates do not reproduce the saved LP'
    assert draws['saved_draws'] == 2000 and draws['new_draws'] == 0
    shape(draws['gdp_level_percent'], [13])
    for q in ['0.025', '0.975']:
        shape(draws['gdp_level_pointwise_95'][q], [13])
        shape(draws['unit_quantiles'][q], [13, 5])
    for h in range(13):
        target = 100 * math.expm1(sum(row[1][4] for row in original['irf'][:h + 1]) / 100)
        assert math.isclose(draws['gdp_level_percent'][h], target, abs_tol=1e-12)
    audited = validate_mc(members, simulation)
    launch = load(members['simulation-launch.json'])
    assert launch['source_unchanged'] == plan['code_sha256'] and launch['threads'] == 1
    result = {
        'schema_version': 1, 'state': 'complete', 'parent': PARENT,
        'run_identity': plan['identity'], 'observed_rows': 119,
        'baseline_hashes': BASELINE, 'packages': PACKAGES, 'code_sha256': plan['code_sha256'],
        'archive_sha256': sha(raw), 'completed_stages': list(STAGES),
        'baseline_bootstrap_rerun': False, 'new_baseline_draws': 0,
        'validation': {'archive_members': len(members), 'mc_checkpoints_reconciled': audited, 'baseline_lp_max_abs_difference': difference},
        'residuals': residuals, 'lp': lp, 'saved_draws': draws, 'simulation': simulation,
        'baseline': {'impact_fdi_pp': original['irf'][0][4][4], 'unit_gdp_growth': [row[1][4] / original['irf'][0][4][4] for row in original['irf']]},
        'interpretation': 'Completed sensitivity evidence, not new causal identification. Conditional HAC intervals omit generated-shock uncertainty; residual Wald tests are asymptotic and high-dimensional; Monte Carlo evidence is synthetic. Municipal effects remain unavailable.',
    }
    result['identity'] = sha(json.dumps(result, sort_keys=True, allow_nan=False).encode())
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--archive', type=Path, required=True)
    ap.add_argument('--baseline', type=Path, default=REPO / 'artifacts/local/fdi/runs/4b63a4eef4770644')
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    result = build(args.archive, args.baseline)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(json.dumps(result, sort_keys=True, indent=2, allow_nan=False).encode())
    assert load(args.output.read_bytes()) == result
    print(json.dumps({'identity': result['identity'], 'validated': result['validation'], 'stages': result['completed_stages']}))


if __name__ == '__main__':
    main()
