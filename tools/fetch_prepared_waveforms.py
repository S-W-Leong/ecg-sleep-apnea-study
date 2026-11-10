"""Download and verify the optional exact waveform dataset; no model fitting."""

import hashlib
import json
import shutil
import subprocess
import tarfile
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
meta = json.loads((ROOT / "provenance/prepared-waveforms.json").read_text())
cache = ROOT / "scratch/releases"
cache.mkdir(parents=True, exist_ok=True)
archive = cache / meta["filename"]
if not archive.exists():
    temporary = cache / (meta["filename"] + ".download")
    # Authenticated gh works for this private repo; public HTTP works after visibility changes.
    downloaded = False
    if shutil.which("gh"):
        result = subprocess.run(
            [
                "gh",
                "release",
                "download",
                meta["release"],
                "--repo",
                meta["repository"],
                "--pattern",
                meta["filename"],
                "--dir",
                str(cache),
            ],
            check=False,
        )
        downloaded = result.returncode == 0
    if not downloaded:
        url = f"https://github.com/{meta['repository']}/releases/download/{meta['release']}/{meta['filename']}"
        with urlopen(url) as source, temporary.open("wb") as target:
            shutil.copyfileobj(source, target)
        temporary.rename(archive)
assert archive.stat().st_size == meta["bytes"], "Archive size mismatch"
with archive.open("rb") as stream:
    assert hashlib.file_digest(stream, "sha256").hexdigest() == meta["sha256"], (
        "Archive hash mismatch"
    )
with tarfile.open(archive, "r:gz") as source:
    members = source.getmembers()
    assert len(members) == len(meta["members"])
    assert {m.name for m in members} == set(meta["members"]), "Unexpected archive paths"
    for member in members:
        assert member.isfile() and not member.issym() and not member.islnk()
        destination = ROOT / member.name
        assert destination.resolve().is_relative_to(ROOT.resolve())
        if destination.exists():
            with destination.open("rb") as stream:
                assert (
                    hashlib.file_digest(stream, "sha256").hexdigest()
                    == meta["members"][member.name]
                )
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(".download")
        with source.extractfile(member) as stream, temporary.open("wb") as target:
            shutil.copyfileobj(stream, target)
        with temporary.open("rb") as stream:
            assert hashlib.file_digest(stream, "sha256").hexdigest() == meta["members"][member.name]
        temporary.rename(destination)
print("Verified and restored all 34 prepared waveform files.")
