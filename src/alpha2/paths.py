"""Single source of repo-relative paths (replaces the sandbox /mnt/... path).

Every absolute/output path in the toolkit resolves through this module; no other
module in src/alpha2 may embed a filesystem path. The repo root is discovered
from this file's location (src/alpha2/paths.py -> repo root is three parents up).
"""
from pathlib import Path

# src/alpha2/paths.py -> parents[0]=alpha2, [1]=src, [2]=repo root
REPO_ROOT = Path(__file__).resolve().parents[2]

CORPUS = REPO_ROOT / "data" / "corpus" / "hadwiger_alpha2_certificates.json"


def ensure_parent(path=CORPUS):
    """Ensure the parent directory of ``path`` exists; return the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    return path
