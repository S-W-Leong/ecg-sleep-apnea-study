# Search and compute specifications

Notebook 07 measured development-only fitting cost and serialized the frozen search. The evaluated input contract is the original 3,009-parameter CNN at 100 Hz and 6,000 samples/minute. Candidate budgets are 24 per pipeline. The protocol uses five outer grouped folds, three inner grouped folds and training-only CNN stopping partitions.

Training uses CPU with four estimator/PyTorch threads and search parallelism one. XGBoost is fitted/scored in a fresh process without PyTorch. The saved freeze pins data/source hashes, package/Python/platform versions, candidate settings and order, seed rules, thresholds and epoch rules. Prior test exposure and unverified identities remain limitations.

Read the [reproduction guide](../REPRODUCING.md) before rerunning. Exact source definitions and the original pilot payload are retained for provenance; this scientific method record is not a model-selection result.
