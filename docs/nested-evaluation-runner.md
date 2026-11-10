# Nested evaluation runner

Notebook 08 implements the frozen five-outer/three-inner grouped evaluation. Read [REPRODUCING.md](../REPRODUCING.md) for verification, optional input restoration, environment constraints and new-run execution. The completed study and its limitations are in the [final report](final-study-report.md).

The original full export manifest and the curated subset manifest are both retained. Each included model/prediction/table matches its original hash. The distributed subset excludes search checkpoints, cached input memory maps, extra-seed and ablation model binaries; their results are retained. XGBoost fitting/scoring must stay isolated from PyTorch in this environment. No study settings were changed for publication.
