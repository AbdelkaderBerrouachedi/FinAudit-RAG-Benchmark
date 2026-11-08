"""Execute and log real verification; do not interpret fixtures as benchmark data."""
from pathlib import Path
import subprocess,sys,hashlib,json,datetime

root=Path(__file__).resolve().parent
out=root/'runs'/'verification';out.mkdir(parents=True,exist_ok=True)
commands=[['-m','unittest','discover','-s','tests','-v'],
          ['run_finaudit.py','screen','--bundle','data/synthetic_example.json','--output','runs/verification/synthetic_screen.json']]
results=[]
for i,args in enumerate(commands):
    p=subprocess.run([sys.executable,*args],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8')
    (out/f'command_{i}.log').write_text(p.stdout,encoding='utf-8')
    results.append({'command':[sys.executable,*args],'returncode':p.returncode,'log':f'command_{i}.log'})
hashes={str(p.relative_to(root)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
        for folder in ('finaudit','tests') for p in (root/folder).glob('*.py')}
summary={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commands':results,
         'all_passed':all(x['returncode']==0 for x in results),'source_sha256':hashes,
         'scope':'synthetic correctness tests and illustrative screening only; no labeled financial benchmark'}
(out/'verification.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
raise SystemExit(0 if summary['all_passed'] else 1)
