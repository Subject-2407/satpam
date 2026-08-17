"""Tes penjaga: rule engine tidak boleh melihat jawaban maupun mesin pembuatnya.

Kembaran `test_no_circularity.py` untuk arah sebaliknya. Dua hal yang dijaga:

1. **Tidak ada file di `rules/` yang mengimpor `generator/`.** Kontrak skema
   data adalah satu-satunya titik temu; kedua sisi menyalinnya sendiri-sendiri.
   Kalau rule engine mengimpor modul generator, keduanya berhenti menjadi
   artefak independen dan perubahan di satu sisi diam-diam mengubah sisi lain.

2. **Tidak ada file di `rules/` yang menyebut kolom ground truth.** Kalau nama
   kolomnya tidak pernah muncul, ia tidak mungkin terbaca. `loader.py` memakai
   allowlist kolom, jadi larangan ini menutup jalan masuknya sepenuhnya.

Kalau tes ini gagal, `weak_labels.csv` berhenti menjadi label lemah dan menjadi
salinan jawaban. Seluruh premis weak supervision, propagasi feedback, dan
ablasi A1-A5 runtuh bersamanya.
"""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RULES_DIR = REPO_ROOT / "rules"

#: Paket yang tidak boleh diimpor dari `rules/`.
FORBIDDEN_MODULES = {"generator"}

#: Nama kolom jawaban. Tidak boleh muncul di mana pun dalam `rules/`.
FORBIDDEN_COLUMNS = ("gt_illicit", "gt_operator_id", "gt_ecosystem")


def _python_files() -> list[Path]:
    return sorted(RULES_DIR.rglob("*.py"))


def _module_is_forbidden(module_name: str) -> bool:
    return any(part in FORBIDDEN_MODULES for part in module_name.split("."))


def test_rules_dir_exists():
    assert RULES_DIR.is_dir(), "Folder rules/ tidak ditemukan"
    assert _python_files(), "Folder rules/ tidak berisi file Python"


def test_rules_does_not_import_generator():
    """rules/ tidak boleh mengimpor generator/ (lihat docstring modul)."""
    violations: list[str] = []

    for py_file in _python_files():
        tree = ast.parse(py_file.read_text(encoding="utf-8-sig"), filename=str(py_file))
        relative = py_file.relative_to(REPO_ROOT)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if _module_is_forbidden(alias.name):
                        violations.append(f"{relative}:{node.lineno} -> import {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                names = [alias.name for alias in node.names]
                if _module_is_forbidden(module) or any(
                    _module_is_forbidden(name) for name in names
                ):
                    violations.append(
                        f"{relative}:{node.lineno} -> from {module or '.'} "
                        f"import {', '.join(names)}"
                    )

    assert not violations, (
        "rules/ mengimpor generator/ — keduanya harus tetap artefak independen:\n"
        + "\n".join(violations)
    )


def test_rules_never_names_ground_truth_columns():
    """Nama kolom jawaban tidak boleh muncul di mana pun dalam rules/."""
    violations: list[str] = []

    for py_file in _python_files():
        relative = py_file.relative_to(REPO_ROOT)
        for number, line in enumerate(
            py_file.read_text(encoding="utf-8-sig").splitlines(), start=1
        ):
            for column in FORBIDDEN_COLUMNS:
                if column in line:
                    violations.append(f"{relative}:{number} -> menyebut {column}")

    assert not violations, (
        "rules/ menyebut kolom ground truth; label lemah bisa berubah menjadi "
        "salinan jawaban:\n" + "\n".join(violations)
    )


def test_loader_uses_allowlist_not_blocklist():
    """Kolom yang dibaca harus daftar yang diizinkan, bukan daftar yang dilarang.

    Allowlist lebih kuat: kolom baru apa pun yang muncul di berkas otomatis
    tidak terbaca, bukan otomatis terbaca.
    """
    from rules.loader import OBSERVABLE_NODE_COLUMNS

    assert all(
        column == "node_id"
        or column == "node_type"
        or column.startswith(("first_seen", "last_seen", "feat_"))
        for column in OBSERVABLE_NODE_COLUMNS
    ), f"ada kolom non-teramati di allowlist: {OBSERVABLE_NODE_COLUMNS}"
    assert "split" not in OBSERVABLE_NODE_COLUMNS
