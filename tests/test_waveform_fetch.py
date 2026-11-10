import hashlib
import io
import json
import runpy
import shutil
import subprocess
import tarfile
from pathlib import Path
from unittest.mock import patch

HELPER = Path(__file__).resolve().parents[1] / "tools/fetch_prepared_waveforms.py"


def test_public_download_falls_back_when_installed_gh_is_not_authenticated(tmp_path):
    root = tmp_path
    (root / "tools").mkdir()
    (root / "provenance").mkdir()
    helper = root / "tools/fetch_prepared_waveforms.py"
    shutil.copy2(HELPER, helper)
    payload = b"exact-waveform-test-fixture"
    member = "data/processed/phase1/waveforms/test.npz"
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode="w:gz") as tar:
        info = tarfile.TarInfo(member)
        info.size = len(payload)
        tar.addfile(info, io.BytesIO(payload))
    content = archive.getvalue()
    meta = {
        "filename": "prepared-waveforms.tar.gz",
        "release": "study-artifacts-v1",
        "repository": "owner/study",
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "members": {member: hashlib.sha256(payload).hexdigest()},
    }
    (root / "provenance/prepared-waveforms.json").write_text(json.dumps(meta))

    # Compatible with old check=True or new check=False subprocess invocation.
    def gh_failure(*args, **kwargs):
        if kwargs.get("check"):
            raise subprocess.CalledProcessError(4, args[0])
        return subprocess.CompletedProcess(args[0], 4, "", "Not logged in")

    with (
        patch("shutil.which", return_value="/usr/bin/gh"),
        patch("subprocess.run", side_effect=gh_failure),
        patch("urllib.request.urlopen", return_value=io.BytesIO(content)) as public,
    ):
        runpy.run_path(str(helper), run_name="__main__")
    public.assert_called_once()
    assert (root / member).read_bytes() == payload
