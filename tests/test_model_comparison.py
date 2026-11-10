import ast
import json
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    nodes = []
    for c in json.loads((ROOT / "notebooks" / name).read_text())["cells"]:
        if c["cell_type"] == "code":
            nodes.extend(
                n
                for n in ast.parse("".join(c["source"])).body
                if isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef))
            )
    ns = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), name, "exec"), ns)
    return ns


def test_original_architecture_and_100hz_inputs():
    a = load("03_waveform_cnn.ipynb")
    b = load("07_nested_model_comparison.ipynb")
    x = np.arange(6000, dtype=float)
    np.testing.assert_allclose(
        a["normalize_minute"](x, 100), np.clip((x - x.mean()) / x.std(), -8, 8).astype("float32")
    )
    assert a["normalize_minute"](np.zeros(6000), 100).shape == (6000,)
    assert np.isfinite(a["normalize_minute"](np.ones(6000) * 1e-10, 100)).all()
    for samples, hz in [(1500, 25), (6000, 25), (1500, 100)]:
        with pytest.raises(ValueError):
            a["normalize_minute"](np.zeros(samples), hz)
    torch.set_num_threads(1)
    old = a["make_model"]()
    new = b["make_cnn"]()
    assert str(old) == str(new)
    assert sum(p.numel() for p in new.parameters()) == 3009
    assert {k: tuple(v.shape) for k, v in old.state_dict().items()} == {
        k: tuple(v.shape) for k, v in new.state_dict().items()
    }
    logits = new(torch.ones(2, 1, 6000))
    assert logits.shape == (2, 1)
    logits.sum().backward()
    assert all(p.grad is not None and torch.isfinite(p.grad).all() for p in new.parameters())


def test_candidate_counts_determinism_and_fixed_architecture():
    api = load("07_nested_model_comparison.ipynb")
    a = api["candidate_registry"]()
    assert a == api["candidate_registry"]()
    assert set(a) == {"logistic_regression", "random_forest", "xgboost", "linear_svm", "cnn"}
    assert all(len(v) == 24 for v in a.values())
    assert all(
        set(c) == {"learning_rate", "weight_decay", "batch_size", "pos_weight"} for c in a["cnn"]
    )
    assert all("gamma" not in c for c in a["linear_svm"])


def test_input_contract_and_checkpoint_reuse():
    api = load("03_waveform_cnn.ipynb")
    with pytest.raises(ValueError):
        api["validate_cnn_cache"]({"input_hz": 25, "input_samples": 1500}, "test")


def test_freeze_hash_and_dependency_guards(tmp_path):
    api = load("07_nested_model_comparison.ipynb")
    payload = {
        "synthetic": False,
        "timing": {"complete": True},
        "candidates": api["candidate_registry"](),
    }
    api["write_stage"](tmp_path, "freeze", payload)
    api["write_stage"](tmp_path, "freeze", payload)
    with pytest.raises(ValueError):
        api["write_stage"](tmp_path, "freeze", dict(payload, synthetic=True))
    p = tmp_path / "freeze/manifest.json"
    p.write_text("{}")
    with pytest.raises(ValueError):
        api["write_stage"](tmp_path, "freeze", payload)


def test_xgboost_isolated_fit_after_torch():
    api = load("07_nested_model_comparison.ipynb")
    torch.set_num_threads(1)
    x = np.random.default_rng(67).normal(size=(32, 6))
    result = api["benchmark_xgboost"](x, np.array([0, 1] * 16), dict(n_estimators=2, max_depth=2))
    assert result["fit_seconds"] > 0
    assert result["torch_loaded"] is False


def test_waveform_loader_reads_each_record_once(monkeypatch):
    import pandas as pd

    api = load("07_nested_model_comparison.ipynb")
    reads = []

    class Source:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def __getitem__(self, key):
            if key == "fs":
                return np.array(100)
            reads.append(key)
            return np.arange(12000, dtype=float)

    monkeypatch.setattr(api["np"], "load", lambda *args, **kwargs: Source())
    cohort = pd.DataFrame(
        dict(record_id=["r", "r"], start_sample=[0, 6000], end_sample=[6000, 12000])
    )
    result = api["load_waveforms"](cohort, Path("/unused"))
    assert result.shape == (2, 6000) and reads == ["filtered"]


def test_checkpoint_source_data_drift():
    api = load("03_waveform_cnn.ipynb")
    metadata = dict(
        input_hz=100,
        input_samples=6000,
        parameters=3009,
        notebook_sha256="code",
        architecture=str(api["make_model"]()),
        phase1_manifest_sha256="old",
    )
    with pytest.raises(ValueError):
        api["validate_cnn_cache"](metadata, "code", "new")
