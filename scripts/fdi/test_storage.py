import json,zipfile
from pathlib import Path
import pytest
from fdi.storage import Study,save_json,verify_archive,file_hash

def project(tmp_path):
    p=tmp_path/'project';(p/'scripts/fdi').mkdir(parents=True);(p/'research/fdi').mkdir(parents=True)
    (p/'scripts/fdi/engine.py').write_text('frozen = True\n')
    (p/'scripts/fdi_pipeline.py').write_text('pass\n')
    (p/'research/fdi/requirements.txt').write_text('numpy==2.2.6\n')
    save_json(p/'research/fdi/study.json',{'seed':7})
    return p

def test_backup_readback_detects_altered_member_even_with_valid_zip_crc(tmp_path):
    s=Study(tmp_path/'data',project(tmp_path));(s.run/'prepared/observation.json').write_text('{"value":12}')
    result=s.backup('prepared');archive=Path(result['path']);assert len(verify_archive(archive))==2
    changed=tmp_path/'altered.zip'
    with zipfile.ZipFile(archive) as source,zipfile.ZipFile(changed,'w') as target:
        for name in source.namelist():target.writestr(name,b'{"value":99}' if name.endswith('observation.json') else source.read(name))
    with pytest.raises(ValueError,match='Content hash mismatch'):verify_archive(changed)

def test_cache_rejects_mutated_input_and_changed_output(tmp_path):
    s=Study(tmp_path/'data',project(tmp_path));a=s.run/'raw/input.csv';b=s.run/'prepared/output.csv'
    a.write_text('1');b.write_text('2');s.finish('prepare',[b],[a]);assert s.cached('prepare',[a])
    a.write_text('3');assert not s.cached('prepare',[a]);a.write_text('1');b.write_text('4');assert not s.cached('prepare',[a])

def test_run_identity_tracks_cli_and_configuration_and_uses_portable_paths(tmp_path):
    p=project(tmp_path);s=Study(tmp_path/'data',p);before=s.identity
    (p/'scripts/fdi_pipeline.py').write_text('print("new")\n');assert Study(tmp_path/'data',p).identity!=before
    item=s.run/'raw/input.csv';item.write_text('a');s.finish('source',[item],[item]);record=json.loads((s.run/'status/source.json').read_bytes())
    assert 'raw/input.csv' in record['outputs'];assert not any('\\' in k for k in record['outputs'])
