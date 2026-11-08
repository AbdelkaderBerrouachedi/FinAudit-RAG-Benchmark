import unittest
import math
import copy
import tempfile
import wave
from pathlib import Path
import numpy as np
from finaudit.evaluation import binary_metrics,auc,roc,paired_cluster_bootstrap,annotation_metrics
from finaudit.provenance import validate_manifest,utc,load_json
from finaudit.screening import screen,retrieve
from finaudit.model import fit,predict
from finaudit.cli import evaluate
from finaudit.audio import waveform_features
from finaudit.sec import normalize_companyfacts

ROOT=Path(__file__).resolve().parents[1]


def manifest():
    result=[]
    for si,split in enumerate(('train','validation','test')):
        for j in range(8):
            i=8*si+j
            result.append({'event_id':f'e{i}','issuer_id':f'firm{j%4}',
                           'call_time':f'202{si+1}-01-{j+1:02d}T12:00:00Z',
                           'fiscal_period':f'202{si+1}Q1','source_url':f'synthetic://event/{i}',
                           'split':split,'label':j%2,'label_as_of':'2025-01-01T00:00:00Z',
                           'label_source':'synthetic://fixture','label_definition':'synthetic test label',
                           'data_kind':'synthetic'})
    return result


class MetricsTests(unittest.TestCase):
    def test_macro_f1_regression(self):
        m=binary_metrics([0,0,0,1],[.1,.2,.8,.9])
        self.assertAlmostEqual(m['positive_f1'],2/3)
        self.assertAlmostEqual(m['negative_f1'],.8)
        self.assertAlmostEqual(m['macro_f1'],11/15)

    def test_tie_order_invariance(self):
        self.assertEqual(auc([0,1],[.5,.5]),.5)
        self.assertEqual(auc([1,0],[.5,.5]),.5)

    def test_auc_against_pair_definition(self):
        rng=np.random.default_rng(2)
        for _ in range(30):
            y=rng.integers(0,2,30);s=rng.integers(0,5,30)
            pairs=[(float(a>b)+.5*float(a==b)) for a in s[y==1] for b in s[y==0]]
            self.assertAlmostEqual(auc(y,s),float(np.mean(pairs)))

    def test_roc_matches_auc_with_ties(self):
        y=[0,1,0,1,1];s=[.1,.8,.8,.5,.9]
        p=roc(y,s)
        area=sum((b['fpr']-a['fpr'])*(b['tpr']+a['tpr'])/2 for a,b in zip(p,p[1:]))
        self.assertAlmostEqual(area,auc(y,s))

    def test_undefined_auc_is_not_half(self):
        self.assertIsNone(auc([1,1],[.2,.9]))
        self.assertIsNone(binary_metrics([1,1],[.2,.9])['specificity'])

    def test_invalid_inputs(self):
        for y,s in (([0],[float('nan')]),([2],[.5]),([] ,[]),([0,1],[.5])):
            with self.assertRaises(ValueError): binary_metrics(y,s)
        with self.assertRaises(ValueError):binary_metrics([0,1],[-1,2],probabilities=True)

    def test_probability_bins_include_one(self):
        m=binary_metrics([0,1],[0,1],probabilities=True)
        self.assertEqual(m['brier'],0)
        self.assertEqual(m['ece'],0)
        self.assertEqual(sum(x['n'] for x in m['reliability']),2)

    def test_paired_identical_models(self):
        d=paired_cluster_bootstrap([0,1,0,1],[.1,.8,.4,.7],[.1,.8,.4,.7],['a','a','b','b'],100)
        self.assertEqual(d['ci95'],[0,0]);self.assertIsNone(d['p_value'])

    def test_annotations_denominators(self):
        a=[{'claim_id':'a','memo_id':'1','judgment':'unsupported','citations':[{'supported':False}]},
           {'claim_id':'b','memo_id':'1','judgment':'unverifiable','citations':[]},
           {'claim_id':'c','memo_id':'2','judgment':'supported','citations':[{'supported':True},{'supported':True}]}]
        m=annotation_metrics(a)
        self.assertEqual(m['unsupported_claim_rate'],.5)
        self.assertEqual(m['citation_support_rate'],2/3)
        self.assertEqual(m['memos'],2)


