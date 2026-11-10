import ast
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks/08_nested_evaluation.ipynb"


@pytest.fixture
def api():
    nodes = []
    for c in json.loads(NOTEBOOK.read_text())["cells"]:
        if c["cell_type"] == "code":
            nodes.extend(
                n
                for n in ast.parse("".join(c["source"])).body
                if isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.ClassDef))
            )
    scope = {"ROOT": ROOT}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(NOTEBOOK), "exec"), scope)
    scope["install_dependencies"](ROOT, scope)
    return scope


def test_selection_uses_inner_scores_and_frozen_ties(api):
    rows = [
        dict(candidate=0, mean_validation_ap=0.8, outer_ap=1),
        dict(candidate=1, mean_validation_ap=0.9, outer_ap=0),
    ]
    assert api["select_candidate"](rows) == 1
    rows[0]["mean_validation_ap"] = 0.9 - 1e-13
    assert api["select_candidate"](rows) == 0
    with pytest.raises(ValueError):
        api["select_candidate"]([dict(candidate=0, mean_validation_ap=np.nan)])


def test_checkpoint_resume_drift_corruption_and_interruption(api, tmp_path):
    calls = []

    def work():
        calls.append(1)
        return {"value": 42}

    task = tmp_path / "fit"
    context = {"freeze": "a", "runner": "b"}
    assert api["checkpoint_task"](task, context, work)["value"] == 42
    assert api["checkpoint_task"](task, context, work)["value"] == 42
    assert len(calls) == 1
    with pytest.raises(ValueError):
        api["checkpoint_task"](task, dict(context, runner="changed"), work)
    (task / "payload.pkl").write_bytes(b"corrupt")
    with pytest.raises(ValueError):
        api["checkpoint_task"](task, context, work)

    def interrupted():
        raise RuntimeError("interrupted")

    with pytest.raises(RuntimeError):
        api["checkpoint_task"](tmp_path / "other", context, interrupted)
    assert not (tmp_path / "other").exists()
    assert api["checkpoint_task"](tmp_path / "other", context, work)["value"] == 42


def test_saved_folds_and_cnn_stopping_are_disjoint(api):
    run = ROOT / "tests/fixtures/protocol"
    c = pd.read_parquet(run / "cohort.parquet")
    f = pd.read_csv(run / "fold_assignments.csv")
    s = pd.read_csv(run / "cnn_stop_assignments.csv")
    train, held, cv, stopping = api["partition_indices"](c, f, s, 0)
    assert len(set(train) & set(held)) == 0
    for (fit, val), (cal, stop) in zip(cv, stopping, strict=True):
        assert not set(c.iloc[train[fit]].subject_group) & set(c.iloc[train[val]].subject_group)
        assert not set(cal) & set(stop) and set(cal) | set(stop) == set(fit)
    s.loc[0, "role"] = "bad"
    with pytest.raises(ValueError):
        api["partition_indices"](c, f, s, 0)


def test_sklearn_preprocessing_sees_only_inner_fit_rows(api):
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    seen = []

    class Spy(SimpleImputer):
        def fit(self, X, y=None):
            seen.append(set(np.asarray(X)[:, 0]))
            return super().fit(X, y)

    api["make_classical_model"] = lambda name, settings, seed: make_pipeline(
        Spy(), StandardScaler(), LogisticRegression(**settings)
    )
    x = np.arange(8, dtype=float).reshape(-1, 1)
    y = np.array([0, 1] * 4)
    cv = [(np.arange(4), np.arange(4, 8)), (np.arange(4, 8), np.arange(4))]
    result = api["sklearn_search"]("logistic_regression", x, y, cv, [{"C": 0.1}, {"C": 1}], 67)
    assert len(result["trials"]) == 2
    assert seen == [set(range(4)), set(range(4, 8))] * 2


def test_cnn_fresh_fits_fixed_epochs_and_fit_only_weight(api):
    import torch

    torch.set_num_threads(1)
    x = np.random.default_rng(67).normal(size=(4, 1, 6000)).astype("float32")
    y = np.array([0, 0, 0, 1])
    settings = dict(learning_rate=0.001, weight_decay=0.0001, batch_size=4, pos_weight="balanced")
    a = api["cnn_fit"](x, y, settings, 67, 2)
    b = api["cnn_fit"](x, y, settings, 67, 2, stop_data=(x[:2], np.array([0, 1])))
    assert len(a["history"]) == 2 and a["pos_weight"] == 3
    assert a["initial_state_hash"] == b["initial_state_hash"]
    assert a["final_state_hash"] != a["initial_state_hash"]
    assert 1 <= b["best_epoch"] <= 2
    scores = api["cnn_scores"](a["model_bytes"], x)
    assert scores.shape == (4,) and np.isfinite(scores).all()


