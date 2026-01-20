# PhD Radiomics Sandbox 🧪

## Project Overview
This repository serves as the **experimental laboratory** (sandbox) for my PhD research in **Prostate Cancer Radiomics**. 
It contains prototype pipelines, exploratory data analysis (EDA), and "dry run" scripts designed to test hypotheses before deployment in production environments.

**Focus Areas:**
- Longitudinal MRI Analysis (Delta Radiomics)
- Image Preprocessing & Standardization (SimpleITK)
- Feature Extraction (PyRadiomics)
- Predictive Modeling (Toxicities & Treatment Efficacy)

## ⚠️ Disclaimer
**Experimental Code:** The code within this repository is volatile and subject to frequent changes. It is intended for research validation and prototyping purposes only.
**Not for Clinical Use:** None of the algorithms or models in this repository are intended for direct clinical diagnosis or decision-making.

## Data Privacy Protocol
Strict adherence to GDPR and ethical guidelines:
- **No Patient Data:** This repository does **not** contain any DICOM, NIfTI, or private clinical metadata.
- **External Data:** Scripts are designed to point to external, secure local directories (e.g., `02_Data/`) or use public datasets (e.g., ProstateX) for validation.
- **Separation of Concerns:** Data and Code are strictly decoupled to prevent leakage.

## Structure
- `ExpXX_Name/`: Self-contained experimental modules.
- `notebooks/`: Jupyter notebooks for visual validation and plotting.
- `src/`: Reusable python modules for data loading and processing.

---
*Maintained by Giacomo Da Re, PhD Candidate in Universidad de Navarra*