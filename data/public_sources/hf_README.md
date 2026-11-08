---
license: mit
language:
  - en
pretty_name: "S&P 500 Earnings Call Transcripts (2005-2025)"
tags:
  - finance
  - earnings
  - transcripts
  - sp500
  - stocks
  - text
datasets:
  - kurry/sp500_earnings_transcripts
task_categories:
  - text-generation
  - text-classification
size_categories:
  - 10M<n<100M
date: "2025-05-19"
---
# S&P 500 Earnings Transcripts Dataset

This comprehensive dataset contains earnings call transcripts for S&P 500 companies and US large-caps, spanning from 2005 to 2025. Earnings calls provide valuable insights into company performance, strategic initiatives, and management perspectives that are essential for financial analysis, natural language processing research, and market sentiment studies.

## Dataset Description

This collection includes:

- **Complete transcripts**: Full verbatim records of quarterly earnings calls for S&P 500 constituents and related large-cap US companies
- **Structured dialogues**: Organized speaker-by-speaker segmentation allowing for detailed conversation analysis
- **Rich metadata**: Comprehensive company information including ticker symbols, company names, unique identifiers, and temporal data
- **Extensive coverage**: Over 33,000 unique transcripts across 685 companies and more than two decades

## Data Structure

Each transcript record contains the following fields:

| Field                | Type    | Description                                                     |
|----------------------|---------|-----------------------------------------------------------------|
| `symbol`             | string  | Stock ticker symbol (e.g., "AAPL")                              |
| `company_name`       | string  | Full company name (e.g., "Apple Inc.")                          |
| `company_id`         | float   | Capital IQ Company identifier                                   |
| `year`               | integer | Fiscal year of the earnings call                                |
| `quarter`            | integer | Fiscal quarter (1-4)                                            |
| `date`               | string  | Earnings call date in YYYY-MM-DD HH:MM:SS format                |
| `content`            | string  | Complete raw transcript text                                    |
| `structured_content` | object  | Array of `{speaker, text}` objects segmenting the dialogue      |

## Coverage and Distribution

The dataset provides extensive temporal coverage with transcript counts increasing significantly after 2007:

- **Total companies:** 685  
- **Total transcripts:** 33,362  
- **Year range:** 2005–2025  
- **Quarter range:** 1–4  
- **Example company tickers:** MCHP, INFO, HCA, NEM, ERIE, ZBRA, GD, PSA, DLR, STI

### Transcript Length Statistics

- Characters per transcript: min=0, median=53,734, max=244,695

### Top Companies by Transcript Count
- Akamai Technologies, Inc.: 78 transcripts
- AutoZone, Inc.: 78 transcripts
- Biogen Inc.: 78 transcripts
- Broadcom Inc.: 78 transcripts
- Adobe Inc.: 78 transcripts
- Amazon.com, Inc.: 78 transcripts
- Amgen Inc.: 77 transcripts
- The Boeing Company: 76 transcripts
- Automatic Data Processing, Inc.: 76 transcripts
- Applied Materials, Inc.: 76 transcripts

### Transcript Count by Year

```
2005: 67     | 2010: 1322  | 2015: 1814  | 2020: 2210
2006: 358    | 2011: 1556  | 2016: 1899  | 2021: 2170
2007: 927    | 2012: 1710  | 2017: 1946  | 2022: 2110
2008: 1489   | 2013: 1765  | 2018: 1969  | 2023: 2079
2009: 1497   | 2014: 1780  | 2019: 2014  | 2024: 2033
                                         | 2025: 647 (partial)
```

## S&P 500 Coverage

As of May 2025, this dataset includes transcripts from all major S&P 500 constituents and primary equity listings. Some companies have multiple share classes but only the primary class is typically included in earnings calls.

The dataset includes transcripts from companies across all 11 GICS sectors:
- Information Technology
- Health Care
- Financials
- Consumer Discretionary
- Industrials
- Communication Services
- Consumer Staples
- Energy
- Utilities
- Real Estate
- Materials

### Sample Companies

```
A     – Agilent Technologies, Inc.
AAPL  – Apple Inc.
ABBV  – AbbVie Inc.
ABNB  – Airbnb, Inc.
ABT   – Abbott Laboratories
…
XOM   – Exxon Mobil Corporation
XYL   – Xylem Inc.
YUM   – Yum! Brands, Inc.
ZTS   – Zoetis Inc.
```
## Typical Transcript Structure

Most earnings call transcripts follow a standard format:
1. **Call introduction**: Operator remarks and standard disclaimers
2. **Management presentation**: Prepared remarks from executives (typically CEO and CFO)
3. **Q&A session**: Analyst questions and management responses
4. **Call conclusion**: Closing remarks and end of call notification

The `structured_content` field makes it possible to analyze these distinct sections separately for more nuanced research.

## Usage Examples

```python
from datasets import load_dataset

# Load the dataset
ds = load_dataset("kurry/sp500_earnings_transcripts")

# Inspect a sample record
rec = ds["train"][0]
print(rec["symbol"], rec["company_name"], rec["date"], "Q"+str(rec["quarter"]), rec["year"])
for seg in rec["structured_content"][:3]:
    print(seg["speaker"], ":", seg["text"][:80], "…")
```

```python
# Filter Apple transcripts from 2022
apple_2022 = ds["train"].filter(lambda x: x["symbol"]=="AAPL" and x["year"]==2022)
print("Apple 2022 count:", len(apple_2022))
```

## Citation

```
@dataset{kurry2025sp500earnings,
  author    = {Kurry},
  title     = {S&P 500 Earnings Transcripts Dataset},
  year      = {2025},
  publisher = {Hugging Face},
  url       = {https://huggingface.co/datasets/kurry/sp500_earnings_transcripts}
}
```

## License & Limitations

Licensed under MIT. For research and educational use only.