def test_xgboost_scoring_remains_isolated(api):
    x = np.random.default_rng(67).normal(size=(16, 2))
    y = np.array([0, 1] * 8)
    result = api["xgb_worker"](
        "fit", dict(x=x, y=y, score_x=x[:4], settings={"n_estimators": 2, "max_depth": 2}, seed=67)
    )
    assert not result["torch_loaded"] and isinstance(result["model_bytes"], bytes)
    assert np.asarray(result["scores"]).shape == (4,)


def test_exclusive_lock_releases_on_exception(api, tmp_path):
    with pytest.raises(RuntimeError, match="boom"):
        with api["exclusive_run"](tmp_path):
            with pytest.raises(RuntimeError, match="already running"):
                with api["exclusive_run"](tmp_path):
                    pass
            raise RuntimeError("boom")
    with api["exclusive_run"](tmp_path):
        pass


def test_frozen_definitions_have_explicit_dependency_bindings(api):
    run = ROOT / "tests/fixtures/protocol"
    cohort = pd.read_parquet(run / "cohort.parquet")
    folds, stops = api["build_fold_assignments"](
        cohort, outer_splits=2, inner_splits=2, stopping_splits=2
    )
    assert len(folds) == 64 and len(stops) > 0
    assert api["choose_threshold"]([0, 1], [0.1, 0.9]) == 0.9
    model = api["make_classical_model"]("logistic_regression", {"C": 1}, 67)
    model.fit(np.arange(8).reshape(-1, 1), [0, 1] * 4)


def test_outer_prediction_coverage_and_frozen_fold_labels(api):
    run = ROOT / "tests/fixtures/protocol"
    c = pd.read_parquet(run / "cohort.parquet")
    f = pd.read_csv(run / "fold_assignments.csv")
    p = c[["record_id", "minute", "subject_group", "label"]].merge(
        f.query("outer_role == 'test'")[["record_id", "outer_fold"]], on="record_id"
    )
    p = p.assign(
        analysis="tuned",
        model="logistic_regression",
        feature_set="B_F2",
        seed=67,
        score=p.label * 0.8 + 0.1,
        threshold=0.5,
        prediction=p.label,
    )
    api["validate_outer_predictions"](p, c, f)
    for bad in [p.iloc[1:], pd.concat([p, p.iloc[:1]])]:
        with pytest.raises((ValueError, AssertionError)):
            api["validate_outer_predictions"](bad, c, f)
    bad = p.copy()
    bad.loc[0, "prediction"] = 1 - bad.loc[0, "prediction"]
    with pytest.raises(ValueError):
        api["validate_outer_predictions"](bad, c, f)


def test_cnn_stopping_leakage_fails_before_training(api, tmp_path):
    api["cnn_fit"] = lambda *args, **kwargs: (_ for _ in ()).throw(
        AssertionError("training reached")
    )
    x = np.zeros((4, 1, 6000), dtype="float32")
    y = np.array([0, 1, 0, 1])
    cv = [(np.array([0, 1]), np.array([2, 3]))]
    bad_stopping = [(np.array([0]), np.array([0, 1]))]
    with pytest.raises(ValueError, match="stopping leakage"):
        api["run_inner_search"]("cnn", x, y, cv, bad_stopping, [{}], {}, 67, tmp_path, {})


def test_cnn_patience_uses_separate_stopping_loss(api, monkeypatch):
    import torch

    class ConstantLoss:
        def __init__(self, **kwargs):
            pass

        def __call__(self, logits, truth):
            return torch.tensor(1.0)

    monkeypatch.setattr(api["nn"], "BCEWithLogitsLoss", ConstantLoss)
    api["train_epoch"] = lambda *args: 0.5
    x = np.zeros((4, 1, 6000), dtype="float32")
    y = np.array([0, 1, 0, 1])
    settings = dict(learning_rate=0.001, weight_decay=0, batch_size=4, pos_weight="balanced")
    result = api["cnn_fit"](x, y, settings, 67, 10, stop_data=(x[:2], y[:2]), patience=2)
    assert len(result["history"]) == 3 and result["best_epoch"] == 1
