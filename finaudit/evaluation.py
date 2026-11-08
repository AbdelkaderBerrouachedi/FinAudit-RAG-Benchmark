"""Binary metrics and paired cluster bootstrap, without fabricated significance.

Undefined ratios are returned as None. F1 uses the explicitly documented
zero-denominator convention 0, matching a fixed binary label set {0, 1}.
No function rounds intermediate results or interprets a score as deception.
"""
from collections import Counter
import math
import numpy as np


def arrays(labels, scores):
    y = np.asarray(labels)
    s = np.asarray(scores, dtype=float)
    if y.ndim != 1 or s.ndim != 1 or len(y) == 0 or len(y) != len(s):
        raise ValueError("Labels and scores must be nonempty, equal-length vectors")
    if not np.all(np.isin(y, [0, 1])) or not np.all(np.isfinite(s)):
        raise ValueError("Labels must be binary and scores finite")
    return y.astype(int), s


def average_ranks(scores):
    s = np.asarray(scores, dtype=float)
    if s.ndim != 1 or not np.all(np.isfinite(s)):
        raise ValueError("Ranks require a finite vector")
    order = np.argsort(s, kind="stable")
    ranks = np.empty(len(s), dtype=float)
    i = 0
    while i < len(s):
        j = i + 1
        while j < len(s) and s[order[j]] == s[order[i]]:
            j += 1
        ranks[order[i:j]] = (i + 1 + j) / 2
        i = j
    return ranks


def auc(labels, scores):
    y, s = arrays(labels, scores)
    pos, neg = int(y.sum()), int((1-y).sum())
    if not pos or not neg:
        return None
    return float((average_ranks(s)[y == 1].sum() - pos*(pos+1)/2)/(pos*neg))


def roc(labels, scores):
    y, s = arrays(labels, scores)
    if not y.sum() or not (1-y).sum():
        return []
    order = np.argsort(-s, kind="stable")
    y, s = y[order], s[order]
    ends = np.r_[np.flatnonzero(np.diff(s) != 0), len(s)-1]
    tp = np.cumsum(y)[ends]
    fp = (ends+1)-tp
    points = [{"threshold": None, "fpr": 0.0, "tpr": 0.0}]
    points += [{"threshold": float(s[i]), "fpr": float(f/(1-y).sum()),
                "tpr": float(t/y.sum())} for i, t, f in zip(ends, tp, fp)]
    return points


def binary_metrics(labels, scores, threshold=0.5, probabilities=False, bins=10):
    y, s = arrays(labels, scores)
    if not math.isfinite(threshold):
        raise ValueError("Threshold must be finite")
    pred = s >= threshold
    tp = int(np.sum(pred & (y == 1)))
    fp = int(np.sum(pred & (y == 0)))
    tn = int(np.sum(~pred & (y == 0)))
    fn = int(np.sum(~pred & (y == 1)))
    def ratio(n, d): return float(n/d) if d else None
    f1p = 2*tp/(2*tp+fp+fn) if 2*tp+fp+fn else 0.0
    f1n = 2*tn/(2*tn+fp+fn) if 2*tn+fp+fn else 0.0
    result = {"n": len(y), "positives": int(y.sum()), "prevalence": float(y.mean()),
              "threshold": float(threshold), "auroc": auc(y, s),
              "positive_f1": f1p, "negative_f1": f1n, "macro_f1": (f1p+f1n)/2,
              "precision": ratio(tp, tp+fp), "recall": ratio(tp, tp+fn),
              "specificity": ratio(tn, tn+fp), "false_positive_rate": ratio(fp, tn+fp),
              "false_discovery_rate": ratio(fp, tp+fp),
              "tp": tp, "fp": fp, "tn": tn, "fn": fn,
              "f1_zero_denominator_policy": "zero; fixed labels [0,1]"}
    if probabilities:
        if not np.all((s >= 0) & (s <= 1)) or not isinstance(bins, int) or bins < 1:
            raise ValueError("Probability metrics require [0,1] scores and positive integer bins")
        groups = np.minimum((s*bins).astype(int), bins-1)
        reliability = []
        for b in range(bins):
            mask = groups == b
            reliability.append({"bin": b, "lower": b/bins, "upper": (b+1)/bins,
                                "n": int(mask.sum()),
                                "mean_prediction": float(s[mask].mean()) if mask.any() else None,
                                "event_rate": float(y[mask].mean()) if mask.any() else None})
        result.update(brier=float(np.mean((s-y)**2)), reliability=reliability,
                      ece=float(sum(r['n']/len(y)*abs(r['mean_prediction']-r['event_rate'])
                                    for r in reliability if r['n'])))
    return result


def paired_cluster_bootstrap(labels, scores_a, scores_b, cluster_ids, replicates=1000, seed=0):
    """Percentile CI for paired AUC difference; resample whole issuer/case clusters.

    This is not a DeLong test. No p-value is manufactured from the CI. Degenerate
    one-class replicates are excluded and their number is reported explicitly.
    Validity requires independent sampled clusters under the stated study design.
    """
    y, a = arrays(labels, scores_a)
    _, b = arrays(labels, scores_b)
    if len(cluster_ids) != len(y) or replicates < 100:
        raise ValueError("One cluster ID per row and at least 100 replicates required")
    groups = {}
    for i, c in enumerate(cluster_ids):
        if c is None or str(c).strip() == "":
            raise ValueError("Empty cluster ID")
        groups.setdefault(str(c), []).append(i)
    if len(groups) < 2 or auc(y, a) is None:
        raise ValueError("Need two classes and at least two independent clusters")
    indices = [np.asarray(v) for v in groups.values()]
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(replicates):
        ix = np.concatenate([indices[i] for i in rng.integers(0, len(indices), len(indices))])
        aa, bb = auc(y[ix], a[ix]), auc(y[ix], b[ix])
        if aa is not None:
            diffs.append(aa-bb)
    valid = len(diffs)
    ci = np.quantile(diffs, [0.025, 0.975]).tolist() if valid >= 100 else None
    return {"method": "paired cluster percentile bootstrap", "auc_difference": auc(y,a)-auc(y,b),
            "ci95": ci, "clusters": len(groups), "requested_replicates": replicates,
            "valid_replicates": valid, "excluded_one_class_replicates": replicates-valid,
            "seed": seed, "p_value": None}


def annotation_metrics(records):
    """Human adjudications; separate claim and citation denominators."""
    if not records:
        raise ValueError("No annotation records")
    ids = [str(x['claim_id']) for x in records]
    if len(ids) != len(set(ids)):
        raise ValueError("Use one adjudicated annotation per unique claim_id")
    allowed = {'supported', 'unsupported', 'unverifiable'}
    if any(x.get('judgment') not in allowed for x in records):
        raise ValueError("Unknown judgment")
    judged = [x for x in records if x['judgment'] != 'unverifiable']
    citations = [c for x in records for c in x.get('citations', [])]
    if any(type(c.get('supported')) is not bool for c in citations):
        raise ValueError("Each citation needs a boolean supported judgment")
    return {"memos": len({x['memo_id'] for x in records}), "claims": len(records),
            "judgments": dict(Counter(x['judgment'] for x in records)),
            "adjudicable_claims": len(judged),
            "unsupported_claim_rate": sum(x['judgment']=='unsupported' for x in judged)/len(judged) if judged else None,
            "citation_count": len(citations),
            "citation_support_rate": sum(x['supported'] for x in citations)/len(citations) if citations else None}
