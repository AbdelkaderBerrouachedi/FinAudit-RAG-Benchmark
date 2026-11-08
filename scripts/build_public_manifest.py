from pathlib import Path
import io, sys, json, csv, collections, urllib.request, time
import pyarrow.parquet as pq

root = Path(__file__).resolve().parents[1]/'data'/'public_sources'
record = json.loads((root/'hf_dataset_record.json').read_text(encoding='utf-8'))
revision = record['sha']
if revision != 'f3ded372da8d18dc6ad98955c4558e34b5fe6d45':
    raise ValueError('Source changed; audit the new schema and size before running this adapter')
url = f'https://huggingface.co/datasets/kurry/sp500_earnings_transcripts/resolve/{revision}/parquet_files/part-0.parquet'

class RangeReader(io.RawIOBase):
    def __init__(self):
        super().__init__()
        self.pos=0
        self.size=1824805388
        self.fetched=0
    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos
    def seek(self, offset, whence=0):
        self.pos = offset if whence==0 else self.pos+offset if whence==1 else self.size+offset
        return self.pos
    def read(self, n=-1):
        if n<0: n=self.size-self.pos
        n=min(n,self.size-self.pos)
        if n<=0: return b''
        if n>128*1024*1024: raise ValueError('Unexpected oversized metadata request')
        req=urllib.request.Request(url, headers={'Range':f'bytes={self.pos}-{self.pos+n-1}'})
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req,timeout=90) as response:
                    if response.status != 206: raise ValueError('Server ignored byte range')
                    start=int(response.headers['Content-Range'].split()[1].split('-')[0])
                    if start != self.pos: raise ValueError('Wrong byte range')
                    data=response.read(n)
                if len(data)!=n: raise ValueError('Incomplete range')
                self.pos+=len(data)
                self.fetched+=len(data)
                return data
            except Exception:
                if attempt==3: raise
                time.sleep(attempt+1)

r=RangeReader()
pf=pq.ParquetFile(r, pre_buffer=False)
print(json.dumps({'schema':pf.schema.names,'rows':pf.metadata.num_rows,'row_groups':pf.num_row_groups}),flush=True)
columns=[c for c in ['symbol','company_name','company_id','year','quarter','date'] if c in pf.schema.names]
table=pf.read(columns=columns, use_threads=False)
rows=table.to_pylist()
fields=['source_row','event_id','symbol','company_name','company_id','year','quarter','call_time_as_supplied','source_dataset','source_revision','label','label_status','audio_status']
selected=[]
for i,row in enumerate(rows):
    if row.get('year') is None or not 2018<=int(row['year'])<=2024: continue
    selected.append(dict(source_row=i,event_id=f'hf-kurry-{i}',symbol=row['symbol'],company_name=row.get('company_name',''),company_id=row.get('company_id',''),year=int(row['year']),quarter=int(row['quarter']),call_time_as_supplied=row['date'],source_dataset=record['id'],source_revision=revision,label='',label_status='unknown_not_a_negative',audio_status='not_in_this_text_dataset'))
with (root/'public_call_manifest_2018_2024.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(selected)
summary={'source_url':url,'revision':revision,'all_rows':len(rows),'selected_rows':len(selected),'unique_symbols':len({x['symbol'] for x in selected}),'years':dict(collections.Counter(x['year'] for x in selected)),'downloaded_metadata_bytes':r.fetched,'full_transcripts_downloaded':False,'label_status':'unlabeled; no AAER/restatement adjudication','purpose':'New public source inventory, not the original FinAudit cohort'}
(root/'public_call_manifest_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary),flush=True)
