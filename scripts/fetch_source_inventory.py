from pathlib import Path
from urllib.request import Request, urlopen
import json, hashlib, datetime

root = Path(__file__).resolve().parents[1] / 'data' / 'public_sources'
root.mkdir(parents=True, exist_ok=True)
registry = []

def fetch(url, name):
    req = Request(url, headers={'User-Agent': 'FinAudit-research-source-audit/1.0'})
    with urlopen(req, timeout=60) as response:
        content = response.read()
    (root/name).write_bytes(content)
    registry.append({'url': url, 'file': name, 'sha256': hashlib.sha256(content).hexdigest(),
                     'bytes': len(content), 'retrieved_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    return content

record = json.loads(fetch('https://zenodo.org/api/records/19032377', 'zenodo_record.json'))
for f in record['files']:
    if f['key'] in ('metadata.csv', 'README_data.md', 'checksums.txt'):
        fetch(f['links']['self'], 'zenodo_' + f['key'])
for name in ('metadata.csv', 'LICENSE.md', 'README.md'):
    fetch('https://raw.githubusercontent.com/revdotcom/speech-datasets/main/earnings22/' + name, 'earnings22_' + name)
fetch('https://huggingface.co/api/datasets/kurry/sp500_earnings_transcripts', 'hf_dataset_record.json')
fetch('https://huggingface.co/datasets/kurry/sp500_earnings_transcripts/raw/main/README.md', 'hf_README.md')
(root/'source_registry.json').write_text(json.dumps(registry, indent=2), encoding='utf-8')
print(json.dumps({'downloaded': len(registry), 'bytes': sum(x['bytes'] for x in registry)}))
