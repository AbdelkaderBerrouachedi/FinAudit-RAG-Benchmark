"""Context-matched accounting discrepancies; deterministic, source-linked reports.

Inputs are explicit claim/fact annotations, not automatically verified XBRL or
LLM extraction. No fallback values, causal effects, intent labels or legal verdicts.
"""
import math
import re
from collections import Counter
from .provenance import utc


def finite(value):
    if isinstance(value, bool) or not isinstance(value, (int,float)) or not math.isfinite(value):
        raise ValueError("Expected a finite numeric value, not a boolean or missing value")
    return float(value)


def tokens(text):
    return re.findall(r'[a-z0-9]+', text.lower())


def retrieve(query, documents, k=5):
    """BM25 lexical retrieval; ranking does not establish numerical comparability."""
    if not documents: return []
    q = set(tokens(query))
    terms = [tokens(d['text']) for d in documents]
    avg = sum(map(len,terms))/len(terms) or 1
    df = Counter(t for doc in terms for t in set(doc))
    scored=[]
    for d, ts in zip(documents,terms):
        counts=Counter(ts)
        score=sum(math.log(1+(len(terms)-df[t]+0.5)/(df[t]+0.5)) *
                  counts[t]*2.5/(counts[t]+1.5*(0.25+0.75*len(ts)/avg))
                  for t in q if counts[t])
        if score>0: scored.append({"source_id":d['source_id'],"score":score,"text":d['text']})
    return sorted(scored,key=lambda x:(-x['score'],x['source_id']))[:k]


def validate_bundle(bundle):
    if bundle.get('data_kind') not in ('observed','synthetic'):
        raise ValueError("Explicit observed/synthetic data_kind required")
    call_time=utc(bundle['call_time'])
    if not bundle.get('event_id') or not bundle.get('issuer_id'):
        raise ValueError("Event and issuer identifiers required")
    facts=bundle['facts']; claims=bundle['claims']; docs=bundle['documents']
    for objects,key in ((facts,'fact_id'),(claims,'claim_id'),(docs,'source_id')):
        ids=[x[key] for x in objects]
        if len(ids)!=len(set(ids)): raise ValueError(f"Duplicate {key}")
    source_map={d['source_id']:d for d in docs}
    for d in docs:
        if not d.get('url') or not isinstance(d.get('text'),str):
            raise ValueError("Documents require source URL and text")
        utc(d['available_at'])
    if len({x.get('fact_id',x.get('claim_id')) for x in facts+claims}) != len(facts)+len(claims):
        raise ValueError('Claim and fact IDs must be globally distinct')
    for item in facts+claims:
        finite(item['value'])
        if any(not item.get(k) for k in ('concept','period','unit','issuer_id','basis')):
            raise ValueError("Every numeric item needs concept, period, unit, issuer and measurement basis")
        if item['issuer_id']!=bundle['issuer_id']: raise ValueError("Issuer mismatch")
    for f in facts:
        if f['source_id'] not in source_map or not f.get('locator'):
            raise ValueError("Fact requires an existing source and locator")
        if f.get('assurance') not in ('reported','reviewed','audited','unknown'):
            raise ValueError("Declare source assurance, without inferring truth")
    for c in claims:
        if c.get('comparator','eq') not in ('eq','at_least','at_most'):
            raise ValueError("Unsupported claim comparator")
        if not c.get('quote') or not c.get('transcript_locator'):
            raise ValueError("Claims need a quote and transcript locator")
    return source_map, call_time


def compare_claim(claim, facts, sources, call_time, relative_tolerance=0.01, absolute_tolerance=0.0):
    finite(relative_tolerance);finite(absolute_tolerance)
    if relative_tolerance<0 or absolute_tolerance<0:
        raise ValueError("Tolerances must be nonnegative")
    keys=('concept','period','unit','issuer_id','basis')
    matching=[f for f in facts if all(f[k]==claim[k] for k in keys)]
    available=[f for f in matching if utc(sources[f['source_id']]['available_at'])<=call_time]
    result={'claim_id':claim['claim_id'],'quote':claim['quote'],'concept':claim['concept'],
            'transcript_locator':claim['transcript_locator'],
            'comparison_context':{k:claim[k] for k in keys},
            'disposition':'insufficient_evidence','score':None,'evidence':[],
            'reason':'No context-matched evidence available by the call timestamp'}
    if not available: return result
    values={finite(f['value']) for f in available}
    if len(values)!=1:
        result['reason']='Conflicting source values; human source/context adjudication required'
        result['evidence']=[{'fact_id':f['fact_id'],'source_id':f['source_id'],'locator':f['locator'],
                            'value':f['value'],'assurance':f['assurance'],
                            'url':sources[f['source_id']]['url']} for f in available]
        return result
    observed=values.pop(); claimed=finite(claim['value'])
    comparator=claim.get('comparator','eq')
    diff=abs(claimed-observed) if comparator=='eq' else max(0,claimed-observed) if comparator=='at_least' else max(0,observed-claimed)
    scale=max(abs(claimed),abs(observed),1e-12)
    tolerance=absolute_tolerance+relative_tolerance*scale
    result.update(disposition='candidate_discrepancy' if diff>tolerance else 'no_numeric_discrepancy',
                  score=min(1.0,diff/scale),claimed_value=claimed,reported_value=observed,
                  comparator=comparator,absolute_difference=diff,tolerance=tolerance,
                  reason='Context-matched numeric comparison; this is not a truth or intent judgment',
                  evidence=[{'fact_id':f['fact_id'],'source_id':f['source_id'],
                             'locator':f['locator'],'assurance':f['assurance'],
                             'url':sources[f['source_id']]['url']} for f in available])
    return result


