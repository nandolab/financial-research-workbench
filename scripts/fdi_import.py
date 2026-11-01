"""Strict private archive import; copy only reviewed public-safe release files."""
from pathlib import Path
import argparse,io,json,shutil,zipfile
from fdi.storage import Study,canonical,digest,file_hash,read_json,save_json,verify_archive


def import_release(archive,expected_sha,national_archive,root,project,destination):
    if file_hash(archive)!=expected_sha:raise ValueError('Downloaded archive SHA256 differs from Colab receipt')
    manifest=verify_archive(archive);national=verify_archive(national_archive);study=Study(root,project)
    immutable=[k for k in national if k.startswith(('raw/','prepared/','checkpoints/national-bootstrap/')) or k in ['identity.json','models/national.json']]
    for key in immutable:
        if manifest.get(key)!=national[key]:raise ValueError('Frozen national input/output changed: '+key)
    with zipfile.ZipFile(archive) as z:
        identity=json.loads(z.read('identity.json'))
        if identity['identity']!=study.identity or identity['code_sha256']!=study.code_hash:raise ValueError('Study or frozen national code identity mismatch')
        bundle=json.loads(z.read('exports/public/observatory.json'))
        if bundle['identity']!=study.identity or bundle['national']['review']['state']!='passed':raise ValueError('Reviewed public export missing or mismatched')
        if bundle['national']['review']['native_model_sha256']!=national['models/national.json']:raise ValueError('Review identifies another native model')
        if bundle['research_status']['complete_causal_study'] and not bundle['municipal'].get('causal_release_eligible'):raise ValueError('Unsupported complete causal claim')
        extension=z.read('extensions/causal-source.zip');record=json.loads(z.read('extensions/causal-source.json'))
        if digest(extension)!=record['sha256']:raise ValueError('Python extension identity mismatch')
        with zipfile.ZipFile(io.BytesIO(extension)) as source:
            if source.testzip() is not None:raise ValueError('Python source package CRC failed')
            for name in source.namelist():
                path=(project/name).resolve()
                if not path.is_relative_to(project.resolve()) or not path.is_file() or path.read_bytes()!=source.read(name):
                    raise ValueError('Python extension code differs from local reviewed code: '+name)
        # Validate every target before writing any file.
        for name in manifest:
            path=(study.run/name).resolve()
            if not path.is_relative_to(study.run.resolve()):raise ValueError('Unsafe archive target')
        for name in manifest:
            path=study.run/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.read(name))
    destination.mkdir(parents=True,exist_ok=True)
    allowed={'.json','.csv','.svg','.png'};public=study.run/'exports/public'
    for source in public.iterdir():
        if source.is_file() and source.suffix in allowed:shutil.copyfile(source,destination/source.name)
    receipt={'state':'passed','archive_sha256':expected_sha,'members':len(manifest),
        'immutable_national_members_unchanged':len(immutable),'national':'complete',
        'municipal':bundle['municipal']['state'],'export_identity':bundle['export_identity'],
        'extension_sha256':record['sha256'],'raw_data_remains_private':True,
        'public_files':{p.name:file_hash(p) for p in sorted(destination.iterdir()) if p.is_file()}}
    save_json(root/'import-receipt.json',receipt);print(json.dumps({k:v for k,v in receipt.items() if k!='public_files'}))
    return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--archive',type=Path,required=True);p.add_argument('--sha256',required=True)
    p.add_argument('--national-archive',type=Path,required=True);p.add_argument('--root',type=Path,default=Path('artifacts/local/fdi'))
    p.add_argument('--destination',type=Path,default=Path('web/public/data/fdi'));a=p.parse_args()
    import_release(a.archive,a.sha256,a.national_archive,a.root,Path(__file__).resolve().parents[1],a.destination)
