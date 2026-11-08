"""Exercise the public CLI through train -> predict -> evaluate on fictional data."""
from pathlib import Path
import sys,subprocess,json,datetime
from finaudit.provenance import save_json,sha256

root=Path(__file__).resolve().parent
out=root/'runs'/'integration';out.mkdir(parents=True,exist_ok=True)
rows=[];features=[]
for si,split in enumerate(('train','validation','test')):
    for j in range(8):
        event=f'integration-{si}-{j}'
        rows.append({'event_id':event,'issuer_id':f'fictional-{j%4}',
                     'call_time':f'202{si+1}-01-{j+1:02d}T12:00:00Z',
                     'fiscal_period':f'202{si+1}Q1','source_url':f'synthetic://{event}',
                     'split':split,'label':j%2,'label_as_of':'2025-01-01T00:00:00Z',
                     'label_source':'synthetic://integration-fixture',
                     'label_definition':'alternating fictional test labels','data_kind':'synthetic'})
        features.append({'event_id':event,'features':{'x':float(j%2)}})
save_json(out/'manifest.json',rows);save_json(out/'features.json',features)
save_json(out/'test_features.json',features[-8:])
commands=[['train','--manifest',str(out/'manifest.json'),'--features',str(out/'features.json'),
           '--feature-names','x','--allow-synthetic','--output',str(out/'model.json')],
          ['predict','--model',str(out/'model.json'),'--features',str(out/'test_features.json'),
           '--output',str(out/'predictions.json')]]
records=[]
def execute(args):
    p=subprocess.run([sys.executable,str(root/'run_finaudit.py'),*args],cwd=root,capture_output=True,text=True)
    records.append({'arguments':args,'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    if p.returncode:raise RuntimeError(p.stderr or p.stdout)
for command in commands:execute(command)
threshold=json.loads((out/'model.json').read_text())['threshold']
execute(['evaluate','--manifest',str(out/'manifest.json'),'--predictions',str(out/'predictions.json'),
         '--threshold',str(threshold),'--probabilities','--allow-synthetic','--output',str(out/'evaluation.json')])
result=json.loads((out/'evaluation.json').read_text())
assert result['metrics']['n']==8 and result['metrics']['macro_f1']==1.0
save_json(out/'integration_record.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'all_passed':True,'commands':records,'scope':'fictional CLI integration only, not financial accuracy',
          'artifact_sha256':{p.name:sha256(p) for p in out.glob('*.json') if p.name!='integration_record.json'}})
print('CLI integration passed; fictional data only.')
