"""
Load atomic service definitions from atoms/*.json and build a registry
{ atom_id: atom_def } for use by the plan validator and executor.
"""

from pathlib import Path
import json


def load_atoms_registry(atoms_dir: Path | None = None) -> dict:
    """
    Load all atoms from JSON files under atoms_dir and return a registry
    mapping atom id -> atom definition.

    Atom definition shape: at least id, inputs (list of {name, required?, ...}), outputs (list of {name, ...}).
    """
    if atoms_dir is None:
        # Default: project root / atoms (core/atoms_loader.py -> parent.parent / atoms)
        atoms_dir = Path(__file__).resolve().parent.parent / "atoms"
    if not atoms_dir.is_dir():
        return {}

    registry: dict = {}
    for path in sorted(atoms_dir.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        atoms = data.get("atoms") or []
        for atom in atoms:
            aid = atom.get("id")
            if aid:
                registry[aid] = atom
    return registry
