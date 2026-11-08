FinAudit-RAG 0.3 — reference implementation and public-source audit
================================================================

This release replaces the former fixed-score demonstration with executable
source-linked numeric screening, waveform descriptors, a trainable logistic
baseline and corrected evaluation. It does not reproduce the former claimed
12,500-call experiment, B-GAT/LLM system, 500-memo annotation study or financial
performance numbers. No original fitted weights or held-out research predictions
were available. The manuscript has been revised to this narrower evidence level.

INSTALL AND VERIFY
Python 3.10+; tested locally with the Python version recorded in run outputs.
From this Code_Git directory:
  python -m venv .venv
  .venv\Scripts\python -m pip install -r requirements.txt
  .venv\Scripts\python verify.py
On Linux/macOS use .venv/bin/python. The only core third-party dependency is NumPy.
Tests and their logs are in tests/ and runs/verification/. They establish software
behavior on controlled inputs, not detection accuracy on real financial events.

RUN THE SCREENING EXAMPLE
  python run_finaudit.py screen --bundle data/synthetic_example.json --output runs/demo.json
This writes JSON and a readable .txt report. All companies, quotes and values in
that example are fictional. There is one matched amount, one discrepancy, and one
missing-evidence claim. The output deliberately contains no probability of fraud.

Input contract: an event has event_id, issuer_id, call_time (ISO 8601 with timezone),
data_kind (observed or synthetic), documents, facts and claims. See the executable
fixture for exact JSON structure. Each document needs source_id, url, text and
available_at. Each fact needs fact_id, source_id, locator, assurance, concept,
issuer_id, period, unit, basis and finite value. Assurance is reported, reviewed,
audited or unknown. Each claim needs claim_id, quote, transcript_locator, the same
comparison context and value. comparator is eq, at_least or at_most. All units and
periods must be normalized by the input preparer. Different bases do not match.

Only evidence available by the call time is eligible. Missing/conflicting values
produce insufficient_evidence. Lexical retrieval provides context; it does not
convert prose into authenticated facts. Accounting checks inspect arithmetic,
not the economic truth of accounts. Human review follows report generation.

BUILD A LABELED STUDY (NOT INCLUDED)
The public CSV is a source inventory, not accepted as a labeled evaluation manifest.
Do not fill missing labels with zero. A separate JSON array must supply:
  event_id, issuer_id, call_time, fiscal_period, source_url, split, data_kind,
  label (integer 0 or 1), label_source, label_definition, label_as_of.
Optional features_available_at must not follow call_time. Use split=train,
validation,test with strictly separated chronological windows. Deduplicate source
events, resolve issuer/CIK identity and define the outcome horizon before splitting.
The software cannot establish whether manually supplied provenance is true.

Create feature JSON rows of this form:
  {"event_id":"event-001","features":{"discrepancy":0.2,"coverage":0.8}}
Unknown/nonfinite features are rejected; there is no implicit imputation. The
feature table may include the full cohort but fitting reads only train/validation.
  python run_finaudit.py validate-manifest --manifest cohort.json --output runs/cohort_check.json
  python run_finaudit.py train --manifest cohort.json --features features.json --feature-names discrepancy coverage --output runs/model.json
  python run_finaudit.py predict --model runs/model.json --features test_features.json --output runs/predictions.json
Read the saved threshold from model.json and pass exactly that value:
  python run_finaudit.py evaluate --manifest cohort.json --predictions runs/predictions.json --threshold SAVED_THRESHOLD --probabilities --output runs/evaluation.json
The CLI rejects predictions that do not match exactly the test event IDs. Saved
prediction objects also reject a threshold different from the fitted one. A raw
prediction list is accepted for external models, with threshold provenance the
researcher's responsibility. Synthetic studies require --allow-synthetic for
train/evaluate; any resulting metric remains a fixture result.

Corrected evaluation includes class-specific and macro-F1, tie-aware AUROC/ROC,
confusion counts, Brier score and explicit reliability bins. Scores are positive
class scores. Probability metrics require --probabilities and values in [0,1].
An optional comparison_score in every prediction row produces a paired issuer-
cluster bootstrap interval for the AUROC difference (1,000 draws; seed 0). This is
not DeLong, does not test a single AUC against 0.5, and reports no invented p-value.
Repeated cases spanning issuers may require a different clustering design. The
reported percentile interval assumes independent sampling clusters. Undefined AUC
and ratios are null; F1 uses the documented fixed-label zero-denominator convention.