def accounting_checks(facts, sources, call_time, relative_tolerance=1e-6):
    """Check reported arithmetic only; unknown inputs never silently become zeros."""
    identities=[('balance_sheet','Assets',('Liabilities','Equity'),(1,1)),
                ('gross_profit','GrossProfit',('Revenue','CostOfRevenue'),(1,-1)),
                ('total_accruals','TotalAccruals',('NetIncome','OperatingCashFlow'),(1,-1))]
    contexts=sorted({(f['issuer_id'],f['period'],f['unit'],f['basis']) for f in facts})
    checks=[]
    for context in contexts:
        selected=[f for f in facts if (f['issuer_id'],f['period'],f['unit'],f['basis'])==context and
                  utc(sources[f['source_id']]['available_at'])<=call_time]
        values={}
        for f in selected: values.setdefault(f['concept'],set()).add(finite(f['value']))
        for name,lhs,rhs,signs in identities:
            required=(lhs,)+rhs
            if not any(k in values for k in required): continue
            if any(len(values.get(k,set()))!=1 for k in required):
                checks.append({'identity':name,'context':list(context),'status':'not_assessed','reason':'Missing or conflicting terms'})
                continue
            actual=next(iter(values[lhs])); expected=sum(s*next(iter(values[k])) for k,s in zip(rhs,signs))
            residual=actual-expected
            checks.append({'identity':name,'context':list(context),'status':'consistent' if abs(residual)<=relative_tolerance*max(abs(actual),abs(expected),1) else 'arithmetic_discrepancy','residual':residual})
    return checks


def screen(bundle, relative_tolerance=0.01, absolute_tolerance=0.0):
    sources,call_time=validate_bundle(bundle)
    results=[compare_claim(c,bundle['facts'],sources,call_time,relative_tolerance,absolute_tolerance) for c in bundle['claims']]
    docs=[d for d in bundle['documents'] if utc(d['available_at'])<=call_time]
    for c,r in zip(bundle['claims'],results):
        r['retrieved_context']=retrieve(c['quote'],docs)
    scores=[r['score'] for r in results if r['score'] is not None]
    graph={'nodes':[{'id':c['claim_id'],'type':'claim'} for c in bundle['claims']]+
                   [{'id':f['fact_id'],'type':'financial_fact'} for f in bundle['facts']],
           'edges':[{'from':r['claim_id'],'to':e['fact_id'],'type':'context_matched_reference'}
                    for r in results for e in r['evidence']]}
    return {'schema_version':'0.3','event_id':bundle['event_id'],'data_kind':bundle['data_kind'],
            'issuer_id':bundle['issuer_id'],'call_time':bundle['call_time'],
            'method':'context-matched numeric discrepancy with lexical source retrieval',
            'max_discrepancy':max(scores) if scores else None,
            'evidence_coverage':len(scores)/len(results) if results else None,
            'probability':None,'probability_status':'not_estimated',
            'claim_results':results,'accounting_checks':accounting_checks(bundle['facts'],sources,call_time),
            'graph':graph,'human_review_required':True}


def render_memo(result):
    lines=['FinAudit source-linked screening report',f"Event: {result['event_id']}",
           f"Data kind: {result['data_kind']}",
           'Scope: numeric discrepancies in annotated inputs; no intent or legal determination.',
           'A report of no numeric discrepancy does not establish truth or compliance.','']
    for r in result['claim_results']:
        lines += [f"{r['claim_id']}: {r['disposition']}",r['quote'],
                  f"Transcript locator: {r['transcript_locator']}",r['reason']]
        for e in r['evidence']:
            lines.append(f"  Source: {e['source_id']} | {e['locator']} | {e.get('url','source conflict')}")
        lines.append('')
    return '\n'.join(lines)
