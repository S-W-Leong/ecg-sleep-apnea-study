import ast
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

NB = Path(__file__).resolve().parents[1] / "notebooks/06_literature_baselines.ipynb"


@pytest.fixture
def api():
    nodes = []
    for cell in json.loads(NB.read_text())["cells"]:
        if cell["cell_type"] == "code":
            nodes.extend(
                n
                for n in ast.parse("".join(cell["source"])).body
                if isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef))
            )
    space = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(NB), "exec"), space)
    return space


def test_source_feature_fixture(api):
    result = api["rr_feature_vector"](
        [0.8, 0.9, 1.0, 0.8], [True] * 4, min_intervals=4, min_pairs=3
    )
    expected = [
        875,
        np.sqrt(27500 / 3),
        1,
        2,
        0.25,
        0.5,
        np.sqrt(30000),
        np.sqrt(20000),
        850,
        125,
        75,
    ]
    np.testing.assert_allclose(result, expected)
    assert len(api["literature_feature_names"]()) == len(result) == 11


def test_rejected_interval_does_not_create_new_pairs(api):
    result = api["rr_feature_vector"](
        [0.8, 1.8, 1.0, 0.8], [True, False, True, True], min_intervals=3, min_pairs=1
    )
    assert result[2] == 1 and result[3] == 0
    assert result[4] == pytest.approx(1 / 3)
    assert np.isnan(result[6])  # sample SDSD needs two differences
    assert result[7] == pytest.approx(200)
    assert np.isnan(api["rr_feature_vector"]([0.8], [True])).all()


def test_invalid_rr_rejected(api):
    with pytest.raises(ValueError):
        api["rr_feature_vector"]([np.nan], [True])
    with pytest.raises(ValueError):
        api["rr_feature_vector"]([-0.1], [True])


def test_constant_references_use_training_prevalence_only(api):
    evaluation = pd.DataFrame(
        dict(
            record_id=["a"] * 4,
            minute=range(4),
            subject_group=["g"] * 4,
            label=[0, 1, 0, 1],
            outer_fold=[0] * 4,
        )
    )
    result = api["constant_references"]([0, 0, 0, 1], evaluation)
    assert len(result) == 12
    assert result.query("model == 'training_prevalence'").score.eq(0.25).all()
    assert result.query("model == 'constant_positive'").prediction.eq(1).all()
    assert result.query("model == 'constant_negative'").prediction.eq(0).all()
    changed = evaluation.assign(label=1)
    other = api["constant_references"]([0, 0, 0, 1], changed)
    pd.testing.assert_series_equal(result.score, other.score)
    positive = result.query("model == 'constant_positive'")
    tp = ((positive.label == 1) & (positive.prediction == 1)).sum()
    assert 2 * tp / (2 * tp + 2) == pytest.approx(2 / 3)


def test_linear_pipeline_train_only_and_feature_order(api):
    names = api["literature_feature_names"]()
    x = pd.DataFrame(np.tile(np.arange(8)[:, None], (1, 11)), columns=names, dtype=float)
    x.iloc[0, 0] = np.nan
    model = api["fit_literature_model"](x, [0, 0, 0, 0, 1, 1, 1, 1])
    assert model[-1].kernel == "linear" and not model[-1].probability
    np.testing.assert_allclose(model[0].statistics_[0], 4)
    means = model[1].mean_.copy()
    scores = api["predict_literature_scores"](model, x[names[::-1]] + 100)
    assert scores.shape == (8,) and np.isfinite(scores).all()
    np.testing.assert_equal(model[1].mean_, means)
    with pytest.raises(ValueError):
        api["fit_literature_model"](x.assign(mean_rr_ms=np.nan), [0] * 4 + [1] * 4)


def test_window_boundaries_and_missing_windows(api):
    cohort = pd.DataFrame(
        dict(
            record_id=["r", "r"],
            minute=[0, 1],
            start_sample=[0, 6000],
            end_sample=[6000, 12000],
            label=[0, 1],
        )
    )
    rr = pd.DataFrame(
        [
            dict(
                record_id="r",
                start_sample=j * 80,
                end_sample=(j + 1) * 80,
                rr_seconds=0.8,
                plausible=True,
            )
            for j in range(24)
        ]
        + [dict(record_id="r", start_sample=5900, end_sample=6100, rr_seconds=2.0, plausible=True)]
    )
    result = api["extract_literature_features"](cohort, rr)
    assert len(result) == 2 and result.label.tolist() == [0, 1]
    assert result.iloc[0].mean_rr_ms == pytest.approx(800)
    assert result.iloc[0].sdrr_ms == 0
    assert result.iloc[1][api["literature_feature_names"]()].isna().all()


def test_protocol_and_baseline_cache_guard(api, tmp_path):
    protocol = tmp_path / "protocol"
    protocol.mkdir()
    (protocol / "manifest.json").write_text(
        json.dumps(dict(configuration={"synthetic": True}, artifacts={}))
    )
    with pytest.raises(ValueError, match="Synthetic"):
        api["verify_protocol"](tmp_path, False)
    frame = pd.DataFrame({"value": [1]})
    api["save_baselines"](tmp_path, {"test": 1}, [], frame, {"source": "a"})
    api["save_baselines"](tmp_path, {"test": 1}, [], frame, {"source": "a"})
    with pytest.raises(ValueError):
        api["save_baselines"](tmp_path, {"test": 1}, [], frame, {"source": "b"})
    (tmp_path / "baselines/features.parquet").write_bytes(b"bad")
    with pytest.raises(ValueError):
        api["save_baselines"](tmp_path, {"test": 1}, [], frame, {"source": "a"})
