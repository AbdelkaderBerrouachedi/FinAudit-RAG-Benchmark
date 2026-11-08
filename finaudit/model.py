"""Train-only-standardized logistic baseline with validation-only threshold selection.

This is an executable baseline, not the previously claimed B-GAT. It must be
trained on actual labeled events before any empirical performance is reported.
"""
import numpy as np
from .evaluation import binary_metrics
from .provenance import validate_manifest


def sigmoid(z):
    return np.exp(-np.logaddexp(0,-z))


def matrix(rows, names):
    if not rows or not names or len(names)!=len(set(names)):
        raise ValueError('Nonempty rows and unique feature names required')
    x=np.asarray([[r['features'][n] for n in names] for r in rows],dtype=float)
    if not np.all(np.isfinite(x)): raise ValueError('Missing/nonfinite features; no implicit imputation')
    return x


def fit(records, feature_rows, feature_names, allow_synthetic=False, iterations=1000, learning_rate=0.1, l2=0.01):
    validate_manifest(records)
    if iterations<1 or learning_rate<=0 or l2<0: raise ValueError('Invalid training configuration')
    if not allow_synthetic and any(r['data_kind']=='synthetic' for r in records):
        raise ValueError('Synthetic fixtures require explicit opt-in and are not empirical evidence')
    by_id={r['event_id']:r for r in feature_rows}
    if len(by_id)!=len(feature_rows): raise ValueError('Duplicate feature event IDs')
    train=[r for r in records if r['split']=='train']; val=[r for r in records if r['split']=='validation']
    if not train or not val: raise ValueError('Both training and validation partitions required')
    for subset in (train,val):
        if {r['label'] for r in subset}!={0,1}: raise ValueError('Both labels required in training and validation')
    x=matrix([by_id[r['event_id']] for r in train],feature_names)
    xv=matrix([by_id[r['event_id']] for r in val],feature_names)
    mean=x.mean(axis=0);std=x.std(axis=0);std[std==0]=1
    x=(x-mean)/std;xv=(xv-mean)/std
    y=np.asarray([r['label'] for r in train]);yv=np.asarray([r['label'] for r in val])
    w=np.zeros(x.shape[1]);bias=0.0
    for _ in range(iterations):
        error=sigmoid(x@w+bias)-y
        w-=learning_rate*(x.T@error/len(y)+l2*w)
        bias-=learning_rate*error.mean()
    pv=sigmoid(xv@w+bias)
    candidates=np.unique(np.r_[0,pv,1])
    ranked=[(binary_metrics(yv,pv,float(t))['macro_f1'],-abs(float(t)-0.5),float(t)) for t in candidates]
    best=max(ranked)
    return {'schema_version':'0.3','model_type':'standardized_l2_logistic_regression',
            'feature_names':feature_names,'mean':mean.tolist(),'std':std.tolist(),
            'weights':w.tolist(),'bias':float(bias),'threshold':best[2],
            'threshold_selection':'maximize validation macro-F1; ties closest to 0.5, then larger',
            'validation_macro_f1':best[0],'train_event_ids':[r['event_id'] for r in train],
            'validation_event_ids':[r['event_id'] for r in val],
            'data_kinds':sorted({r['data_kind'] for r in records}),
            'config':{'iterations':iterations,'learning_rate':learning_rate,'l2':l2},
            'training_loss':float(np.mean(np.logaddexp(0,x@w+bias)-y*(x@w+bias))),
            'calibration_status':'no post-hoc calibration; probabilities require held-out assessment'}


def predict(model, feature_rows, require_unseen=True):
    if model.get('model_type')!='standardized_l2_logistic_regression': raise ValueError('Unsupported model')
    ids=[r['event_id'] for r in feature_rows]
    if len(ids)!=len(set(ids)): raise ValueError('Duplicate prediction event IDs')
    used=set(model['train_event_ids']+model['validation_event_ids'])
    if require_unseen and used.intersection(ids): raise ValueError('Prediction input overlaps fitting events')
    x=matrix(feature_rows,model['feature_names'])
    std=np.asarray(model['std'],dtype=float)
    if not np.all(std>0): raise ValueError('Invalid fitted scaling')
    p=sigmoid(((x-np.asarray(model['mean']))/std)@np.asarray(model['weights'])+model['bias'])
    if not np.all(np.isfinite(p)): raise ValueError('Nonfinite fitted parameters/output')
    return [{'event_id':r['event_id'],'score':float(s),'prediction':int(s>=model['threshold'])} for r,s in zip(feature_rows,p)]
