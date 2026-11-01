"""Content-verified stage cache and durable, independently verifiable archives."""
from __future__ import annotations
import hashlib, json, os, platform, shutil, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path

def now(): return datetime.now(timezone.utc).isoformat()
def digest(data: bytes): return hashlib.sha256(data).hexdigest()
def canonical(value): return json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')
def save_json(path: Path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp');tmp.write_bytes(canonical(value));os.replace(tmp,path)
def read_json(path: Path): return json.loads(path.read_bytes())
def file_hash(path: Path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''):h.update(chunk)
    return h.hexdigest()

class Study:
    def __init__(self, root: Path, project: Path):
        self.root=Path(root).resolve();self.project=Path(project).resolve()
        self.config=read_json(self.project/'research/fdi/study.json')
        paths=[p for p in (self.project/'scripts/fdi').glob('*.py') if not p.name.startswith('test_')]+list((self.project/'scripts/fdi').glob('*.R'))+[self.project/'research/fdi/requirements.txt',self.project/'scripts/fdi_pipeline.py']
        self.code_hash=digest(canonical({p.relative_to(self.project).as_posix():file_hash(p) for p in sorted(paths)}))
        self.base_identity=digest(canonical({'config':self.config,'code':self.code_hash}))
        locator=self.root/'studies'/f'{self.base_identity}.json'
        self.identity=read_json(locator)['identity'] if locator.exists() else self.base_identity
        self.run=self.root/'runs'/self.identity[:16]
        for folder in ['raw','prepared','models','checkpoints','exports','figures','status']:(self.run/folder).mkdir(parents=True,exist_ok=True)
        if not (self.run/'identity.json').exists():save_json(self.run/'identity.json',{'identity':self.identity,'code_sha256':self.code_hash,'config':self.config,'python':sys.version,'platform':platform.platform()})
    def seal_sources(self):
        records=read_json(self.run/'raw/sources.json')
        snapshot={k:{'sha256':v.get('sha256'),'status':v['status'],'url':v['url']} for k,v in records.items()}
        identity=digest(canonical({'specification':self.base_identity,'sources':snapshot}))
        target=self.root/'runs'/identity[:16]
        if target!=self.run:
            target.mkdir(parents=True,exist_ok=True)
            for p in self.run.rglob('*'):
                if p.is_file():
                    dest=target/p.relative_to(self.run);dest.parent.mkdir(parents=True,exist_ok=True)
                    if not dest.exists():shutil.copyfile(p,dest)
                    elif file_hash(dest)!=file_hash(p):raise ValueError('Existing sealed source differs')
            self.run=target;self.identity=identity
            for folder in ['raw','prepared','models','checkpoints','exports','figures','status']:(self.run/folder).mkdir(parents=True,exist_ok=True)
        save_json(self.run/'identity.json',{'identity':identity,'code_sha256':self.code_hash,'sources_sha256':digest(canonical(snapshot)),'config':self.config,'python':sys.version,'platform':platform.platform()})
        save_json(self.root/'studies'/f'{self.base_identity}.json',{'identity':identity})
        return identity
    def fingerprint(self, inputs=()):return digest(canonical({p.relative_to(self.run).as_posix():file_hash(p) for p in sorted(inputs)}))
    def cached(self, stage, inputs=()):
        p=self.run/'status'/f'{stage}.json'
        if not p.exists():return False
        d=read_json(p)
        return d.get('state')=='complete' and d.get('inputs')==self.fingerprint(inputs) and all((self.run/k).is_file() and file_hash(self.run/k)==v for k,v in d.get('outputs',{}).items())
    def finish(self,stage,outputs,inputs=(),details=None):
        save_json(self.run/'status'/f'{stage}.json',{'state':'complete','at':now(),'identity':self.identity,'inputs':self.fingerprint(inputs),'outputs':{p.relative_to(self.run).as_posix():file_hash(p) for p in outputs},'details':details or {}})
    def unavailable(self,stage,reason,details=None):
        save_json(self.run/'status'/f'{stage}.json',{'state':'unavailable','at':now(),'reason':reason,'details':details or {}})
    def backup(self,label,destination=None):
        """Snapshot only finished files. Verify archive and each member before recording success."""
        target=Path(destination) if destination else self.root/'backups'
        target.mkdir(parents=True,exist_ok=True)
        files=[p for p in sorted(self.run.rglob('*')) if p.is_file() and not p.name.endswith('.tmp')]
        manifest={str(p.relative_to(self.run)).replace('\\','/'):file_hash(p) for p in files}
        archive=target/f'fdi-{self.identity[:16]}-{label}.zip'
        temporary=archive.with_suffix('.zip.tmp')
        with zipfile.ZipFile(temporary,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
            for p in files:z.write(p,str(p.relative_to(self.run)).replace('\\','/'))
            z.writestr('ARCHIVE-MANIFEST.json',canonical(manifest))
        os.replace(temporary,archive)
        verify_archive(archive)
        result={'path':str(archive),'sha256':file_hash(archive),'bytes':archive.stat().st_size,'members':len(manifest),'verified_at':now(),'crc':'passed','content_hashes':'passed'}
        save_json(archive.with_suffix('.verified.json'),result)
        return result

def verify_archive(path):
    with zipfile.ZipFile(path) as z:
        bad=z.testzip()
        if bad:raise ValueError(f'CRC failed: {bad}')
        manifest=json.loads(z.read('ARCHIVE-MANIFEST.json'))
        if set(z.namelist())!=set(manifest)|{'ARCHIVE-MANIFEST.json'}:raise ValueError('Archive membership mismatch')
        for name,sha in manifest.items():
            if digest(z.read(name))!=sha:raise ValueError(f'Content hash mismatch: {name}')
    return manifest
