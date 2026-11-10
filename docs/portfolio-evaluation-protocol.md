# Portfolio evaluation protocol v2.0 — draft

Prepared 2026-11-08. **Exploratory retrospective internal evaluation.** Original patient identities are unavailable; subject groups come from a published mapping. Earlier test outcomes were inspected. Nested evaluation does not reverse that exposure or establish patient independence. This is not clinical validation.

## Cohort and labels

Use all 34 prepared recordings and 16,558 complete labeled one-minute windows, retaining quality-flagged and feature-missing windows. Exclude the previously documented overlapping c05 recording. Keep the existing 24 literature-derived subject groups. Preserve source labels: apnea status at the beginning of the associated minute, not a guarantee of events anywhere in that minute. Do not derive clinical AHI from these annotations.

Notebook 05 checks the raw feature table against the cohort keys and labels. Raw feature values remain unimputed until a fitting fold is known. Signals remain retrospectively filtered; CNN input in the next implementation phase will use the fixed existing architecture and 100 Hz / 6,000 samples per minute.

## Evaluation and selection

- Five StratifiedGroupKFold outer folds, shuffled with seed 67; every group is held out exactly once.
- Three inner grouped folds within each outer-training partition, seed 167 + outer fold. Shared assignments across models and seeds.
- CNN epoch calibration uses four grouped subfolds within each inner-training partition, seed 267 + 10 × outer fold + inner fold. Subfold zero is the stopping subset; the other subfolds fit the calibration model. Inner validation and outer test never provide stopping feedback.
- Fit imputation, scaling, learned transformations and class-weight ratios on the current fitting data only. Deterministic label-independent signal transformations may be cached within recordings.
- Select candidate settings by mean inner-fold average precision. Differences within 1e-12 choose the earlier persisted candidate. No outer score selects methods, hyperparameters, checkpoints, thresholds, seeds, or feature sets.
- Select each threshold by maximum F1 on the selected configuration's inner out-of-fold scores; lowest threshold wins ties. Thresholds may use decision scores and do not imply calibrated probability.
- Refit only after selection. Primary training seed 67; seeds 167 and 267 are secondary reproducibility checks, with no best-seed selection or implicit ensemble.

## Questions and estimands

RQ1 keeps Phase 2 settings fixed across the five feature sets: LR C=1/max_iter=1000; RF 200 trees/depth 8/min_samples_leaf 5; XGBoost 200 trees/depth 3/learning_rate .05/subsample 1/colsample_bytree 1. Refit each model and its preprocessing for every feature set. Apply the same inner threshold procedure to each.

RQ2 tunes full F2 classical pipelines versus the existing compact CNN with its fixed architecture and original sampling rate. This compares representations and training procedures, not solely classifier choice. Literature methods and their adaptations must be finalized in Plan 002 before inclusion.

Primary result: arithmetic mean of five outer-fold average-precision scores (scikit-learn average_precision_score, not trapezoidal PR integration). Display each fold and paired fold differences. Fold standard deviation is descriptive, not a confidence interval.

Secondary results: pooled outer out-of-fold average precision, ROC-AUC, sensitivity, specificity, precision, F1, accuracy and confusion counts. Each outer prediction uses its own training-selected threshold. Keep pooled and mean-fold estimands distinct. Include per-record and per-group counts and prevalence; single-class groups have missing AP/ROC-AUC with a stated reason. Group-level summaries and pooled window-weighted results require explicit denominators.

For differences in pooled metrics, resample whole groups jointly across methods, using multiplicity weights, 2,000 draws and seed 20261108. Report percentile limits 2.5/97.5 only if at least 1,000 draws contain both classes, and report skipped draws. These approximate intervals are conditional on fixed cross-fitted predictions and exclude full tuning/training uncertainty. Do not count windows, folds or repeated seeds as independent people; do not use naive minute-level significance tests.

## Reproduction and artifact contract

Run notebooks/05_evaluation_protocol.ipynb after Notebooks 00–02. APNEA_PORTFOLIO_RUN selects the run root; relative paths resolve against the project root. The default is data/processed/portfolio-v2/protocol-20261108. APNEA_RUN, APNEA_SPLIT_RUN and APNEA_PHASE2_RUN can select compatible prepared inputs.

The protocol/ subdirectory contains cohort.parquet, fold_assignments.csv, cnn_stop_assignments.csv, protocol.json, metrics.json and manifest.json. The manifest records configuration, input/source hashes, Python/package versions, and output hashes. Writes use a staging directory and atomic rename. Matching reuse verifies hashes; incompatible or corrupt reuse fails instead of replacing results.

APNEA_PORTFOLIO_SMOKE=1 creates 16 synthetic groups with two records and both classes per group, using two outer/inner/stopping folds. Synthetic artifacts are explicitly marked and cannot satisfy the real-run configuration checks. No models are fitted by Notebook 05. Save executed copies under ignored reports/; keep source notebooks output-free.

## Freeze gate and amendments

**Draft:** literature eligibility and search/compute specifications are pending Plans 002–003. Do not label this protocol frozen before those decisions and the timing pilot are complete. Future changes to cohort, groups, metrics, preprocessing or search require a new protocol version and run; do not amend choices in response to outer scores.

- 2026-11-08: initial implementation of cohort, deterministic nested assignments, metrics, conditional paired group bootstrap, artifact checks and offline smoke mode. Prior data exposure and identity limitations remain explicit.

Method references: [grouped validation](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-iterators-for-grouped-data), [nested selection](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html), [dataset source](https://physionet.org/content/apnea-ecg/1.0.0/).
