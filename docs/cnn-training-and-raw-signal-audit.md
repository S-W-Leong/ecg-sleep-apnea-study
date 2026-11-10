# CNN training curves and raw signal audit — 10 November 2026

This post-evaluation investigation uses saved histories and source recordings; it does not retrain models, change thresholds, remove windows or replace the frozen evaluation. [Notebook 11](../notebooks/11_cnn_curves_and_raw_signals.ipynb) is the reproducible analysis. It complements the [implementation audit](cnn-implementation-audit.md) and [nested results](portfolio-nested-results.md). Subject identities remain unverified; this is retrospective exploratory research.

## What the selected learning curves show

All 15 selected calibration histories reproduce the frozen stopping rule: unweighted stopping BCE must improve by more than 0.0001, with patience eight. The saved refits have exactly the selected number of epochs. The final outer epoch schedules are 1, 1, 3, 2 and 1.

Seven of 15 calibration runs selected epoch 1. All 15 reached their eight-epoch non-improvement patience limit. Training BCE decreased from the first to final observed epoch in every run, while final stopping BCE exceeded its selected minimum in every run. This is consistent with fitting the training groups while generalizing poorly to stopping groups, not an off-by-one stopping bug. In the class-weighted fold, absolute training and stopping BCE levels are not directly comparable because their weighting differs.

| Display fold | Selected calibration epochs | Observed calibration epochs | Outer refit epochs |
| --- | --- | --- | ---: |
| 1 | 1, 1, 2 | 9, 9, 10 | 1 |
| 2 | 1, 12, 1 | 9, 20, 9 | 1 |
| 3 | 4, 3, 1 | 12, 11, 9 | 3 |
| 4 | 2, 5, 2 | 10, 13, 10 | 2 |
| 5 | 23, 1, 1 | 31, 9, 9 | 1 |

Examples:

- Fold 2 / inner 1: training loss 0.573 → 0.391, stopping loss 0.758 → 2.106; selected epoch 1.
- Fold 2 / inner 2: stopping loss improved from 0.654 to 0.399; selected epoch 12.
- Fold 5 / inner 1: stopping loss improved from 0.646 to 0.465; selected epoch 23. The other two inner histories selected epoch 1, producing an outer median of 1.

These differences make a single stable training duration implausible on the available evidence. They do not show that simply increasing patience or imposing more epochs would improve held-out performance: the observed extra epochs frequently worsened stopping BCE. Stopping BCE targets probability loss whereas hyperparameter selection targets AP; ranking could behave differently, but per-epoch stopping AP was not saved. No causal conclusion about that objective mismatch is possible from these histories alone.

The median schedule is faithful to the protocol but compresses markedly different inner histories to a very short outer refit. That is a modeling/protocol limitation worth testing in a separately specified development experiment, not a reason to retroactively change these outer predictions.

## Tracing near-flat minutes

The 17 minutes with filtered standard deviation below the 0.001 mV normalization floor were traced to seven original WFDB recordings: a17 (1), b04 (2), c01 (2), c02 (4), c04 (3), c09 (3), c10 (2). All 17 have exactly constant original digital samples, not merely small ECG amplitude. Saved raw physical samples match original WFDB decoding. The signal contains no within-minute waveform variation before the filter is applied.

Source dat/header/annotation checksums match the recorded Phase 1 source hashes. Whole-record filtering was independently reconstructed with the recorded fourth-order 0.5–40 Hz Butterworth SOS filter at 100 Hz and default zero-phase padding. Reconstructed filtered arrays match saved arrays. The A/N source annotations at the minute boundaries match the retained binary labels for all 17 minutes.

All 17 were flagged as flat/low-amplitude and retained under the explicitly documented Phase 1 policy to keep complete finite windows with descriptive quality flags. They are not newly introduced cache corruption. Sixteen are labeled non-apnea and one apnea. A clinical-looking source annotation does not guarantee that the ECG waveform is informative in that minute.

A constant source baseline is removed by bandpass filtering; small residuals can reflect surrounding transitions and filter decay. This is expected filter behavior rather than evidence that the filter erased valid ECG in those intervals. The physical cause of the constant source segments (for example acquisition dropout) is unverified; do not diagnose it from plots alone. The audit covers these seven recordings and intervals, not an exhaustive signal-quality validation of the database.

These windows constitute approximately 0.10% of the cohort. Their existence is a real data-quality issue, but does not establish that they caused the large overall performance gaps or the all-positive folds. No exclusions or replacement performance scores were computed.

## Interpretation and next work

The evidence favors two distinct issues:

1. **Training/generalization:** early minima on some stopping groups alongside continuing training-loss reduction; heterogeneous epoch schedules; and permissive inner-F1 thresholds on weakly separated scores. The stopping code behaves as specified, but the chosen procedure does not yield reliable generalization on this cohort.
2. **Source quality:** genuine constant-signal intervals, correctly represented and flagged in preprocessing. They deserve a prospectively specified quality policy, not an unreported cleanup chosen to improve the evaluated score.

No preprocessing fix or stopping change is justified as a proven remedy yet. A useful next development experiment would record per-epoch training and stopping AP/AUC/BCE, class-specific score distributions and group metrics, then compare a small set of prespecified stopping/epoch policies. Quality handling should be defined from source signal properties without reference to model success. Any changes motivated by this audit remain exploratory on the exposed cohort; an independent cohort with verified identities is needed for stronger evidence.

## Reproduction and artifacts

Run Notebook 11 in the project environment. It verifies frozen waveform/result hashes, reconstructs stopping decisions, verifies source file hashes, decodes original WFDB digital/physical samples, reconstructs whole-record filtering, checks source annotation alignment and exports all diagnostics. It creates a new timestamped directory under ignored `reports/portfolio-v2/cnn-curves-raw/` with:

- `selected_calibration_curves.png`: all 15 selected calibration histories and epoch choices.
- `near_flat_raw_context.png`: all 17 source/filtered intervals with neighboring context.
- `selected_curves.csv`, `outer_training.csv`, `near_flat_trace.csv`, `filter_reconstruction.csv`.

The successful executed notebook and HTML walkthrough are under `reports/portfolio-v2/cnn-curves-raw/executed-20261110-v4/`. Earlier interrupted/failed diagnostic attempts are preserved separately; those were audit-development errors and did not affect the completed model search. Source notebooks are saved without outputs. No new public release or independent review is claimed.
