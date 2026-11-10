# Reproducing and inspecting the study

## 1. Read and verify without fitting

Run `uv sync --locked`, launch `uv run jupyter lab`, and open `notebooks/START_HERE.ipynb` using the project kernel. It checks the raw recordings, bundled result hashes and primary model files, then replays held-out logistic regression predictions. It does not download, retrain or change thresholds.

The final PDF/HTML and `notebooks/executed/` can be read without Python. Executed copies are evidence snapshots, not replacement source files. Local display paths were redacted; some snapshots predate the final explanatory text. Use the notebooks directly under `notebooks/` for rerunning. Sources pinned in the frozen experiment are byte-identical to the original versions. Notebook 04 is a navigation pointer; the superseded single-split evaluation implementation and its model exports are not included.

## 2. Exact prepared waveforms for deeper audits

The raw WFDB files are in Git. The larger raw/filtered NumPy arrays are an optional release download, rather than a second large copy of the waveforms in Git history:

```bash
python tools/fetch_prepared_waveforms.py
```

While the repository is private, this uses authenticated `gh release download`. After it becomes public, the helper also supports the public release URL. It verifies archive and individual array checksums, restricts extraction to the 34 expected `.npz` files and the accompanying license/attribution, and never replaces a different existing file. The archive is approximately 850 MB. It contains prepared datasets, not training checkpoints or model-search caches.

After restoration, `notebooks/10_cnn_implementation_audit.ipynb` and `11_cnn_curves_and_raw_signals.ipynb` can run against the bundled results and original sources. Notebook 09 and the final-report notebook run without those prepared waveforms except the final report's raw-signal example figure, which needs them. All outputs go to new ignored report directories.

## 3. Inspect model weights

The 25 files under the evaluated run's `results/models/` are the primary seed-67 outer models: five held-out folds for LR, RF, XGBoost, adapted SVM and CNN. Their selected candidate settings, fold-specific thresholds and CNN epochs are in `selected_configurations.json`.

They are cross-validation models, not a single full-cohort deployment model. Choose each model's own held-out fold when replaying performance. The model card documents representations and serialization. Only load these local trusted pickle files after checksum verification. **XGBoost must be loaded/fitted/scored in a separate process without PyTorch in this pinned environment.** START_HERE demonstrates LR without loading XGBoost or PyTorch together.

## 4. Why the curated results manifest differs

The original export contained 140 artifacts, including 130 fitted model files. This showcase retains all ten non-model exports and 25 primary models. The retained `results/manifest.json` lists exactly these 35 artifacts and records its curation scope. `provenance/original-results-manifest.json` preserves the original full manifest unchanged. Every retained artifact hash matches that original manifest. Extra-seed and fixed-ablation *predictions and metrics* are included even though their model binaries are not.

The saved freeze identity, original source hashes, candidate order, saved assignments and result values are unchanged. Dates inside machine provenance identify the frozen study; they are not a collection of development plans. The method-source documents used to define the freeze retain their original text, including pre-freeze draft metadata; the freeze wrapper is authoritative. No new scientific score is produced by packaging.

## 5. Rerun the frozen runner or start a new experiment

Notebook 08 defaults to fitting-free verification. With the exact prepared waveforms restored, its input hashes and frozen environment can be checked. A complete rerun uses a **new** `APNEA_NESTED_TAG` and `APNEA_NESTED_ACTION=full`; it is a long CPU search. Do not reuse the published results directory or overwrite it with another experiment.

The original freeze pins package versions, Python 3.12.13 and the original platform. Another OS/Python build may legitimately fail that strict gate. Do not bypass the gate or claim byte-identical reproduction. Instead define a documented new run/freeze with the source notebooks and report the environment change. The original evaluated artifacts remain independently inspectable on other platforms.

For preparation from raw data, Notebook 00 can write to a new `APNEA_RUN`; choose fresh paths for downstream feature/protocol/baseline stages. Some stages download missing official files. The literature comparator's paper is not redistributed: Notebook 06 uses the source receipt and linked paper cache instructions. Checksums of newly serialized arrays may differ even when numerical arrays agree; the optional release is the route to the exact evaluated binary inputs.

## 6. Rebuild the report

The Markdown report is `docs/final-study-report.md`; figures are `reports/figures/`. The committed PDF and HTML are ready to read. PDF authoring is optional:

```bash
uv run --with reportlab==4.4.9 --with pypdf==6.10.0 python tools/build_pdf.py
```

Notebook 12 regenerates figures and HTML from saved results and creates an ignored timestamped output directory. It checks reported tables before rendering. The public-facing report includes the original full study's verification account; the curation paragraph and bundle manifest make the reduced model-file distribution explicit.

## Licenses and scope

MIT covers original code and associated documentation. PhysioNet source and derived data keep ODC-By attribution; read `data/README.md` and `LICENSES/ODC-By-1.0.txt`. The source paper and author software are not included. These are exploratory retrospective results, with unverified subject identities and prior cohort exposure. No clinical validation is claimed.
