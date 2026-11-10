# Frozen nested evaluation results

**Completed experiment:** real-20261109-v1. **Report date:** 10 November 2026.
**Scope:** retrospective exploratory research; not a clinical diagnostic system.

## Executive interpretation

RR-feature logistic regression achieved the highest observed mean outer-fold AP (0.646),
followed by the adapted literature SVM (0.603), XGBoost (0.540), random forest (0.502),
and the original 100 Hz CNN (0.474). This is a comparison of these tested pipelines,
not evidence of universal superiority. Threshold transfer and between-fold variation
are substantial weaknesses. The CNN predicted every window positive in two folds.

## Design and provenance

34 recordings, 16,558 one-minute windows (6,508 positive; 39.3%), and 24 literature-derived
groups from the Apnea-ECG learning cohort; overlapping c05 excluded. Subject identities
remain unverified. Prior test exposure means nested resplitting does not restore a clean
confirmatory holdout. Five outer folds, three inner folds, 24 frozen candidates per pipeline.
Selection uses mean inner AP; thresholds maximize inner out-of-fold F1, lowest threshold on ties.
All learned preprocessing is fitted on training partitions. CNN stopping uses groups inside
inner training, followed by fresh initialization and refitting; outer labels do not choose epochs.
The CNN retains 3,009 parameters, 100 Hz and 6,000 samples/minute. Classical F2 models
use six RR features; the literature adaptation uses 11 local RR features. This compares
feature/model pipelines rather than isolating classifier architecture alone.

Freeze identity: `1765caa330e2136b1f16f61828fae0a568bcc36b0730bd3b2cfd9b3d7e2f1363`.
Runner SHA-256: `b3b1a8c4fb58e6abdd6a3c547a7375061dc47f63ccf1e81fdb9809d8af42997d`.
Results manifest status: complete; 140 artifact hashes verified.
All five folds, repeat seeds, fixed ablations, and exports completed; 886 checkpoint tasks
finished with no recorded failures. Recorded fit warnings were SVC parameter deprecations,
not convergence or numerical failures. Completion is computational evidence, not proof
of scientific validity. See [runner](nested-evaluation-runner.md),
[protocol](portfolio-evaluation-protocol.md), and
[literature verification](literature-baselines.md).

## Primary and secondary metrics

| model | mean_fold_ap | fold_sd | pooled_ap | pooled_auc | pooled_f1 |
| --- | --- | --- | --- | --- | --- |
| logistic_regression | 0.646 | 0.137 | 0.594 | 0.708 | 0.568 |
| linear_svm | 0.603 | 0.171 | 0.560 | 0.684 | 0.569 |
| xgboost | 0.540 | 0.136 | 0.508 | 0.630 | 0.539 |
| random_forest | 0.502 | 0.098 | 0.499 | 0.633 | 0.540 |
| cnn | 0.474 | 0.101 | 0.432 | 0.548 | 0.523 |

Primary: unweighted mean outer-fold AP. SD describes five folds, not a confidence interval.
Pooled AP/AUC/F1 are separate secondary summaries across models fitted on different partitions.
AP is not accuracy. Mean fold constant-score AP is 0.395; pooled prevalence is 0.393.
Logistic regression exceeds CNN by 0.172, SVM by 0.043, and XGBoost by 0.106 mean AP.
These observed differences alone do not establish all pairwise superiority claims.

## Fold variability

| model | fold_1 | fold_2 | fold_3 | fold_4 | fold_5 |
| --- | --- | --- | --- | --- | --- |
| logistic_regression | 0.662 | 0.476 | 0.856 | 0.614 | 0.623 |
| linear_svm | 0.633 | 0.438 | 0.849 | 0.651 | 0.444 |
| xgboost | 0.633 | 0.518 | 0.720 | 0.437 | 0.392 |
| random_forest | 0.459 | 0.535 | 0.657 | 0.448 | 0.408 |
| cnn | 0.366 | 0.486 | 0.406 | 0.631 | 0.483 |

Display fold numbers are 1–5; artifact IDs are 0–4. LR AP spans 0.476–0.856;
CNN AP spans 0.366–0.631. Model ordering changes across folds: pooled or mean scores
must not hide cohort heterogeneity. Folds have different prevalences; their training
sets overlap, so five fold scores are not five independent experiments.
Notebook 09 plots every fold and specificity at each operating point.

## Threshold failures

Every threshold was selected on inner predictions, not held-out labels. Nonetheless,
it may transfer poorly. The full primary-seed diagnostic table follows; positive_rate
is the fraction of outer windows called positive. All-positive calls have zero specificity.

