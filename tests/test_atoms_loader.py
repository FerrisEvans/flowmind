import json
import tempfile
from pathlib import Path

from core.atoms_loader import load_atoms_registry

EXPECTED_ATOM_IDS = {
    "common.file.get_file_size",
    "globalx.permission.grant_permission",
    "globalx.permission.query_permissions",
    "globalx.space.query_quota",
    "globalx.transfer.file_transfer",
}


def test_load_real_atoms(atoms_registry):
    assert set(atoms_registry.keys()) == EXPECTED_ATOM_IDS


def test_load_empty_dir():
    with tempfile.TemporaryDirectory() as td:
        registry = load_atoms_registry(Path(td))
        assert registry == {}


def test_load_missing_dir():
    registry = load_atoms_registry(Path("/nonexistent/path/xyz"))
    assert registry == {}


def test_skip_invalid_json():
    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        (td_path / "bad.json").write_text("NOT JSON", encoding="utf-8")
        (td_path / "good.json").write_text(
            json.dumps({
                "atoms": [{"id": "test.ok", "inputs": [], "outputs": []}]
            }),
            encoding="utf-8",
        )
        registry = load_atoms_registry(td_path)
        assert "test.ok" in registry
        assert len(registry) == 1


def test_atom_shape(atoms_registry):
    for atom_id, atom in atoms_registry.items():
        assert atom.get("id") == atom_id
        assert isinstance(atom.get("inputs"), list) or atom.get("inputs") is None
        assert isinstance(atom.get("outputs"), list) or atom.get("outputs") is None
