# Earnings Call Multimodal Dataset

## Overview

This dataset contains multimodal earnings call data organized by company, year, and fiscal quarter.

Each earnings call includes:

- audio.mp3 — audio recording of the call
- transcript.csv — transcript aligned with the call
- LEVEL_3.json — intermediate structured representation
- LEVEL_4.json — processed multimodal representation

## Directory structure

Inside each yearly archive the structure is:

companies/
  TICKER/
    YEAR/
      QX/
        audio.mp3
        transcript.csv
        LEVEL_3.json
        LEVEL_4.json

Example:

companies/AAPL/2024/Q2/
  audio.mp3
  transcript.csv
  LEVEL_3.json
  LEVEL_4.json

## Dataset contents

- Companies: ~200
- Years: 2018–2024
- Earnings calls: ~8100
- Total compressed size: ~114 GB

Archives:

dataset_2018.zip  
dataset_2019.zip  
dataset_2020.zip  
dataset_2021.zip  
dataset_2022.zip  
dataset_2023.zip  
dataset_2024.zip  

## Metadata

The file `metadata.csv` provides a global index of all calls and their locations.

Fields include:

- company
- year
- quarter
- audio_path
- transcript_path
- level3_path
- level4_path

## Code

The code used to process this dataset is available at:
https://github.com/jordieres/earnings-call-multimodal-framework

## Citation

The dataset used in this study is publicly available on Zenodo and linked to the EU-Funded Research community.
If you use this dataset, please cite:
Álvarez Castro, A. and Ordieres-Meré J. (2026). Multimodal Earnings Call Dataset (2018–2024).
Zenodo. https://doi.org/10.5281/zenodo.19030119