| model | threshold | positive_rate | prevalence | sensitivity | specificity | f1_score | fold_number |
| --- | --- | --- | --- | --- | --- | --- | --- |
| cnn | 0.425 | 0.758 | 0.319 | 0.994 | 0.353 | 0.590 | 1 |
| cnn | 0.287 | 0.407 | 0.383 | 0.551 | 0.682 | 0.535 | 2 |
| cnn | 0.369 | 0.267 | 0.468 | 0.154 | 0.634 | 0.197 | 3 |
| cnn | 0.247 | 1.000 | 0.399 | 1.000 | 0.000 | 0.571 | 4 |
| cnn | 0.240 | 1.000 | 0.407 | 1.000 | 0.000 | 0.579 | 5 |
| linear_svm | -2.928 | 0.999 | 0.319 | 1.000 | 0.002 | 0.485 | 1 |
| linear_svm | -1.034 | 0.828 | 0.383 | 0.852 | 0.186 | 0.539 | 2 |
| linear_svm | -0.852 | 0.719 | 0.468 | 0.977 | 0.508 | 0.771 | 3 |
| linear_svm | -0.736 | 0.337 | 0.399 | 0.549 | 0.803 | 0.595 | 4 |
| linear_svm | -0.736 | 0.389 | 0.407 | 0.439 | 0.645 | 0.449 | 5 |
| logistic_regression | 0.174 | 0.946 | 0.319 | 0.994 | 0.076 | 0.502 | 1 |
| logistic_regression | 0.243 | 0.887 | 0.383 | 0.901 | 0.122 | 0.543 | 2 |
| logistic_regression | 0.317 | 0.809 | 0.468 | 0.980 | 0.341 | 0.718 | 3 |
| logistic_regression | 0.321 | 0.343 | 0.399 | 0.529 | 0.780 | 0.568 | 4 |
| logistic_regression | 0.411 | 0.228 | 0.407 | 0.367 | 0.868 | 0.471 | 5 |
| random_forest | 0.000 | 1.000 | 0.319 | 1.000 | 0.000 | 0.484 | 1 |
| random_forest | 0.063 | 0.902 | 0.383 | 0.967 | 0.138 | 0.577 | 2 |
| random_forest | 0.358 | 0.728 | 0.468 | 0.909 | 0.431 | 0.711 | 3 |
| random_forest | 0.336 | 0.322 | 0.399 | 0.375 | 0.713 | 0.415 | 4 |
| random_forest | 0.374 | 0.422 | 0.407 | 0.445 | 0.593 | 0.437 | 5 |
| xgboost | 0.066 | 1.000 | 0.319 | 1.000 | 0.000 | 0.484 | 1 |
| xgboost | 0.001 | 1.000 | 0.383 | 1.000 | 0.000 | 0.554 | 2 |
| xgboost | 0.243 | 0.766 | 0.468 | 0.949 | 0.394 | 0.719 | 3 |
| xgboost | 0.284 | 0.327 | 0.399 | 0.370 | 0.702 | 0.407 | 4 |
| xgboost | 0.277 | 0.421 | 0.407 | 0.470 | 0.612 | 0.462 | 5 |

CNN folds 4 and 5 are all-positive; RF fold 1 and XGBoost fold 1 also are all-positive.
Other folds are near-degenerate (e.g. XGBoost fold 2 specificity 0.0004).
A CNN F1 near 0.57 in an all-positive fold is not useful discrimination at that operating point.
CNN pooled AUC is only 0.548. Poor threshold transfer is consistent with group-related
score/distribution shifts or an unsuitable transferred operating point; these outputs do
not establish the cause. Thresholds have not been repaired using outer labels.

## Repeat seeds

| model | 67 | 167 | 267 |
| --- | --- | --- | --- |
| logistic_regression | 0.646 | nan | nan |
| linear_svm | 0.603 | nan | nan |
| xgboost | 0.540 | 0.540 | 0.541 |
| random_forest | 0.502 | 0.503 | 0.502 |
| cnn | 0.474 | 0.487 | 0.476 |

RF and XGBoost mean AP change little across seeds. CNN mean AP is 0.474–0.487,
so repeats do not reverse its overall position. These seeds refit selected settings and
epoch schedules; they do not repeat hyperparameter selection, add independent people,
or constitute an ensemble. Small seed spread does not resolve large cohort variability.

## Tuning and fixed feature ablations

| model | fixed_F2 | tuned_F2 | difference |
| --- | --- | --- | --- |
| logistic_regression | 0.650 | 0.646 | -0.003 |
| random_forest | 0.507 | 0.502 | -0.005 |
| xgboost | 0.531 | 0.540 | 0.009 |

Tuning does not consistently improve held-out AP: the selected inner optimum need not
be the outer optimum. Retain both prespecified analyses; do not choose the better outer
version afterward. The bounded search makes selection more transparent without claiming
globally optimal hyperparameters.

| model | A_F1 | B_F2 | C_no_SDRR | D_no_RMSSD | E_no_pRR50 |
| --- | --- | --- | --- | --- | --- |
| logistic_regression | 0.401 | 0.650 | 0.357 | 0.521 | 0.668 |
| random_forest | 0.400 | 0.507 | 0.355 | 0.489 | 0.519 |
| xgboost | 0.390 | 0.531 | 0.363 | 0.503 | 0.545 |

