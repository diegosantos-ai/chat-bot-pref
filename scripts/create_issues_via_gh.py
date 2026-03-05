#!/usr/bin/env python3
"""Cria issues usando o `gh` CLI a partir de .github/ISSUES_BATCH.md

Uso:
  python scripts/create_issues_via_gh.py --repo owner/repo [--create-milestones]

Requer: `gh` autenticado (`gh auth login`).
"""
from __future__ import annotations
import os
import re
import sys
import argparse
import subprocess
import tempfile
from typing import List, Optional, Tuple

ISSUES_FILE = os.path.join('.github', 'ISSUES_BATCH.md')


def parse_issues_batch(path: str) -> List[Tuple[str, str, List[str], Optional[str]]]:
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()
    blocks = re.split(r'^##\s+', text, flags=re.MULTILINE)[1:]
    issues = []
    for b in blocks:
        lines = b.strip().splitlines()
        if not lines:
            continue
        title = lines[0].strip()
        body_lines = lines[1:]
        body = '\n'.join(body_lines).strip()
        labels = []
        lm = re.search(r'Labels:\s*(.*)', b)
        if lm:
            found = re.findall(r'`([^`]+)`', lm.group(1))
            labels = [s.strip() for s in found if s.strip()]
        milestone = None
        mm = re.search(r'Milestone:\s*`([^`]+)`', b)
        if mm:
            milestone = mm.group(1).strip()
        issues.append((title, body, labels, milestone))
    return issues


def run(cmd: List[str], check: bool = True):
    print('>',' '.join(cmd))
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        print('ERROR:', r.returncode)
        print(r.stderr.strip())
        if check:
            raise SystemExit(1)
    return r


def ensure_milestone(repo: str, milestone: str):
    # tenta criar a milestone (se já existir, ignora)
    cmd = ['gh', 'api', 'POST', f'/repos/{repo}/milestones', '-f', f'title={milestone}']
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if r.returncode == 0:
        print('Milestone criada:', milestone)
        return True
    # se já existe, API retorna 422 - podemos ignorar
    if 'already exists' in r.stderr.lower() or r.returncode == 422:
        print('Milestone já existe:', milestone)
        return True
    print('Aviso: criação de milestone não confirmou:', r.stderr.strip())
    return False


def create_issue_via_gh(repo: str, title: str, body: str, labels: List[str], milestone: Optional[str]):
    # escreve body em temp file e usa --body-file
    with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8', suffix='.md') as tf:
        tf.write(body)
        tf_path = tf.name
    cmd = ['gh', 'issue', 'create', '--repo', repo, '--title', title, '--body-file', tf_path]
    for l in labels:
        cmd += ['--label', l]
    if milestone:
        cmd += ['--milestone', milestone]
    r = run(cmd, check=False)
    if r.returncode == 0:
        print('Criada: ', r.stdout.strip())
    else:
        print('Falha ao criar issue:', title)


def main(argv: List[str]):
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', '-r', required=True, help='owner/repo')
    parser.add_argument('--create-milestones', action='store_true')
    args = parser.parse_args(argv)
    if not os.path.exists(ISSUES_FILE):
        print('Arquivo não encontrado:', ISSUES_FILE)
        sys.exit(1)
    issues = parse_issues_batch(ISSUES_FILE)
    print(f'Found {len(issues)} issues to create')

    # build set of existing issue titles to avoid duplicates
    existing_titles = set()
    try:
        resp = subprocess.run(['gh', 'issue', 'list', '--repo', args.repo, '--limit', '200', '--json', 'title'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if resp.returncode == 0 and resp.stdout:
            import json
            items = json.loads(resp.stdout)
            for it in items:
                t = it.get('title')
                if t:
                    existing_titles.add(t.strip())
    except Exception:
        pass
    for i, (title, body, labels, milestone) in enumerate(issues, start=1):
        print(f'[{i}/{len(issues)}] {title}')
        if title in existing_titles:
            print('Skipping existing issue:', title)
            continue
        if milestone and args.create_milestones:
            ensure_milestone(args.repo, milestone)
        create_issue_via_gh(args.repo, title, body, labels, milestone)


if __name__ == '__main__':
    main(sys.argv[1:])
