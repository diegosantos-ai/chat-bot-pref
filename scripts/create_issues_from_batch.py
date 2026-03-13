#!/usr/bin/env python3
"""Cria issues no GitHub a partir de .github/ISSUES_BATCH.md

Uso:
  export GITHUB_TOKEN=ghp_xxx
  python scripts/create_issues_from_batch.py --repo owner/repo [--dry-run] [--create-milestones]

O script procura blocos iniciados por '##' no arquivo `.github/ISSUES_BATCH.md`.
Cada bloco deve ter a estrutura gerada pelo assistente: título na linha seguinte e
descrição com checklists. Labels são detectados na linha 'Labels: `a`, `b`' e
Milestone na linha 'Milestone: `name`'.
"""
from __future__ import annotations
import os
import re
import sys
import argparse
import requests
from typing import List, Optional, Tuple

ISSUES_FILE = os.path.join('.github', 'ISSUES_BATCH.md')
GITHUB_API = 'https://api.github.com'


def parse_issues_batch(path: str) -> List[Tuple[str, str, List[str], Optional[str]]]:
    """Parseia o arquivo e retorna lista de tuplas (title, body, labels, milestone)
    """
    with open(path, 'r', encoding='utf-8') as f:
        text = f.read()

    blocks = re.split(r'^##\s+', text, flags=re.MULTILINE)[1:]
    issues = []
    for b in blocks:
        lines = b.strip().splitlines()
        if not lines:
            continue
        # título está na primeira linha
        title = lines[0].strip()
        body_lines = lines[1:]
        body = '\n'.join(body_lines).strip()

        # extrair labels: procura por 'Labels: `a`, `b`'
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


def gh_request(method: str, url: str, token: str, **kwargs):
    headers = kwargs.pop('headers', {})
    headers.update({'Authorization': f'token {token}', 'Accept': 'application/vnd.github+json'})
    resp = requests.request(method, url, headers=headers, **kwargs)
    if resp.status_code >= 400:
        raise SystemExit(f'Erro {resp.status_code} em {url}: {resp.text}')
    return resp.json()


def get_milestone_number(repo: str, token: str, title: str, create_if_missing: bool=False) -> Optional[int]:
    url = f'{GITHUB_API}/repos/{repo}/milestones?state=all'
    ms = gh_request('GET', url, token)
    for m in ms:
        if m.get('title') == title:
            return m.get('number')
    if create_if_missing:
        url = f'{GITHUB_API}/repos/{repo}/milestones'
        payload = {'title': title}
        m = gh_request('POST', url, token, json=payload)
        return m.get('number')
    return None


def create_issue(repo: str, token: str, title: str, body: str, labels: List[str], milestone_number: Optional[int]):
    url = f'{GITHUB_API}/repos/{repo}/issues'
    payload = {'title': title, 'body': body}
    if labels:
        payload['labels'] = labels
    if milestone_number is not None:
        payload['milestone'] = milestone_number
    return gh_request('POST', url, token, json=payload)


def main(argv: List[str]):
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', '-r', required=True, help='owner/repo')
    parser.add_argument('--dry-run', action='store_true', help='Imprime issues sem criar')
    parser.add_argument('--create-milestones', action='store_true', help='Cria milestone se não existir')
    args = parser.parse_args(argv)

    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        print('Erro: defina a variável de ambiente GITHUB_TOKEN com permissões de repo.')
        sys.exit(2)

    if not os.path.exists(ISSUES_FILE):
        print(f'Arquivo não encontrado: {ISSUES_FILE}')
        sys.exit(1)

    issues = parse_issues_batch(ISSUES_FILE)
    print(f'Encontradas {len(issues)} issues no batch.')

    for i, (title, body, labels, milestone) in enumerate(issues, start=1):
        print(f'[{i}/{len(issues)}] {title}')
        if milestone:
            ms_num = get_milestone_number(args.repo, token, milestone, create_if_missing=args.create_milestones)
        else:
            ms_num = None

        if args.dry_run:
            print('--- DRY RUN ---')
            print('Title:', title)
            print('Labels:', labels)
            print('Milestone:', milestone, '->', ms_num)
            print('Body:')
            print(body[:1000])
            print('---')
            continue

        created = create_issue(args.repo, token, title, body, labels, ms_num)
        print('Criada: ', created.get('html_url'))


if __name__ == '__main__':
    main(sys.argv[1:])
