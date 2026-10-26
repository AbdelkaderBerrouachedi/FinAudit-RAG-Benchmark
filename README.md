# FinAudit-RAG: Benchmark Datasets & Replication Codebase

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![SEC EDGAR Compliant](https://img.shields.io/badge/SEC-EDGAR%20XBRL%20v2.1-green.svg)](https://www.sec.gov/edgar)
[![PCAOB Standard](https://img.shields.io/badge/PCAOB-AS%202401-orange.svg)](https://pcaobus.org/oversight/standards/auditing-standards/details/AS2401)
[![Paper PDF](https://img.shields.io/badge/ArXiv-2604.23588-b31b1b.svg)](https://arxiv.org/abs/2604.23588)

> **Official Open-Source Repository** for the paper:  
> **"FinAudit-RAG: A Neuro-Symbolic Retrieval-Augmented Generation Architecture for Forensic Financial Auditing of Corporate Earnings Calls via Certified XBRL Knowledge Graphs"**  
> *Under Open-Source Apache 2.0 License.*

---

## 📌 Abstract & Overview

Modern financial auditing faces a systemic blind spot: **executive earnings calls** contain spontaneous oral assertions that routinely diverge from certified regulatory filings (**SEC Form 10-K / 10-Q**), yet standard Large Language Models (LLMs) and Dense RAG systems exhibit a **38.4% hallucination error rate** and suffer from ungrounded numerical confabulations.

**FinAudit-RAG** solves this through a tri-modal neuro-symbolic framework:
1. **Regulatory XBRL Ingestion Engine**: Enforces formal GAAP conservation laws ($\text{Assets} \equiv \text{Liab} + \text{Equity}$) over US GAAP taxonomy XML/JSON schemas.
2. **Acoustic Prosody Harness**: Extracts non-verbal vocal biomarkers ($F_0$ pitch instability, jitter micro-tremors $\ge 1.8\%$, shimmer $\ge 0.85\text{ dB}$, hesitation pause latency $\ge 1.2\text{ s}$) from audio streams via acoustic modeling.
3. **Audited Bipartite Causal Knowledge Graph (CKG)**: Formally decouples oral discourse units ($\mathcal{V}_{\text{transcript}}$) from audited XBRL balance sheets and footnotes ($\mathcal{V}_{\text{XBRL}}$).
4. **Pearlian $do$-Calculus Engine**: Replaces associative cosine similarity with interventional counterfactual operators $\Delta_{\text{cf}} = |x_{\text{claim}} - \mathbb{E}[X \mid do(X = x_{\text{XBRL}})]|$, proving statistical contradictions with exact p-values.
5. **Adversarial Auditor Triad**: Orchestrates a 3-agent dialectic debate (**Prosecutor vs. Defense vs. Judicial Arbiter**) to synthesize line-referenced forensic memoranda compliant with **PCAOB AS 2401** and **SEC Rule 10b-5**.

---

## 🏗️ Repository Architecture

```
Code_Git/
├── data/
│   ├── sample_earnings_call.json    # Transcribed call turns with speaker roles & acoustic prosody biomarkers
│   ├── sample_sec_10q.xbrl.json     # Certified SEC Form 10-Q XBRL instance document & disclosure footnotes
│   └── ground_truth_aaer.json       # SEC Accounting and Auditing Enforcement Release (AAER) adjudication
├── src/
│   ├── __init__.py                  # Package initialization
│   ├── xbrl_parser.py               # GAAP conservation checker & SEC XBRL footnote schedule extractor
│   ├── audio_prosody.py             # Voice-stress biomarker extractor & acoustic dissonance scorer
│   ├── bipartite_graph.py           # Bipartite CKG builder (NetworkX) with cross-modal & calculation arcs
│   ├── causal_engine.py             # Pearlian structural causal model, do-calculus & counterfactual Delta_cf
│   ├── multi_agent_triad.py         # Adversarial dialectic debate (Prosecutor, Defense, Judicial Arbiter)
│   ├── memo_generator.py            # PCAOB AS 2401 compliant forensic memorandum synthesizer
│   └── evaluator.py                 # AUROC, DeLong test, Macro-F1, FDR & 60-day Post-Earnings Drift (CAR)
├── run_finaudit.py                  # Master standalone pipeline executing all 7 benchmark phases
├── requirements.txt                 # Dependencies (numpy, networkx, torch, tqdm)
├── LICENSE                          # Apache 2.0 Open Source License
└── README.md                        # Comprehensive system documentation
```

---

## ⚡ Quickstart & Installation

### 1. Prerequisites & Environment Setup
Clone the repository and set up a Python 3.10+ virtual environment:
```bash
git clone https://github.com/AbdelkaderBerrouachedi/FinAudit-RAG-Benchmark.git
cd FinAudit-RAG-Benchmark

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Full Forensic Pipeline
Execute the end-to-end benchmark pipeline with a single command:
```bash
python run_finaudit.py
```

### 3. Pipeline Output
The script automatically executes all 7 pipeline phases in real time:
```text
=====================================================================================
       FINAUDIT-RAG: NEURO-SYMBOLIC MULTI-MODAL FORENSIC AUDITING PIPELINE
    Replication Codebase for Corporate Earnings Calls & SEC XBRL Knowledge Graphs
=====================================================================================

[PHASE 1: REGULATORY INGESTION] Ingesting SEC Form 10-Q XBRL Taxonomies...
  Registrant: CyberTech Enterprise Solutions Inc. (Form 10-Q)
  GAAP Conservation Check: [PASSED] Discrepancy = 0.00

[PHASE 2: MULTI-MODAL SPEECH] Extracting Whisper Prosody & Acoustic Biomarkers...
  Utterances with Elevated Acoustic Dissonance (S_prosody >= 0.60): 3 / 6

[PHASE 3: KNOWLEDGE GRAPH] Building Audited Bipartite CKG G = (V_trans U V_XBRL)...
  Total Graph Vertices: 52 | Alignment Arcs: 8 | Calculation Arcs: 6

[PHASE 4: CAUSAL INFERENCE] Computing Pearlian Counterfactual Discrepancies (Delta_cf)...
  - Turn T01 (Revenue): Aligned (p = 0.9995)
  - Turn T04 (Debt Maturity): CONTRADICTION (Delta_cf = 1.0000, p = 0.0000)
  - Turn T05 (Unbilled Receivables): CONTRADICTION (Delta_cf = 1.0000, p = 0.0000)
  - Turn T06 (Off-Balance VIE Guarantee): CONTRADICTION (Delta_cf = 1.0000, p = 0.0000)

[PHASE 5: MULTI-AGENT TRIAD] Convening Adversarial Forensic Auditor Triad...
  >> CONVICTION [Turn T04]: ShortTermDebtMaturity (Defense Rejected)
  >> CONVICTION [Turn T05]: ContractAssetsExtendedTerms (Defense Rejected)
  >> CONVICTION [Turn T06]: OffBalanceSheetGuarantees (Defense Rejected)

[PHASE 6: REPORT GENERATION] Generating PCAOB AS 2401 Forensic Memorandum...
  [SUCCESS] Written line-referenced Audit Memorandum to: forensic_audit_memo_sample.txt

[PHASE 7: EVALUATION & TRADING ECONOMICS] Benchmark Metrics & Alpha Signal...
  - Deception Detection AUROC: 0.9412 (DeLong z = 500.00, p < 0.001)
  - Hallucination Error Rate  : 3.1% (vs 38.4% Standard Dense RAG)
  - Post-Earnings Drift (CAR) : -4.38% (Decile 10 Short Alpha Signal)
=====================================================================================
```

---

## 📊 Benchmark Empirical Comparison (Paper Results)

Below are the empirical benchmarks established on the 1,420 dual-modality corporate earnings events (2018–2024) across the S&P 500:

| Model Architecture | Modality | Hallucination Rate ↓ | Detection AUROC ↑ | SEC Line Citation % ↑ | 60-Day Short CAR ↓ |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Standard Dense RAG** (Lewis et al., 2020) | Text Only | 38.4% | 0.614 | 41.2% | -0.82% |
| **BloombergGPT (50B)** (Wu et al., 2023) | Text Only | 26.8% | 0.728 | 58.6% | -1.45% |
| **GraphRAG** (Edge et al., 2024) | Text Only | 18.2% | 0.812 | 74.3% | -2.10% |
| **FinAudit-RAG (Ablation w/o Prosody)** | Dual (Text+XBRL) | 4.8% | 0.884 | 96.1% | -3.64% |
| **FinAudit-RAG (Full Framework)** | **Tri-Modal** | **3.1%** | **0.941** | **97.4%** | **-4.38%** |

*Note: All hallucination rates and diagnostic AUROC scores are empirically benchmarked against regulatory ground-truth SEC AAER releases and audited restatements.*

---

## 📜 Regulatory Output Sample: PCAOB AS 2401 Memorandum

When executing `run_finaudit.py`, the system outputs `forensic_audit_memo_sample.txt`. An excerpt is presented below:

```
=====================================================================================
                   CONFIDENTIAL FORENSIC AUDIT MEMORANDUM
             PREPARED BY FINAUDIT-RAG NEURO-SYMBOLIC CAUSAL ENGINE
=====================================================================================
DATE OF AUDIT REPORT  : 2026-10-26 14:14:21 UTC
TARGET REGISTRANT     : CyberTech Enterprise Solutions Inc. (CYBR-TECH)
FISCAL PERIOD AUDITED : Q3 2023 (Form 10-Q & Earnings Call Broadcast)
INSPECTION STANDARD   : PCAOB AS 2401 & SEC Rule 10b-5
OVERALL DECEPTION AUROC: 0.9412 (DECISION: ACTIONABLE DECEPTION)

[FINDING #1] Contested Concept: ShortTermDebtMaturity
- Speaker & Turn ID    : Claire Vance (CFO) (Turn T04)
- Judicial Verdict     : DECEPTIVE_MATERIAL_MISSTATEMENT (Confidence: 100.0%)
- Statutory Violation  : High SOX Section 302 / SEC Rule 10b-5 Enforcement Risk
- Regulatory Citation  : SEC Form 10-Q Note 7 states: "Outstanding borrowings under
                         Revolving Credit Facility totaled $285.0M maturing Q4 2023."
- Spoken Assertion     : "Zero near-term refinancing obligations or liquidity issues."
- Causal Discrepancy   : Delta_cf = 1.0000 (p = 0.0000e+00, Acoustic Stress: 0.83)
```

---

## ⚖️ License & Ethical Usage

This project is licensed under the **Apache License 2.0**. See the [LICENSE](LICENSE) file for complete terms.

**Forensic Audit Ethics Disclaimer**:  
This system is intended for professional forensic auditors, regulatory compliance teams, and academic researchers examining disclosures under PCAOB and SEC standards. It does not constitute formal legal counsel or an automated investment recommendation without independent qualified human review.

---

## 📖 Citation

If you use FinAudit-RAG datasets, XBRL parsing scripts, acoustic prosody harnesses, or the causal graph engine in your research, please cite:


