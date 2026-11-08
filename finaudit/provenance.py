"""Versioned inputs, strict JSON, and time-aware cohort checks."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib
import json


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def load_json(path):
    def invalid(value): raise ValueError(f"Non-finite JSON constant: {value}")
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), parse_constant=invalid)


def save_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')


def utc(value):
    if not isinstance(value, str):
        raise ValueError("Timestamp required")
    stamp = datetime.fromisoformat(value.replace('Z','+00:00'))
    if stamp.tzinfo is None:
        raise ValueError("Timestamp needs explicit timezone; do not infer intraday availability")
    return stamp.astimezone(timezone.utc)


def validate_manifest(records, require_labels=True):
    if not records:
        raise ValueError("Manifest is empty")
    required = ('event_id','issuer_id','call_time','fiscal_period','source_url','split','data_kind')
    ids, sources, splits = set(), set(), {}
    for r in records:
        if any(not r.get(k) for k in required):
            raise ValueError(f"Missing manifest fields; required: {required}")
        if r['event_id'] in ids:
            raise ValueError("Duplicate event_id")
        ids.add(r['event_id'])
        if r['source_url'] in sources:
            raise ValueError("Duplicate event source; adjudicate duplicates before splitting")
        sources.add(r['source_url'])
        if r['data_kind'] not in ('observed','synthetic') or r['split'] not in ('train','validation','test'):
            raise ValueError("Unknown data kind or split")
        t = utc(r['call_time'])
        splits.setdefault(r['split'], []).append(t)
        if r.get('features_available_at') and utc(r['features_available_at']) > t:
            raise ValueError("Feature evidence available after call")
        if require_labels:
            if type(r.get('label')) is not int or r['label'] not in (0,1):
                raise ValueError("Unknown labels cannot be treated as negatives")
            if not r.get('label_source') or not r.get('label_definition'):
                raise ValueError("Label source and definition required")
            if utc(r['label_as_of']) < t:
                raise ValueError("Outcome observation cutoff precedes call")
    order = [s for s in ('train','validation','test') if s in splits]
    for a,b in zip(order, order[1:]):
        if max(splits[a]) >= min(splits[b]):
            raise ValueError("Chronological splits overlap")
    return {"events":len(records), "issuers":len({r['issuer_id'] for r in records}),
            "splits":dict(Counter(r['split'] for r in records)),
            "data_kinds":dict(Counter(r['data_kind'] for r in records)),
            "positive_counts":{s:sum(r.get('label')==1 for r in records if r['split']==s) for s in order}}
