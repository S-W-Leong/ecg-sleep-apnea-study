# RR feature ablation results

The final controlled RQ1 results use the same five grouped outer folds and fixed classifier settings across all feature sets. See [the final report, RQ1](final-study-report.md#4-results-for-rq1) for the full interpretation.

| Classifier | Basic F1 AP | Expanded F2 AP | Difference |
| --- | ---: | ---: | ---: |
| Logistic regression | 0.401 | 0.650 | +0.248 |
| Random forest | 0.400 | 0.507 | +0.107 |
| XGBoost | 0.390 | 0.531 | +0.141 |

Values are mean outer-fold AP; differences use unrounded values. SDRR had the largest conditional removal effect. See Notebook 09 for fold-local ablations and the original metric tables. The feature-extraction source notebook is retained for method reproducibility; this linked summary describes the final grouped nested results.
