"""Adversarial provenance checks; these do not simulate or fit any model."""
import hashlib
import io
import itertools
import json
import unittest
import zipfile
from build_fdi_robustness_export import load, read_archive, validate_mc


def archive(name, data, digest=None):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as z:
        z.writestr(name, data)
        z.writestr('file-manifest.json', json.dumps({name: digest or hashlib.sha256(data).hexdigest()}))
    return out.getvalue()


class ExportAudit(unittest.TestCase):
    def test_crc_valid_archive_with_changed_member_is_rejected(self):
        with self.assertRaises(AssertionError):
            read_archive(archive('result.json', b'{"estimate":99}', '0' * 64))

    def test_path_escape_rejected_even_with_a_matching_hash(self):
        with self.assertRaises(AssertionError):
            read_archive(archive('../credentials.json', b'{}'))

    def test_nonfinite_json_does_not_become_a_public_result(self):
        with self.assertRaises(ValueError):
            load('{"estimate":NaN}')

    def test_missing_replication_and_false_coverage_summary_rejected(self):
        members, cells = {}, []
        for n, ma, p in itertools.product([119, 240], [0., .5], [1, 2]):
            for rep in range(1000):
                result = {'truth': 0., 'estimate': 0. if rep % 2 else 3., 'se': 1., 'covered': bool(rep % 2)}
                members[f'mc/n{n}-ma{ma}-p{p}/{rep:05}.json'] = json.dumps({'result': result, 'sha256': hashlib.sha256(json.dumps(result, sort_keys=True).encode()).hexdigest()}).encode()
            cells.append({'n': n, 'ma': ma, 'p': p, 'requested': 1000, 'valid': 1000, 'failures': 0, 'conditional_coverage': .5, 'bias': 1.5, 'mcse': (.25 / 1000) ** .5})
        study = {'synthetic': True, 'cells': cells}
        self.assertEqual(validate_mc(members, study), 8000)
        cells[0]['conditional_coverage'] = .95
        with self.assertRaises(AssertionError):
            validate_mc(members, study)
        cells[0]['conditional_coverage'] = .5
        members.pop('mc/n240-ma0.5-p2/00999.json')
        with self.assertRaises(AssertionError):
            validate_mc(members, study)


if __name__ == '__main__':
    unittest.main()
