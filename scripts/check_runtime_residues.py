#!/usr/bin/env python3
"""
Varredura automatizada de residuos historicos proibidos no runtime ativo.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TARGETS = [
    "app",
    "scripts",
    ".github/workflows",
    "Dockerfile",
    "docker-compose.yml",
    "docker-compose.local.yml",
    ".env.compose",
    ".env.example",
    ".env.prod.example",
    "requirements.txt",
]
PATTERNS = {
    "pilot_atendimento": re.compile(r"pilot[\s_-]?atendimento", re.IGNORECASE),
    "santa_tereza": re.compile(r"santa[\s_-]?tereza", re.IGNORECASE),
    "ba_rag_piloto": re.compile(r"ba[\s_-]?rag[\s_-]?piloto", re.IGNORECASE),
    "terezia": re.compile(r"terezia", re.IGNORECASE),
}


@dataclass(frozen=True)
class Match:
    path: str
    line: int
    key: str
    excerpt: str


def iter_files() -> list[Path]:
    files: list[Path] = []
    for target in TARGETS:
        base = ROOT / target
        if base.is_file():
            files.append(base)
            continue
        if base.exists():
            files.extend(sorted(path for path in base.rglob("*") if path.is_file()))
    return files


def scan() -> list[Match]:
    matches: list[Match] = []
    for path in iter_files():
        if path == Path(__file__).resolve():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for line_number, line in enumerate(content.splitlines(), start=1):
            for key, pattern in PATTERNS.items():
                if pattern.search(line):
                    matches.append(
                        Match(
                            path=str(path.relative_to(ROOT)),
                            line=line_number,
                            key=key,
                            excerpt=line.strip(),
                        )
                    )
    return matches


def main() -> int:
    matches = scan()
    if matches:
        print("Falha na varredura de residuos historicos:\n")
        for match in matches:
            print(f"- {match.path}:{match.line} [{match.key}] {match.excerpt}")
        return 1

    print("Varredura de residuos historicos aprovada.")
    print(f"Arquivos verificados: {len(iter_files())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