class ScreeningTests(unittest.TestCase):
    def setUp(self):self.bundle=load_json(ROOT/'data'/'synthetic_example.json')

    def test_discrepancy_and_missing_are_separate(self):
        r=screen(self.bundle);d={x['claim_id']:x for x in r['claim_results']}
        self.assertEqual(d['claim-revenue']['disposition'],'no_numeric_discrepancy')
        self.assertEqual(d['claim-cash']['disposition'],'candidate_discrepancy')
        self.assertEqual(d['claim-unknown']['disposition'],'insufficient_evidence')
        self.assertIsNone(d['claim-unknown']['score']);self.assertIsNone(r['probability'])

    def test_future_evidence_excluded(self):
        for doc in self.bundle['documents']:doc['available_at']='2030-01-01T00:00:00Z'
        r=screen(self.bundle)
        self.assertTrue(all(x['disposition']=='insufficient_evidence' for x in r['claim_results']))

    def test_context_mismatch_excluded(self):
        for f in self.bundle['facts']:f['unit']='EUR'
        self.assertTrue(all(x['score'] is None for x in screen(self.bundle)['claim_results']))

    def test_adjusted_basis_does_not_match_reported(self):
        for c in self.bundle['claims']:c['basis']='adjusted'
        self.assertTrue(all(x['score'] is None for x in screen(self.bundle)['claim_results']))

    def test_nan_tolerance_rejected(self):
        with self.assertRaises(ValueError):screen(self.bundle,float('nan'))

    def test_conflicting_facts_abstain(self):
        f=copy.deepcopy(self.bundle['facts'][0]);f['fact_id']='conflict';f['value']=999
        self.bundle['facts'].append(f)
        self.assertEqual(screen(self.bundle)['claim_results'][0]['disposition'],'insufficient_evidence')

    def test_missing_identity_does_not_pass(self):
        r=screen(self.bundle)
        self.assertFalse(any(c['identity']=='total_accruals' and c['status']=='consistent' for c in r['accounting_checks']))

    def test_filing_balance_is_not_truth(self):
        r=screen(self.bundle)
        self.assertTrue(any(c['identity']=='balance_sheet' and c['status']=='consistent' for c in r['accounting_checks']))
        self.assertTrue(any(c['disposition']=='candidate_discrepancy' for c in r['claim_results']))

    def test_lexical_retrieval(self):
        d=retrieve('cash',self.bundle['documents'])
        self.assertTrue(d);self.assertEqual(d[0]['source_id'],'synthetic-filing')


class PipelineTests(unittest.TestCase):
    def test_manifest_unknown_label_rejected(self):
        m=manifest();m[0]['label']=None
        with self.assertRaises(ValueError):validate_manifest(m)

    def test_manifest_temporal_overlap_rejected(self):
        m=manifest();m[0]['call_time']='2024-01-01T00:00:00Z'
        with self.assertRaises(ValueError):validate_manifest(m)

    def test_naive_time_rejected(self):
        with self.assertRaises(ValueError):utc('2020-01-01')

    def test_prediction_alignment_rejected(self):
        with self.assertRaises(ValueError):evaluate(manifest(),[{'event_id':'other','score':.5}],.5,allow_synthetic=True)

    def test_training_and_holdout(self):
        m=manifest();features=[{'event_id':r['event_id'],'features':{'x':2*r['label']-1}} for r in m]
        model=fit(m,features,['x'],allow_synthetic=True)
        outputs=predict(model,features[-8:])
        metrics=evaluate(m,outputs,model['threshold'],True,True)['metrics']
        self.assertEqual(metrics['auroc'],1)
        self.assertEqual(len(model['train_event_ids']),8)
        with self.assertRaises(ValueError):predict(model,features[:1])

    def test_test_features_cannot_change_fit(self):
        m=manifest();f=[{'event_id':r['event_id'],'features':{'x':float(r['label'])}} for r in m]
        a=fit(m,f,['x'],allow_synthetic=True)
        for r in f[-8:]:r['features']['x']=999999
        b=fit(m,f,['x'],allow_synthetic=True)
        self.assertEqual(a,b)

    def test_synthetic_training_needs_opt_in(self):
        with self.assertRaises(ValueError):fit(manifest(),[],['x'])

    def test_waveform_silence_and_tone(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'tone.wav';sr=16000
            samples=(.3*np.sin(2*np.pi*200*np.arange(sr)/sr)*32767).astype('<i2')
            with wave.open(str(p),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes(samples.tobytes())
            r=waveform_features(p)
            self.assertAlmostEqual(r['f0_median_hz'],200,delta=5)
            self.assertIsNone(r['deception_score'])

    def test_sec_unknown_timestamp_excluded(self):
        cf={'cik':1,'facts':{'us-gaap':{'Assets':{'units':{'USD':[{'accn':'a','end':'2020-01-01','val':5}]}}}}}
        r=normalize_companyfacts(cf,{},'2021-01-01T00:00:00Z')
        self.assertEqual(r['facts'],[])
        self.assertEqual(r['excluded_without_eligible_acceptance'],1)


if __name__=='__main__':unittest.main()
