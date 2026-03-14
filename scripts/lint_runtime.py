#!/usr/bin/env python3
"""
Lint minimo e explicavel do runtime ativo.

Este script evita depender de tooling externo para o corte atual da Fase 12.
Ele valida:

- parse de todos os arquivos Python do runtime/testes/scripts
- ausencia de merge markers
- ausencia de wildcard imports
"""

from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON_TARGETS = ["app", "scripts", "tests"]
TEXT_TARGETS = [
    "app",
    "scripts",
    "tests",
    ".github/workflows",
    "README.md",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.local.yml",
]
MERGE_MARKERS = ("<<<<<<<", "=======", ">>>>>>>")


@dataclass(frozen=True)
class Failure:
    path: str
    line: int
    reason: str


def iter_python_files() -> list[Path]:
    files: list[Path] = []
    for target in PYTHON_TARGETS:
        base = ROOT / target
        if not base.exists():
            continue
        files.extend(sorted(base.rglob("*.py")))
    return files


def iter_text_files() -> list[Path]:
    files: list[Path] = []
    for target in TEXT_TARGETS:
        base = ROOT / target
        if base.is_file():
            files.append(base)
            continue
        if base.exists():
            files.extend(sorted(path for path in base.rglob("*") if path.is_file()))
    return files


def validate_python_files(files: list[Path]) -> list[Failure]:
    failures: list[Failure] = []
    for path in files:
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            failures.append(
                Failure(
                    path=str(path.relative_to(ROOT)),
                    line=exc.lineno or 1,
                    reason=f"syntax error: {exc.msg}",
                )
            )
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names):
                failures.append(
                    Failure(
                        path=str(path.relative_to(ROOT)),
                        line=getattr(node, "lineno", 1),
                        reason="wildcard import nao permitido",
                    )
                )
    return failures


def validate_text_files(files: list[Path]) -> list[Failure]:
    failures: list[Failure] = []
    for path in files:
        if path == Path(__file__).resolve():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line_number, line in enumerate(content.splitlines(), start=1):
            normalized = line.lstrip()
            if any(normalized.startswith(marker) for marker in MERGE_MARKERS):
                failures.append(
                    Failure(
                        path=str(path.relative_to(ROOT)),
                        line=line_number,
                        reason="merge marker encontrado",
                    )
                )
    return failures


def main() -> int:
    python_files = iter_python_files()
    text_files = iter_text_files()
    failures = validate_python_files(python_files)
    failures.extend(validate_text_files(text_files))

    if failures:
        print("FALHA no lint minimo do runtime:\n")
        for failure in failures:
            print(f"- {failure.path}:{failure.line} -> {failure.reason}")
        return 1

    print("Lint minimo aprovado.")
    print(f"Arquivos Python verificados: {len(python_files)}")
    print(f"Arquivos texto verificados: {len(text_files)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
