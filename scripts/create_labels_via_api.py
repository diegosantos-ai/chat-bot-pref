import os
import requests

repo = os.environ.get('GITHUB_REPO')
token = os.environ.get('GITHUB_TOKEN')
api = 'https://api.github.com'

labels = [
    ("bug", "d73a4a", "Bug funcional que precisa correção"),
    ("enhancement", "a2eeef", "Nova funcionalidade / melhoria"),
    ("task", "0e8a16", "Tarefa operacional geral"),
    ("infra", "5319e7", "Infraestrutura / deploy / cloud"),
    ("db", "8e6ad8", "Banco de dados / migrations / backup"),
    ("observability", "1d76db", "Métricas, dashboards e alertas"),
    ("security", "fbca04", "Segurança, LGPD, PII e políticas"),
    ("docs", "0075ca", "Documentação e runbooks"),
    ("test", "d4c5f9", "Testes, smoke tests, E2E"),
    ("performance", "0052cc", "Latência e otimizações"),
    ("blocked", "b60205", "Impeditivo / dependência externa"),
    ("needs-review", "ffd3b6", "Pronto para revisão / QA"),
    ("priority:high", "b60205", "Alta prioridade / urgente"),
    ("help wanted", "008672", "Precisa de ajuda externa"),
    ("smoke-test", "0e8a16", "Teste rápido em produção"),
    ("policy", "a2eeef", "Mudanças em PolicyGuard e protocolos"),
    ("chore", "c2e0c6", "Manutenção sem entrega funcional")
]

headers = {'Authorization': f'token {token}', 'Accept': 'application/vnd.github+json'}

for name, color, desc in labels:
    url = f"{api}/repos/{repo}/labels"
    payload = {'name': name, 'color': color, 'description': desc}
    r = requests.post(url, json=payload, headers=headers)
    if r.status_code in (200, 201):
        print('Created', name)
    elif r.status_code == 422:
        print('Exists', name)
    else:
        print('Error', name, r.status_code, r.text)
