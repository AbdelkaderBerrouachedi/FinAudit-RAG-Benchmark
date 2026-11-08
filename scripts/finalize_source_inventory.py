"""Join downloaded text integrity flags to the public inventory by stable row ID."""
from pathlib import Path
import csv,json,gzip,hashlib,datetime

root=Path(__file__).resolve().parents[1]/'data'/'public_sources'
def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for data in iter(lambda:f.read(1024*1024),b''):h.update(data)
    return h.hexdigest()
download=json.loads((root/'transcript_download_summary.json').read_text())
expected='9a305a1c4cbf6c4b0b9c8b98b242ea3de4dbe0ad43937dc54b56418629a17b31'
assert digest(root/'kurry_pinned.parquet')==download['raw_parquet_sha256']==expected
quality={}
with gzip.open(root/'public_calls_2018_2024.jsonl.gz','rt',encoding='utf-8') as f:
    for line in f:
        row=json.loads(line)
        assert row['event_id'] not in quality
        content=row.get('content') or ''
        assert hashlib.sha256(content.encode('utf-8')).hexdigest()==row['content_sha256']
        quality[row['event_id']]={'content_sha256':row['content_sha256'],
                                  'empty_text':not content.strip(),
                                  'duplicate_content':row['duplicate_content'],
                                  'character_count':len(content)}
path=root/'public_call_manifest_2018_2024.csv'
with path.open(encoding='utf-8-sig',newline='') as f:
    reader=csv.DictReader(f);fields=list(reader.fieldnames);rows=list(reader)
assert len(rows)==len(quality)==download['exported_rows']
assert {r['event_id'] for r in rows}==set(quality)
for field in ('content_sha256','empty_text','duplicate_content','character_count'):
    if field not in fields:fields.append(field)
for row in rows:row.update(quality[row['event_id']])
with path.open('w',encoding='utf-8',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
summary_path=root/'public_call_manifest_summary.json'
summary=json.loads(summary_path.read_text())
summary.update(full_transcripts_downloaded=True,empty_texts=download['empty_texts'],
               duplicate_content_rows=download['duplicate_content_rows'],
               manifest_sha256=digest(path),export_sha256=digest(root/'public_calls_2018_2024.jsonl.gz'),
               integrity_verified_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
summary_path.write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,indent=2))
