"""Tes penjaga: generator/ tidak boleh mengimpor rules/ atau scoring. Ini
aturan keras yang tidak boleh dilanggar.

Gagal bila ada file Python di generator/ yang mengimpor `rules`
atau `scoring` dalam bentuk apa pun. Ground truth harus dihasilkan
independen dari rule engine — kalau tidak, eksperimen jadi sirkular.
"""

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GENERATOR_DIR = REPO_ROOT / "generator"

# Nama modul yang dilarang muncul di impor generator/
FORBIDDEN_MODULES = {"rules", "scoring"}


def _module_is_forbidden(module_name: str) -> bool:
    """Cek apakah nama modul (atau paket induknya) termasuk yang dilarang."""
    parts = module_name.split(".")
    return any(part in FORBIDDEN_MODULES for part in parts)


def _find_forbidden_imports(py_file: Path) -> list[str]:
    """Kembalikan daftar pelanggaran impor di satu file Python."""
    # utf-8-sig agar file ber-BOM (umum di editor Windows) tetap bisa diparse
    source = py_file.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(py_file))
    violations = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _module_is_forbidden(alias.name):
                    violations.append(
                        f"{py_file.relative_to(REPO_ROOT)}:{node.lineno} "
                        f"-> import {alias.name}"
                    )
        elif isinstance(node, ast.ImportFrom):
            # node.module bisa None untuk relative import ("from . import x")
            module = node.module or ""
            imported_names = [alias.name for alias in node.names]
            if _module_is_forbidden(module) or any(
                _module_is_forbidden(name) for name in imported_names
            ):
                violations.append(
                    f"{py_file.relative_to(REPO_ROOT)}:{node.lineno} "
                    f"-> from {module or '.'} import {', '.join(imported_names)}"
                )
    return violations


def test_generator_does_not_import_rules_or_scoring():
    """generator/ tidak boleh mengimpor rules/ atau scoring. Ini aturan keras
    yang tidak boleh dilanggar."""
    assert GENERATOR_DIR.is_dir(), "Folder generator/ tidak ditemukan"

    all_violations = []
    for py_file in GENERATOR_DIR.rglob("*.py"):
        all_violations.extend(_find_forbidden_imports(py_file))

    assert not all_violations, (
        "Pelanggaran ATURAN KERAS #1 — generator/ mengimpor logika rule-based:\n"
        + "\n".join(all_violations)
    )
