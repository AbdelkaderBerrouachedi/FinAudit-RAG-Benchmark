"""Fetch pinned public parquet with checked byte ranges, then export selected text.
This retrieves a new unlabeled corpus, never the unavailable original benchmark.
"""
from pathlib import Path
from urllib.request import Request,urlopen
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib,json,time,threading,sys,gzip,collections
import pyarrow.parquet as pq

root=Path(__file__).resolve().parents[1]/'data'/'public_sources'
record=json.loads((root/'hf_dataset_record.json').read_text(encoding='utf-8'))
revision=record['sha']
if revision != 'f3ded372da8d18dc6ad98955c4558e34b5fe6d45':
    raise ValueError('Source changed; audit the new schema and size before running this adapter')
size=1824805388  # pinned source size; update only with a verified dataset revision
url=f'https://huggingface.co/datasets/kurry/sp500_earnings_transcripts/resolve/{revision}/parquet_files/part-0.parquet'
target=root/'kurry_pinned.parquet';partial=root/'kurry_pinned.parquet.part'
block=16*1024*1024;lock=threading.Lock()
if not target.exists():
    with partial.open('wb') as f: f.truncate(size)
    def download(start):
        end=min(size,start+block)-1
        for attempt in range(5):
            try:
                req=Request(url,headers={'Range':f'bytes={start}-{end}'})
                with urlopen(req,timeout=180) as response:
                    if response.status!=206 or response.headers['Content-Range'].split()[1]!=f'{start}-{end}/{size}':
                        raise ValueError('Range mismatch')
                    data=response.read()
                if len(data)!=end-start+1: raise ValueError('Truncated range')
                with lock,partial.open('r+b') as f: f.seek(start);f.write(data)
                return len(data)
            except Exception:
                if attempt==4: raise
                time.sleep(2**attempt)
    ranges=list(range(0,size,block));done=0
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i,f in enumerate(as_completed([pool.submit(download,x) for x in ranges]),1):
            done+=f.result()
            if i%10==0 or i==len(ranges): print(f'Downloaded {done}/{size} bytes ({i}/{len(ranges)} chunks)',flush=True)
    partial.replace(target)
h=hashlib.sha256()
with target.open('rb') as f:
    for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
if h.hexdigest() != '9a305a1c4cbf6c4b0b9c8b98b242ea3de4dbe0ad43937dc54b56418629a17b31':
    raise ValueError('Downloaded parquet differs from the pinned upstream LFS SHA256')
parquet=pq.ParquetFile(target)
dest=root/'public_calls_2018_2024.jsonl.gz';n=0;source_row=0;empty=0;seen=set();duplicates=0;years=collections.Counter()
with gzip.open(dest,'wt',encoding='utf-8',compresslevel=3) as stream:
    for batch in parquet.iter_batches(batch_size=64,columns=['symbol','company_name','company_id','year','quarter','date','content']):
        for row in batch.to_pylist():
            idx=source_row;source_row+=1
            if row['year'] is None or not 2018<=int(row['year'])<=2024:continue
            text=row.get('content') or ''
            digest=hashlib.sha256(text.encode('utf-8')).hexdigest()
            duplicate=digest in seen;seen.add(digest)
            empty+=not text.strip();duplicates+=duplicate
            row.update(event_id=f'hf-kurry-{idx}',source_row=idx,source_revision=revision,
                       content_sha256=digest,duplicate_content=duplicate,label=None,
                       label_status='unknown_not_a_negative',audio_available=False)
            stream.write(json.dumps(row,ensure_ascii=False)+'\n');n+=1;years[int(row['year'])]+=1
summary={'source_url':url,'revision':revision,'raw_parquet_sha256':h.hexdigest(),
         'source_rows':source_row,'exported_rows':n,'years':dict(years),'empty_texts':empty,
         'duplicate_content_rows':duplicates,'export_bytes':dest.stat().st_size,
         'full_transcripts_downloaded':True,'labels_available':False,'audio_in_this_dataset':False}
(root/'transcript_download_summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary),flush=True)
