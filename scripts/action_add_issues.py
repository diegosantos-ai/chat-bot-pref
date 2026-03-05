#!/usr/bin/env python3
"""Action helper: adiciona issues ao Project V2 a partir de um CSV.

Requer o secret `PROJECT_TOKEN` com scope `project` e permissões em repo/project.

Uso (executado pela workflow):
  python scripts/action_add_issues.py --project-id PVT_... --csv artifacts/issues_mapping.csv
"""
from __future__ import annotations
import os
import csv
import argparse
import requests
import sys

GQL_URL = 'https://api.github.com/graphql'


def gh_graphql(query: str, token: str):
    headers = {'Authorization': f'bearer {token}', 'Accept': 'application/vnd.github.v3+json'}
    r = requests.post(GQL_URL, json={'query': query}, headers=headers, timeout=30)
    if r.status_code != 200:
        raise SystemExit(f'GraphQL error {r.status_code}: {r.text}')
    return r.json()


def get_issue_node_id(owner: str, repo: str, number: int, token: str) -> str | None:
    q = f'''query {{ repository(owner: "{owner}", name: "{repo}") {{ issue(number: {number}) {{ id }} }} }}'''
    j = gh_graphql(q, token)
    try:
        return j['data']['repository']['issue']['id']
    except Exception:
        return None


def add_issue_to_project(project_id: str, content_id: str, token: str) -> str | None:
    m = f'''mutation {{ addProjectV2ItemByContentId(input: {{projectId: "{project_id}", contentId: "{content_id}"}}) {{ item {{ id }} }} }}'''
    j = gh_graphql(m, token)
    try:
        return j['data']['addProjectV2ItemByContentId']['item']['id']
    except Exception:
        print('add mutation error:', j)
        return None


def main(argv: list[str]):
    p = argparse.ArgumentParser()
    p.add_argument('--project-id', required=True)
    p.add_argument('--csv', default='artifacts/issues_mapping.csv')
    args = p.parse_args(argv)

    token = os.environ.get('PROJECT_TOKEN') or os.environ.get('GITHUB_TOKEN')
    if not token:
        print('Missing PROJECT_TOKEN in environment')
        sys.exit(2)

    owner_repo = os.environ.get('GITHUB_REPOSITORY')
    if not owner_repo:
        print('Missing GITHUB_REPOSITORY env')
        sys.exit(2)
    owner, repo = owner_repo.split('/')

    path = args.csv
    if not os.path.exists(path):
        print('CSV not found:', path)
        sys.exit(1)

    results = []
    with open(path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            num = int(row['number'])
            print(f'Processing issue #{num}...')
            node = get_issue_node_id(owner, repo, num, token)
            if not node:
                print('  could not find issue node id')
                results.append((num, 'no-node', row.get('url', '')))
                continue
            added = add_issue_to_project(args.project_id, node, token)
            if added:
                print('  added, item id', added)
                results.append((num, 'added', added))
            else:
                print('  failed to add')
                results.append((num, 'failed', row.get('url', '')))
    # Write summary files for failures and helper scripts to assist manual steps
    failed = [r for r in results if r[1] != 'added']

    if failed:
        failed_csv = os.path.join('artifacts', 'failed_items.csv')
        os.makedirs(os.path.dirname(failed_csv), exist_ok=True)
        with open(failed_csv, 'w', newline='', encoding='utf-8') as outfh:
            w = csv.writer(outfh)
            w.writerow(['number', 'status', 'url'])
            for r in failed:
                # r = (num, status, url)
                w.writerow([r[0], r[1], r[2] if len(r) > 2 else ''])

        # Generate curl-based GraphQL attempts (may still fail if API not available)
        curl_script = os.path.join('artifacts', 'add_issues_graphql_attempts.sh')
        with open(curl_script, 'w', encoding='utf-8') as sh:
            sh.write('#!/usr/bin/env bash\n')
            sh.write('# Attempts to run the GraphQL mutation for each failed issue.\n')
            sh.write('# Requires PROJECT_TOKEN env var with appropriate scopes.\n')
            for r in failed:
                num = r[0]
                url = r[2] if len(r) > 2 else ''
                sh.write(f'echo "Attempting issue #{num} ({url})"\n')
                sh.write('echo "Provide PROJECT_TOKEN in environment before running."\n')
                sh.write('curl -s -X POST -H "Authorization: bearer $PROJECT_TOKEN" -H "Content-Type: application/json" \\\n+')
                sh.write('  -d "{\"query\": \"mutation { addProjectV2ItemByContentId(input: {projectId: \\\"%s\\\", contentId: \\\"<CONTENT_ID_HERE>\\\"}) { item { id } } }\" }" \\\n+' % args.project_id)
                sh.write('  https://api.github.com/graphql\n\n')

        # Generate a simple script to open issue URLs in browser for manual linking
        open_script = os.path.join('artifacts', 'open_issue_urls.sh')
        with open(open_script, 'w', encoding='utf-8') as sh2:
            sh2.write('#!/usr/bin/env bash\n')
            sh2.write('# Opens failed issue URLs in the default browser to allow manual add-to-project.\n')
            for r in failed:
                url = r[2] if len(r) > 2 else ''
                if url:
                    sh2.write(f'echo "Opening {url}"\n')
                    sh2.write(f'python -m webbrowser "{url}" || xdg-open "{url}" || echo "Open {url} manually"\n')

        print('\nFailures detected:')
        print(f'- Failed CSV: {failed_csv}')
        print(f'- GraphQL attempts script: {curl_script} (edit <CONTENT_ID_HERE> before running)')
        print(f'- Open URLs script: {open_script} (will open issues in browser)')
        sys.exit(1)
    else:
        print('\nAll items added successfully')
        sys.exit(0)


if __name__ == '__main__':
    main(sys.argv[1:])