F1 has basic mean/median RR and mean HR; F2 adds SDRR, RMSSD and pRR50.
Fixed F2 improves over F1 in all three models. Removing SDRR causes the largest
performance loss among tested removals. Removing pRR50 modestly improves all three;
this suggests limited incremental value here, not physiological causality. These are
fixed-setting ablations, not independently retuned feature subsets or a revised primary model.

## Conditional uncertainty

| comparison | estimate | lower | upper | valid_draws |
| --- | --- | --- | --- | --- |
| cnn | 0.076 | -0.074 | 0.236 | 2000 |
| linear_svm | -0.052 | -0.133 | 0.037 | 2000 |
| logistic_regression | -0.086 | -0.164 | -0.008 | 2000 |
| random_forest | 0.009 | -0.023 | 0.063 | 2000 |

Differences are **XGBoost minus comparator pooled AP**, with 2,000 paired whole-group
bootstrap draws; percentile 95% intervals condition on fixed cross-fitted predictions.
They exclude full training/tuning uncertainty and are not multiplicity-adjusted.
XGBoost minus LR excludes zero in the negative direction, offering conditional exploratory
evidence favoring LR. The CNN, RF and SVM comparison intervals cross zero.
These are not intervals for the primary mean-fold AP. No direct LR–CNN or LR–SVM
interval is supplied; do not infer those comparisons from the XGBoost intervals.

## Literature baseline and limits of comparison

The linear SVM adapts Almazaydeh et al. (2012): local RR features are calculated on
60-second windows, recording-wide summaries are omitted, and original author code/weights
are not used. It is a literature-derived adaptation, not an exact reproduction or human
baseline. Its AP of 0.603 makes it a meaningful competitor here; differing source protocols
prevent direct comparisons with published headline scores. See the source receipt and
adaptation details linked above.

## Honest limitations and portfolio claims

- Patient identities are unverified; use “literature-derived grouped evaluation,” not verified
  patient-independent evaluation.
- Only 24 groups from 34 recordings; correlated minutes do not yield thousands of independent
  participants.
- Prior cohort/test exposure remains; the nested rerun is exploratory, not a clean confirmatory
  test.
- Large fold variability and weak specificity at transferred thresholds limit practical
  generalization.
- One small fixed CNN architecture and finite training searches cannot represent all deep
  learning methods.
- Different feature representations mean this is a pipeline comparison, not an isolated
  architecture experiment.
- Conditional intervals and seed repeats cover limited uncertainty; no external cohort or
  clinical validation exists.
  sampling-rate effect.
- The full comparison's serving/end-to-end inference cost has not yet been benchmarked;
  historical costs are not substitutes.

A defensible portfolio statement is: “Built a reproducible, frozen grouped nested comparison
of RR-feature classifiers, an adapted literature SVM, and an original 100 Hz CNN. A simple
logistic model led the tested pipelines, while fold variability and threshold failures exposed
important limits to generalization.” Do not claim state-of-the-art, human-level, clinical,
universally superior, or definitively patient-independent performance.

Next steps are group/quality diagnostics, clearly specified operating-point objectives,
and independent evaluation with verified identities. Modeling changes motivated by these
outer results require a new exploratory experiment and ideally an untouched cohort.

## Reproduction and relationship to historical work

Run [Notebook 09](../notebooks/09_nested_results.ipynb) with the project environment.
It verifies every saved result hash, checks prediction coverage, independently recomputes
primary fold metrics, displays plots/tables, and exports a copy of this report plus CSVs
and figures into a fresh timestamped directory under ignored reports/portfolio-v2/.
No models are fitted and no thresholds are reselected. Generated artifacts remain ignored;
this tracked report retains the main tables for readers without local data.

Input artifacts: data/processed/portfolio-v2/plan001-real-20261108/full/real-20261109-v1/results/.
The [final study report](final-study-report.md) synthesizes these findings for readers;
this file retains detailed evidence from the nested evaluation.

## Post-evaluation implementation audit

The [CNN audit](cnn-implementation-audit.md) and [Notebook 10](../notebooks/10_cnn_implementation_audit.ipynb) reconstruct all cached minutes and replay all saved CNN predictions exactly. They reveal that the failing folds already had permissive inner thresholds and very short outer refits; distribution shift alone is not an established explanation. Near-flat inputs warrant upstream quality review. No frozen metrics or thresholds were changed.

The [learning-curve and raw-signal follow-up](cnn-training-and-raw-signal-audit.md) confirms that the near-flat intervals were already constant in the source digital samples and flagged in Phase 1. Reconstructed selected stopping decisions agree with saved epochs; training/stopping divergence remains a substantive generalization concern, not a demonstrated stopping-counter bug.
