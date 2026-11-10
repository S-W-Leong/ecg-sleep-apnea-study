# Literature baseline screening — 2026-11-08

## Decision

Include **an independently implemented, adapted Almazaydeh et al. (2012) local-RR linear SVM**, plus constant-negative, constant-positive and training-prevalence references. The adaptation is eligible for our one-minute comparison; it is not author-code reproduction or replication of the paper's accuracy. No outer-model results were used to make this decision. The existing compact CNN's architecture is unchanged, with 100 Hz input restoration reserved for Plan 003.

## Source screening

| Candidate | Evidence inspected | Decision |
| --- | --- | --- |
| [Almazaydeh, Elleithy & Faezipour, EMBC 2012](https://doi.org/10.1109/EMBC.2012.6347100) | Complete four-page [primary paper PDF](https://zenodo.org/records/1267839/files/article.pdf), particularly methods III.C–F, p.4940; Crossref DOI metadata | **Adapted main comparator.** The defining local feature equations and linear-kernel classifier are available. No author source code/weights were used. |
| [Dey, Chaudhuri & Munshi, 2018](https://link.springer.com/article/10.1007/s13534-017-0055-y) | Publisher record and indexed primary article descriptions | **Pending, optional and deferred.** Raw 6,000-sample input is relevant; full reproducible layer/training details and author code have not been verified. No invented architecture is registered as this method. |
| [Wang et al., PeerJ 2019](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6756143/) | Full-text preprocessing section, architecture discussion and supplement listing | **Contextual only.** The method uses adjacent minutes and interpolated RR/amplitude sequences. A supplement exists, but it was not downloaded or copied; it is not the main raw-waveform comparator. |
| [PhysioNet apdet v1.0.0](https://physionet.org/content/apdet/1.0.0/) | Author-contributed method, implementation description and corrections to published threshold constants | **Contextual only.** Longer NN/Hilbert context and prior development on this database prevent interpreting it as a matched one-minute reference. |

For Almazaydeh the reported 96.5% accuracy belongs to selected 15-second epochs and an original random 80/20 evaluation, not our cohort/protocol. No original-paper metric is entered as a result of our study. No human-reader baseline is inferred from expert reference labels.

## Source fidelity and explicit adaptations

The source specifies a **linear kernel with sequential minimal optimization**, so the conditional RBF proposal in Plan 002 is superseded. Use libsvm's linear SVC and decision_function. No gamma search and no implicit probability calibration.

| Component | Source-to-project correspondence |
| --- | --- |
| Epochs and cohort | Adapt selected 10/15/30-second source epochs to every retained 60-second project window; retain quality/missing windows |
| RR extraction | Replace the source peak detector with the existing project GQRS and plausibility policy; preserve within-window endpoints and original adjacency |
| Recording summaries | Omit recording-wide mean/SD; this avoids adding longer context to the local comparator |
| Features | Eleven local statistics below; keep source directional-count definitions and interval-count denominator |
| Defaults | Explicit sample SD (ddof=1), linear quantiles, minimum 20 intervals/10 pairs, train-fitted median imputation and scaling; these conventions are project choices |
| Evaluation | Saved grouped nested folds, inner average-precision selection and inner out-of-fold F1 threshold; no random epoch split |
| Fitting | Fresh fold-local models; C/class-weight search below; no source weights |

Fixed feature order: mean RR, sample SDRR, decrease count >50 ms, increase count >50 ms, each count divided by n accepted intervals (fractions), sample SD of valid adjacent differences, RR RMSSD, median RR, Q75−Q25, mean absolute deviation from mean RR. Units are ms except counts/fractions. Differences do not bridge rejected intervals. Missing statistics remain NaN; an all-missing training predictor stops fitting. These are detected RR statistics, not verified normal-to-normal HRV.

Reference classifier: linear SVC, C=1, class_weight=None. Proposed tuning: GridSearchCV over C={.001,.003,.01,.03,.1,.3,1,3,10,30,100,1000} × class_weight={None,balanced}, 24 candidates, using Plan 001's inner folds and average precision. Fit imputation/scaling inside every fold. Scores are uncalibrated decision values; select thresholds from training-side out-of-fold scores only.

A four-interval fixture [800,900,1000,800] ms yields mean 875, SDRR sqrt(27500/3), directional counts 1/2, fractions .25/.5, SDSD sqrt(30000), RMSSD sqrt(20000), median 850, IQR 125 and mean absolute deviation 75. Notebook tests relax minimum counts only for this fixture.

## Provenance and correction checks

The tracked references/baselines/almazaydeh2012/source.json records DOI, retrieval date, complete-PDF SHA-256, pages, adaptation and correction-check scope. The PDF cache lives under ignored data/references/baselines/almazaydeh2012.pdf. No paper, author implementation or pretrained weights are redistributed in Git. The implementation is independently written from attributed method descriptions; access to a public paper is not treated as a source-code license.

Crossref metadata retrieved 2026-11-08 contained no linked update-to/correction relation for this DOI. This is a limited metadata check, not proof that no correction exists; publisher full-text access was restricted. The source description, rather than its headline accuracy, defines the comparator. For deferred methods no unverified scientific detail is filled in to create apparent reproduction.

## Reproduce and inspect

1. Run Notebook 05 and keep its APNEA_PORTFOLIO_RUN. Notebook 06 verifies all protocol artifact hashes and matching synthetic/real status before use.
2. Cache the linked source PDF at data/references/baselines/almazaydeh2012.pdf for real runs; verify its receipt checksum. Smoke mode needs no network or paper download.
3. Execute notebooks/06_literature_baselines.ipynb with that same run root and smoke setting. It reads Phase 1 RR intervals, retains every cohort key, and writes baselines/register.json, specifications.json, features.parquet and manifest.json atomically. Source/receipt/document/protocol/RR/version hashes protect compatible reuse. Mismatches fail rather than overwrite.
4. Inspect the development-only linear SVM fit: only outer-fold-0 training records excluding inner-fold-0 validation are fitted. Output checks cover ordering/finite scores, not accuracy. No outer scores or tuned results are generated here.
5. Plan 003 will fit all reference strategies on the saved folds and produce the common prediction schema: record_id, minute, subject_group, label, model, feature_set, outer_fold, seed, score, score_kind, threshold, prediction. Simple references have fixed thresholds/classes; training prevalence comes only from the fitting partition.

The main literature specification is now selected and serializable. Overall protocol freezing remains pending Plan 003's timing/search checks. Subject identities remain unverified and all evaluation remains exploratory retrospective research.
