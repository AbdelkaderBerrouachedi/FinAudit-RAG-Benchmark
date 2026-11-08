"""SEC acquisition and point-in-time fact normalization.

Callers supply a genuine contact User-Agent. Company-facts filed dates alone do
not establish intraday availability: an accession acceptance timestamp is required.
Custom tags and dimensional contexts are not covered by company-facts aggregation.
"""
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import HTTPError
import json,time,hashlib
from datetime import datetime,timezone
from .provenance import save_json,utc


def download_company(cik, destination, user_agent):
    if not str(cik).isdigit() or not user_agent.strip():
        raise ValueError('Numeric CIK and descriptive contact User-Agent required')
    cik=str(cik).zfill(10);root=Path(destination);root.mkdir(parents=True,exist_ok=True)
    records=[]
    urls={'submissions':f'https://data.sec.gov/submissions/CIK{cik}.json',
          'companyfacts':f'https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json'}
    for kind,url in urls.items():
        for attempt in range(4):
            try:
                with urlopen(Request(url,headers={'User-Agent':user_agent,'Accept':'application/json'}),timeout=60) as r:
                    data=r.read()
                json.loads(data)
                path=root/f'{kind}_{cik}.json';path.write_bytes(data)
                records.append({'url':url,'file':path.name,'sha256':hashlib.sha256(data).hexdigest(),
                                'retrieved_at':datetime.now(timezone.utc).isoformat()})
                time.sleep(0.25);break
            except HTTPError as exc:
                if exc.code not in (429,500,502,503,504) or attempt==3:raise
                time.sleep(2**attempt)
    save_json(root/f'sources_{cik}.json',records)
    return records


def normalize_companyfacts(companyfacts, submissions, cutoff):
    """Return only facts with verified accession acceptance <= cutoff.

    'submissions' may contain a merged recent/older accession table. Missing older
    accession timestamps exclude facts; never infer a midnight timestamp from date.
    """
    cutoff=utc(cutoff)
    recent=submissions.get('filings',{}).get('recent',submissions)
    stamps={a:t for a,t in zip(recent.get('accessionNumber',[]),recent.get('acceptanceDateTime',[]))}
    facts=[];excluded=0
    cik=str(companyfacts['cik']).zfill(10)
    for taxonomy,concepts in companyfacts.get('facts',{}).items():
        for concept,data in concepts.items():
            for unit,entries in data.get('units',{}).items():
                for i,item in enumerate(entries):
                    accession=item.get('accn');stamp=stamps.get(accession)
                    if not stamp or utc(stamp)>cutoff:
                        excluded+=1;continue
                    value=item.get('val')
                    if isinstance(value,bool) or not isinstance(value,(float,int)):continue
                    period=item.get('end','') if not item.get('start') else item['start']+'/'+item['end']
                    facts.append({'fact_id':f'{taxonomy}:{concept}:{accession}:{unit}:{i}',
                                  'issuer_id':cik,'concept':f'{taxonomy}:{concept}','value':value,'unit':unit,
                                  'period':period,'accession':accession,'available_at':stamp,
                                  'form':item.get('form'),'assurance':'reported',
                                  'source_url':f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace("-","")}/'})
    return {'facts':facts,'excluded_without_eligible_acceptance':excluded,
            'scope':'standard entity-level companyfacts; no custom-tag or footnote completeness claim'}
