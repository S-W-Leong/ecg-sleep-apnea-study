# CNN implementation and threshold audit — 10 November 2026

This is a post-evaluation exploratory audit of `real-20261109-v1`, not a new performance estimate or a revised model. No models were retrained, thresholds replaced, or original results modified. Subject identities remain unverified.

## Checks and evidence

[Notebook 10](../notebooks/10_cnn_implementation_audit.ipynb) verifies result hashes and frozen source provenance, reconstructs every input minute, independently replays exported CNN states, recomputes thresholds, and exports group/quality diagnostics. The first executed copy is under `reports/portfolio-v2/cnn-audit/executed-20261110/`; CSVs are under `reports/portfolio-v2/cnn-audit/20261110T024144237746Z/`. Subsequent executions create fresh directories.

- All 140 result artifact hashes and frozen source hashes matched.
- All 16,558 cached minutes matched independently reconstructed filtered-source normalization exactly. Source hashes, 100 Hz rate, 6,000-sample boundaries, minute indices, finite values and float32 shape were checked. This detects cache misalignment, not whether the upstream filter is scientifically optimal.
- All 15 saved CNNs (five folds, three seeds) reproduced saved outer scores with **zero maximum absolute difference**, using an independent forward/sigmoid inference path and key-based sample alignment.
- Primary thresholds for all five pipelines/five folds matched independently recomputed inner OOF maximum-F1 thresholds with the frozen tie rule.
- Saved training and calibration stopping losses were finite. Code inspection found logits fed to BCEWithLogitsLoss, one sigmoid at inference, training mode reset each epoch, training-only positive weights, restored best calibration states, and fresh refits. Existing leakage/reinitialization regression tests provide complementary checks. No new implementation defect was established by this audit; absence of every possible defect is not proven.

## A correction to the threshold explanation

The all-positive CNN folds cannot be attributed solely to scores shifting on unseen groups. The selected thresholds were already permissive on inner OOF predictions:

| Display fold | Threshold | Inner positive rate | Outer positive rate | Selected inner epochs | Outer refit epochs |
| --- | ---: | ---: | ---: | --- | ---: |
| 1 | 0.424929 | 59.5% | 75.8% | 1, 1, 2 | 1 |
| 2 | 0.286781 | 50.8% | 40.7% | 1, 12, 1 | 1 |
| 3 | 0.368988 | 51.7% | 26.7% | 4, 3, 1 | 3 |
| 4 | 0.246968 | 99.98% | 100% | 2, 5, 2 | 2 |
| 5 | 0.240311 | 85.5% | 100% | 23, 1, 1 | 1 |

In fold 4, inner median scores for negatives/positives were 0.378/0.374: very weak separation. Outer medians were 0.385/0.392, both far above the threshold. Fold 5 outer medians were 0.372/0.376, also above its cutoff. A nearly uninformative ranking can make predicting almost everyone positive the best available inner F1 choice. F1 optimization does not impose a minimum specificity.

Fold 1 shows a more obvious shift: the negative median rose from 0.378 inner to 0.629 outer. Fold 3 has a different problem: outer positive scores had a lower median than negatives (0.244 versus 0.267). Thus the failures combine poor ranking, permissive operating-point selection, and mismatches between inner-model and outer-refit score distributions. Pooling OOF predictions combines several fitted models; its threshold need not match the score scale of the final refit even under identical preprocessing. These observations identify mechanisms, not a unique causal explanation.

## CNN training and representation leads

All primary outer refits used only 1–3 epochs under the frozen median-of-calibrated-epochs rule. Some inner schedules were highly inconsistent (1/12/1 and 23/1/1). This is not a coding error: the runner followed the protocol. It raises a substantive question about how well the unweighted stopping BCE and selected epoch schedule support AP ranking and a transferable operating point. The possibility of undertraining remains a hypothesis, not a result of an extended-training comparison.

The fixed convolutional stack has a nominal local receptive field of 113 input samples before global average pooling: about 1.13 seconds at 100 Hz, versus 4.52 seconds at the historical 25 Hz. Global pooling aggregates these local responses across a minute but does not explicitly model long RR sequences. Preserving sample-based kernels preserves the requested architecture, not its physical time scale. This is a representation limitation worth investigating; these results do not prove it caused weak performance.

## Signal-quality lead

17 filtered minutes had standard deviation below the normalization floor of 0.001: a17 (1), b04 (2), c01 (2), c02 (4), c04 (3), c09 (3), c10 (2). Sixteen were labeled non-apnea, one apnea. Some became effectively zero after float32 normalization. These inputs are faithfully cached, so this is a source/quality concern rather than an input-cache corruption. Their small number does not establish that they explain the overall CNN result.

Average clipping fraction was 0.000146 (0.0146% of samples); the largest per-minute fraction was 0.00683 (0.683%). Widespread saturation was not apparent. Inspect raw waveforms, filtering boundaries, quality flags and beat-detection reliability before proposing a new exclusion policy. No windows were removed in this audit.

## Next investigation, without rewriting the evaluation

1. Review selected calibration/refit loss curves and group-specific score distributions, especially folds 3–5. Compare group prevalence and signal quality; group associations are descriptive, not patient-independent causal evidence.
2. Trace near-flat minutes to raw recordings and Phase 1 filtering/quality flags. Full independent review of upstream filtering and label annotation alignment remains outstanding.
3. If warranted, specify a separate development experiment comparing stopping/epoch rules and physically appropriate temporal representations. Do not tune new settings against these outer labels or claim an improvement on them as confirmatory.
4. Specify operating-point goals before another evaluation. Calibration or specificity constraints are prospective hypotheses, not retroactive repairs to the frozen thresholds.

The original results report remains valid as an evaluation of the frozen pipelines. This audit narrows the interpretation: correct execution can still implement a training/selection procedure that generalizes poorly.

## Follow-up: selected curves and raw signals

[Notebook 11](../notebooks/11_cnn_curves_and_raw_signals.ipynb) and its [written findings](cnn-training-and-raw-signal-audit.md) trace all 17 minutes to constant original digital samples, verify original flags and filtering, and reconstruct all 15 selected stopping histories. Seven histories chose epoch 1 while others favored up to 23 epochs; extending observed training often worsened stopping BCE. No model or metric was replaced.
