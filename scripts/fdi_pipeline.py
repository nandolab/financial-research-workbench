"""Dedicated CPU-only FDI study CLI. No Financial Intelligence imports or inference."""
from pathlib import Path
import argparse, json, sys
from fdi.storage import Study, read_json, verify_archive

def main():
    ap=argparse.ArgumentParser();ap.add_argument('stage',choices=['inspect','acquire','prepare','national','municipal','validate','export','backup','verify'])
    ap.add_argument('--root',type=Path,default=Path('artifacts/local/fdi'));ap.add_argument('--project',type=Path,default=Path(__file__).resolve().parents[1]);ap.add_argument('--destination',type=Path);ap.add_argument('--replications',type=int);ap.add_argument('--archive',type=Path)
    args=ap.parse_args()
    if args.stage=='verify':print(json.dumps({'verified_members':len(verify_archive(args.archive))}));return
    study=Study(args.root,args.project)
    if args.stage=='inspect':
        print(json.dumps({'run':str(study.run),'identity':study.identity,'stages':{p.stem:read_json(p) for p in (study.run/'status').glob('*.json')}},indent=2));return
    if args.stage=='acquire':
        from fdi.sources import acquire
        acquire(study);study.seal_sources();print(study.backup('sources'))
    elif args.stage=='prepare':
        from fdi.prepare import prepare
        prepare(study);print(study.backup('prepared'))
    elif args.stage=='national':
        from fdi.models import national_models
        result=national_models(study,args.replications);print(json.dumps({'state':result['state'],'sample':result['sample'],'diagnostics':result['diagnostics']}));print(study.backup('national'))
    elif args.stage=='municipal':
        from fdi.municipal import municipal_models
        result=municipal_models(study);print(json.dumps(result)[:2000]);print(study.backup('municipal'))
    elif args.stage=='validate':
        from fdi.export import validate
        print(json.dumps(validate(study)))
    elif args.stage=='export':
        from fdi.export import export
        result=export(study,args.destination);print(json.dumps({'identity':result['identity'],'research_status':result['research_status']}));print(study.backup('full'))
    elif args.stage=='backup':print(json.dumps(study.backup('manual',args.destination)))

if __name__=='__main__':main()
