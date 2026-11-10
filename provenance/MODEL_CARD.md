# Included models

These are the 25 primary seed-67 models used to produce the main grouped nested evaluation: five outer folds for each tuned pipeline. No additional fitting was performed for this distribution. The full selected settings, thresholds and CNN epoch counts are retained in the results table.

| Pipeline | Representation | Input | Output | Serialization |
| --- | --- | --- | --- | --- |
| Logistic regression | F2 RR features | six features, with fit-only imputation/scaling in the saved pipeline | positive-class probability | sklearn pickle |
| Random forest | F2 RR features | six features, with saved imputation | positive-class probability | sklearn pickle |
| XGBoost | F2 RR features | six features, with saved imputation | positive-class probability | sklearn/XGBoost pickle; isolated process only |
| Adapted linear SVM | local RR feature adaptation | eleven features in specifications.json order, with saved imputation/scaling | uncalibrated decision score | sklearn pickle |
| CNN | filtered ECG | float32 (batch, 1, 6000), per-minute normalization at 100 Hz | sigmoid score | torch state dictionary |

F2 order: mean_rr_ms, median_rr_ms, mean_hr_bpm, sdrr_ms, rmssd_ms, prr50_pct. Clinical NN processing has not been established. Do not substitute missing features with zeros; use the saved fitted preprocessing pipeline. The CNN architecture is the exact `make_cnn` definition in Notebook 07 (3,009 parameters). Scores are not established as calibrated probabilities; a sigmoid output alone does not establish calibration.

Use each model only with its corresponding feature representation and preprocessing. Cross-validated performance must be replayed on the matching held-out fold. There is no single globally selected/full-cohort deployment model here. Threshold failures, group variability, identity limitations and the lack of clinical/external validation are documented in the final report. These weights are for study inspection and research reproduction, not diagnosis.

Model hashes are in the curated results manifest and `provenance/bundle-manifest.json`. Only load trusted pickle files after verifying hashes. XGBoost's process-isolation requirement is documented in REPRODUCING.md. The pinned environment is defined in uv.lock; a different environment may not deserialize sklearn objects compatibly.
