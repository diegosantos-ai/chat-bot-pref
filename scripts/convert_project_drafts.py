#!/usr/bin/env python3
import subprocess
import json
import sys

proj_num = 2
owner = 'diegosantos-ai'
repo = 'diegosantos-ai/pilot-atendimento'

def gh(cmd):
    full = ['gh'] + cmd
    r = subprocess.run(full, capture_output=True, text=True)
    if r.returncode != 0:
        print('ERROR running', full)
        print(r.stderr)
        return None
    return r.stdout

# get project id
out = gh(['project','view',str(proj_num),'--owner',owner,'--format','json'])
if not out:
    sys.exit(1)
proj = json.loads(out)
proj_id = proj.get('id')
print('Project id:', proj_id)

# get issues
out = gh(['issue','list','--repo',repo,'--limit','200','--json','number,title'])
if not out:
    sys.exit(1)
issues = json.loads(out)
print(f'Found {len(issues)} issues')

# get current project items once
def get_project_items():
    out = gh(['project','item-list',str(proj_num),'--owner',owner,'-L','200','--format','json'])
    if not out:
        return []
    data = json.loads(out)
    return data.get('items', [])

for issue in issues:
    num = issue.get('number')
    title = issue.get('title')
    print('\nProcessing issue', num, title)
    q = f'query {{ repository(owner:"{owner}", name:"pilot-atendimento") {{ issue(number: {num}) {{ id }} }} }}'
    out = gh(['api','graphql','-f', f'query={q}'])
    if not out:
        print('Failed to fetch issue node id')
        continue
    data = json.loads(out)
    try:
        issue_id = data['data']['repository']['issue']['id']
    except Exception as e:
        print('Could not get issue id for', num, e)
        continue
    print('Issue node id:', issue_id)
    mut = f'mutation {{ addProjectV2ItemByContentId(input:{{projectId:"{proj_id}", contentId:"{issue_id}"}}) {{ item {{ id }} }} }}'
    out = gh(['api','graphql','-f', f'query={mut}'])
    if not out:
        print('Mutation failed for', num)
        continue
    resp = json.loads(out)
    if resp.get('data') and resp['data'].get('addProjectV2ItemByContentId'):
        item_id = resp['data']['addProjectV2ItemByContentId']['item']['id']
        print('Added project item id:', item_id)
        # refresh project items and remove draft with same title
        items = get_project_items()
        for it in items:
            try:
                if it.get('title') == title and it.get('type') == 'DraftIssue':
                    did = it.get('id')
                    print('Deleting draft item', did, title)
                    _ = gh(['project','item-delete', did, '--confirm'])
            except Exception:
                continue
    else:
        print('Add mutation returned no data for', num)

print('\nDone')
