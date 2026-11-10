import ast
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

NOTEBOOK = Path(__file__).resolve().parents[1] / "notebooks/05_evaluation_protocol.ipynb"


@pytest.fixture
def api():
    notebook = json.loads(NOTEBOOK.read_text())
    nodes = []
    for cell in notebook["cells"]:
        if cell["cell_type"] == "code":
            nodes.extend(
                n
                for n in ast.parse("".join(cell["source"])).body
                if isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef))
            )
    namespace = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(NOTEBOOK), "exec"), namespace)
    return namespace


@pytest.fixture
def cohort():
    return pd.DataFrame(
        [
            dict(
                record_id=f"r{g}_{r}",
                minute=m,
                subject_group=f"g{g}",
                label=m % 2,
                start_sample=m * 6000,
                end_sample=(m + 1) * 6000,
                quality_flag=False,
            )
            for g in range(16)
            for r in range(2)
            for m in range(4)
        ]
    )


def test_folds_deterministic_and_complete(api, cohort):
    a, s = api["build_fold_assignments"](cohort, outer_splits=2, inner_splits=2, stopping_splits=2)
    b, t = api["build_fold_assignments"](cohort, outer_splits=2, inner_splits=2, stopping_splits=2)
    pd.testing.assert_frame_equal(a, b)
    pd.testing.assert_frame_equal(s, t)
    api["validate_fold_assignments"](
        cohort, a, s, outer_splits=2, inner_splits=2, stopping_splits=2
    )
    assert a.query("outer_role == 'test'").record_id.nunique() == 32


@pytest.mark.parametrize("corruption", ["duplicate", "missing", "role", "inner", "stop"])
def test_corrupted_assignments_rejected(api, cohort, corruption):
    a, s = api["build_fold_assignments"](cohort, outer_splits=2, inner_splits=2, stopping_splits=2)
    if corruption == "duplicate":
        a = pd.concat([a, a.iloc[:1]], ignore_index=True)
    if corruption == "missing":
        a = a.iloc[1:]
    if corruption == "role":
        a.loc[0, "outer_role"] = "train"
    if corruption == "inner":
        a.loc[0, "inner_fold"] = 99
    if corruption == "stop":
        s.loc[0, "role"] = "outer-test"
    with pytest.raises(ValueError):
        api["validate_fold_assignments"](
            cohort, a, s, outer_splits=2, inner_splits=2, stopping_splits=2
        )


def test_cohort_identity_and_duplicate_rejected(api, cohort):
    for changed in [pd.concat([cohort, cohort.iloc[:1]]), cohort.assign(label=2)]:
        with pytest.raises(ValueError):
            api["build_fold_assignments"](changed)
    cohort.loc[0, "subject_group"] = "other"
    with pytest.raises(ValueError):
        api["build_fold_assignments"](cohort)


def predictions(cohort, score):
    p = cohort[["record_id", "minute", "subject_group", "label"]].copy()
    p["score"] = score
    p["prediction"] = (p.score >= 0.5).astype(int)
    p["outer_fold"] = pd.factorize(p.subject_group)[0] % 2
    return p


def test_metrics_and_single_class(api, cohort):
    p = predictions(cohort, np.ones(len(cohort)))
    result = api["summarize_predictions"](p)
    row = result.query("level == 'pooled'").iloc[0]
    assert row.f1_score == pytest.approx(2 / 3)
    assert row.sensitivity == 1 and row.specificity == 0
    assert set(result.level) == {"pooled", "fold", "record", "group", "fold_mean"}
    single = api["summarize_predictions"](p.query("label == 0"))
    assert single.query("level == 'pooled'").average_precision.isna().all()
    with pytest.raises(ValueError):
        api["summarize_predictions"](pd.concat([p, p.iloc[:1]]))


def test_threshold_tie_and_invalid_scores(api):
    # Thresholds .2 and .5 both give F1=2/3: the lower one must win.
    assert api["choose_threshold"]([0, 1, 0, 0, 1], [0.1, 0.2, 0.3, 0.4, 0.5]) == 0.2
    with pytest.raises(ValueError):
        api["choose_threshold"]([0, 1], [0, np.nan])


def test_paired_bootstrap_alignment_and_group_weights(api, cohort):
    a = predictions(cohort, cohort.label.to_numpy() * 0.8 + 0.1)
    r = api["paired_group_bootstrap"](a, a.sample(frac=1, random_state=2), n_resamples=1000)
    assert r["valid_draws"] == 1000 and r["lower"] == r["upper"] == 0
    bad = a.copy()
    bad.loc[0, "label"] = 1
    with pytest.raises(ValueError):
        api["paired_group_bootstrap"](a, bad)
    weights = api["group_weights"](a, ["g0", "g0", "g1"])
    assert set(weights[a.subject_group == "g0"]) == {2}
    assert set(weights[a.subject_group == "g1"]) == {1}
    assert set(weights[a.subject_group == "g2"]) == {0}


def test_prediction_group_leakage_rejected(api, cohort):
    p = predictions(cohort, np.zeros(len(cohort)))
    p.loc[0, "outer_fold"] = 99
    with pytest.raises(ValueError, match="group crosses"):
        api["summarize_predictions"](p)


def test_degenerate_bootstrap_draws_are_reported(api, cohort):
    p = predictions(cohort.query("subject_group in ['g0', 'g1']"), 0.5)
    p["label"] = p.subject_group.eq("g1").astype(int)
    result = api["paired_group_bootstrap"](p, p, n_resamples=100)
    assert 0 < result["valid_draws"] < 100
    assert result["skipped_draws"] == 100 - result["valid_draws"]
    assert np.isnan(result["lower"]) and np.isnan(result["upper"])


def test_artifact_reuse_and_corruption(api, cohort, tmp_path):
    a, s = api["build_fold_assignments"](cohort, outer_splits=2, inner_splits=2, stopping_splits=2)
    config = {"synthetic": True}
    api["save_protocol"](tmp_path, cohort, a, s, config, {"test": "hash"})
    api["save_protocol"](tmp_path, cohort, a, s, config, {"test": "hash"})
    with pytest.raises(ValueError):
        api["save_protocol"](tmp_path, cohort, a, s, {"synthetic": False}, {"test": "hash"})
    (tmp_path / "protocol/cohort.parquet").write_bytes(b"corrupt")
    with pytest.raises(ValueError):
        api["save_protocol"](tmp_path, cohort, a, s, config, {"test": "hash"})
