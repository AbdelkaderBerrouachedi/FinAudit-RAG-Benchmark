"""Explicit commands: illustrative screening is separate from empirical evaluation."""
from pathlib import Path
import argparse
import platform
import sys
import time
from datetime import datetime,timezone
from . import __version__
from .provenance import load_json,save_json,sha256,validate_manifest
from .screening import screen,render_memo
from .evaluation import binary_metrics,roc,paired_cluster_bootstrap,annotation_metrics
from .model import fit,predict
from .audio import waveform_features
from .sec import download_company,normalize_companyfacts


def evaluate(manifest, predictions, threshold, probabilities=False, allow_synthetic=False):
    if isinstance(predictions,dict):
        if 'threshold' in predictions and predictions['threshold'] != threshold:
            raise ValueError('Evaluation threshold differs from the saved fitted threshold')
        predictions=predictions['predictions']
    summary=validate_manifest(manifest)
    records=[r for r in manifest if r['split']=='test']
    if not records: raise ValueError('No held-out test events')
    if any(r['data_kind']=='synthetic' for r in records) and not allow_synthetic:
        raise ValueError('Synthetic test inputs need explicit opt-in')
    by_id={r['event_id']:r for r in predictions}
    if len(by_id)!=len(predictions) or set(by_id)!={r['event_id'] for r in records}:
        raise ValueError('Predictions must match the test set exactly, with unique IDs')
    y=[r['label'] for r in records]; scores=[by_id[r['event_id']]['score'] for r in records]
    result={'cohort':summary,'evaluation_population':'test','data_kinds':sorted({r['data_kind'] for r in records}),
            'metrics':binary_metrics(y,scores,threshold,probabilities),'roc':roc(y,scores)}
    if any('comparison_score' in r for r in predictions):
        if not all('comparison_score' in r for r in predictions): raise ValueError('Incomplete paired predictions')
        result['paired_comparison']=paired_cluster_bootstrap(y,scores,[by_id[r['event_id']]['comparison_score'] for r in records],[r['issuer_id'] for r in records])
    return result


def main(argv=None):
    parser=argparse.ArgumentParser(description='FinAudit 0.3: evidence-limited screening and auditable evaluation')
    commands=parser.add_subparsers(dest='command',required=True)
    p=commands.add_parser('screen');p.add_argument('--bundle',required=True);p.add_argument('--output',required=True)
    p.add_argument('--relative-tolerance',type=float,default=0.01);p.add_argument('--absolute-tolerance',type=float,default=0.0)
    p=commands.add_parser('evaluate');p.add_argument('--manifest',required=True);p.add_argument('--predictions',required=True)
    p.add_argument('--threshold',type=float,required=True);p.add_argument('--probabilities',action='store_true');p.add_argument('--allow-synthetic',action='store_true');p.add_argument('--output',required=True)
    p=commands.add_parser('train');p.add_argument('--manifest',required=True);p.add_argument('--features',required=True)
    p.add_argument('--feature-names',nargs='+',required=True);p.add_argument('--allow-synthetic',action='store_true');p.add_argument('--output',required=True)
    p=commands.add_parser('predict');p.add_argument('--model',required=True);p.add_argument('--features',required=True);p.add_argument('--output',required=True)
    p=commands.add_parser('annotations');p.add_argument('--input',required=True);p.add_argument('--output',required=True)
    p=commands.add_parser('audio');p.add_argument('--input',required=True);p.add_argument('--output',required=True)
    p=commands.add_parser('validate-manifest');p.add_argument('--manifest',required=True);p.add_argument('--output',required=True)
    p=commands.add_parser('sec-download');p.add_argument('--cik',required=True);p.add_argument('--directory',required=True);p.add_argument('--user-agent',required=True);p.add_argument('--output',required=True)
    p=commands.add_parser('sec-normalize');p.add_argument('--companyfacts',required=True);p.add_argument('--submissions',required=True);p.add_argument('--cutoff',required=True);p.add_argument('--output',required=True)
    args=parser.parse_args(argv);start=time.perf_counter()
    inputs={}
    for key in ('bundle','manifest','predictions','features','model','input','companyfacts','submissions'):
        if getattr(args,key,None): inputs[key]={'path':getattr(args,key),'sha256':sha256(getattr(args,key))}
    if args.command=='screen':
        result=screen(load_json(args.bundle),args.relative_tolerance,args.absolute_tolerance)
    elif args.command=='evaluate':
        result=evaluate(load_json(args.manifest),load_json(args.predictions),args.threshold,args.probabilities,args.allow_synthetic)
    elif args.command=='train':
        result=fit(load_json(args.manifest),load_json(args.features),args.feature_names,args.allow_synthetic)
    elif args.command=='predict':
        model=load_json(args.model)
        result={'threshold':model['threshold'],'model_sha256':sha256(args.model),'predictions':predict(model,load_json(args.features))}
    elif args.command=='annotations': result=annotation_metrics(load_json(args.input))
    elif args.command=='audio': result=waveform_features(args.input)
    elif args.command=='sec-download': result={'sources':download_company(args.cik,args.directory,args.user_agent)}
    elif args.command=='sec-normalize': result=normalize_companyfacts(load_json(args.companyfacts),load_json(args.submissions),args.cutoff)
    else: result=validate_manifest(load_json(args.manifest))
    result['run_provenance']={'software_version':__version__,'utc':datetime.now(timezone.utc).isoformat(),
                              'python':platform.python_version(),'platform':platform.platform(),
                              'command':vars(args),'input_files':inputs,'elapsed_seconds':time.perf_counter()-start,
                              'timing_scope':'this local command only; not raw audio-to-LLM end-to-end latency'}
    save_json(args.output,result)
    if args.command=='screen': Path(args.output).with_suffix('.txt').write_text(render_memo(result),encoding='utf-8')
    print(f'Wrote {args.output}')
    return 0


if __name__=='__main__':
    try: raise SystemExit(main())
    except (ValueError,KeyError,OSError) as exc:
        print(f'ERROR: {exc}',file=sys.stderr);raise SystemExit(2)
