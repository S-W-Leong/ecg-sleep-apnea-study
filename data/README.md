# Data provenance and attribution

Source: PhysioNet Apnea-ECG Database, version 1.0.0, https://physionet.org/content/apnea-ecg/1.0.0/.
DOI: https://doi.org/10.13026/C23W2R.

This bundle contains the 34 analyzed learning-set recordings: a01-a20, b01-b05, c01-c04 and c06-c10. c05 is excluded because it overlaps c06. It does not claim to redistribute the complete database or the separate challenge test cohort. Each included record has its original `.dat`, `.hea` and `.apn` files. `RECORDS` lists the included subset; the provider's full `SHA256SUMS.txt` is retained unchanged. Source file hashes are checked by START_HERE and the preparation manifest.

**Dataset license:** Open Data Commons Attribution License v1.0 (ODC-By). The full text is in `LICENSES/ODC-By-1.0.txt` at the repository root; the authoritative provider terms are https://physionet.org/content/apnea-ecg/view-license/1.0.0/. The repository's MIT license applies to original software and associated original documentation, not to these third-party data. Keep this attribution and the provider terms with redistributed data and derived databases.

Cite:

- Penzel T, Moody GB, Mark RG, Goldberger AL, Peter JH. The Apnea-ECG Database. Computers in Cardiology. 2000;27:255-258.
- Pollard T, Moody BE, Lehman L, et al. PhysioNet as a global platform for biomedical research. Nature Health. 2026;1:792-795. https://doi.org/10.1038/s44360-026-00096-z.

Processed files are study-derived representations of this database: retained minute/label tables, quality flags, detected peaks/RR intervals, engineered features, grouped assignments and evaluation outputs. Processing and exclusions are documented in the final report. No new patient identities are asserted. These public research data and models must not be interpreted as a clinical diagnostic service.

The optional prepared-waveform archive contains raw and filtered mV arrays derived from these same recordings, preserving the exact evaluated binary hashes. It retains the same source attribution; it adds no additional subjects or modalities.