HUMAN ANNOTATIONS
  python run_finaudit.py annotations --input adjudications.json --output runs/annotations.json
Input is one adjudicated row per unique claim_id, with memo_id, judgment
(supported/unsupported/unverifiable), and citations (each with boolean supported).
Keep raw independent rater records separately. This command computes denominators;
it does not simulate raters, measure agreement or create the missing 500-memo study.
Unsupported rate excludes explicitly reported unverifiable claims. Citation support
uses citation count, not memo count. See docs/study_protocol.txt before collecting.

AUDIO
  python run_finaudit.py audio --input recording.wav --output runs/audio.json
Accepts 16-bit uncompressed PCM WAV; computes energy, silence fraction and elementary
autocorrelation F0. It does not implement Whisper, pYIN, diarization, jitter, shimmer
or a validated acoustic deception score. Source audio is not in the text dataset.

SEC DATA
  python run_finaudit.py sec-download --cik 320193 --directory data/sec/apple --user-agent "Your project your-real-email@example.org" --output runs/sec_download.json
  python run_finaudit.py sec-normalize --companyfacts data/sec/apple/companyfacts_0000320193.json --submissions data/sec/apple/submissions_0000320193.json --cutoff 2024-12-31T23:59:59Z --output runs/sec_facts.json
Use your own genuine contact. Sources are rate limited and hashed. Normalization
excludes unavailable/missing accession acceptance timestamps. Recent submissions
may omit historical accessions; merge verified older submission histories first
when needed. A filed date alone is not a verified intraday timestamp. The output is
an intermediate fact table: review measurement basis, period, concept mapping and
filing locator before constructing screening facts/documents. Companyfacts does
not cover every custom tag, footnote or dimensional context. There is no automatic
equivalence between SEC prefixed concepts and the fixture's canonical concepts.

PUBLIC DATA COLLECTION
  python -m pip install -r requirements-data.txt
  python scripts/fetch_source_inventory.py
  python scripts/build_public_manifest.py
  python scripts/download_public_transcripts.py
  python scripts/finalize_source_inventory.py
The download command retrieves a 1.825 GB pinned Parquet and exports the selected text
as gzip JSONL. Allow several GB of free disk space. Downloads are public; no API key
is required. Check upstream terms before redistribution. The source card and
records are kept in data/public_sources. The adapter is pinned to a specific schema
and revision and fails if its expected revision changes. Downloaded transcript text
and the large Parquet are excluded from the small source release ZIP.
The finalization command verifies file/text hashes and adds quality flags to the CSV.

SOURCE MAP
finaudit/screening.py  — BM25, context checks, arithmetic, graph, deterministic memo
finaudit/evaluation.py — metrics, paired cluster bootstrap, annotation denominators
finaudit/provenance.py — strict JSON, hashes, timestamps, manifest checks
finaudit/model.py      — train-only scaling, logistic fit, validation threshold
finaudit/audio.py      — real WAV descriptor calculations
finaudit/sec.py        — SEC acquisition and acceptance-time filtering
finaudit/cli.py        — commands and run provenance
scripts/              — pinned public-data acquisition
tests/                — meaningful correctness and leakage-regression tests

BUILD THE PAPER
From the project root, after running Code_Git/verify.py:
  python Projet_latex/build_paper.py
Requires pdflatex and bibtex on PATH (MiKTeX or TeX Live). Alternatively:
  python Projet_latex/build_paper.py --engine tectonic
Requires Tectonic on PATH. Counts are generated from source inventory and test logs;
the build rejects code changed since verification. main.tex is authoritative. Old
section generators are archived and must not be used to restore retired claims.

LICENSE AND RELEASE STATUS
Core code retains the supplied MIT LICENSE. External data has its own terms; the
code license does not override them. This revision is delivered locally. The
existing public GitHub repository has not been updated or tagged by this task.
The complete original learned-system research implementation remains unavailable.
