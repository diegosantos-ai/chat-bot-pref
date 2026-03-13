#!/usr/bin/env python3
"""
Ferramentas utilitárias para gerenciar templates n8n e automações do agente `n8n-specialist`.

Funcionalidades:
- listar templates locais
- criar placeholders de credentials
- tentar importar workflows via API do n8n (se `N8N_URL` e `N8N_API_KEY` estiverem setados)
- deploy de todos os templates

Uso: python n8n_tools.py --help
"""
import os
import sys
import argparse
import json
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = ROOT / 'skills' / 'templates' / 'examples'


def list_templates():
    files = sorted(EXAMPLES_DIR.rglob('*.json'))
    for f in files:
        print(f.relative_to(ROOT))


def create_credentials_placeholder(output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    creds = {
        'cred-api': {'type': 'httpRequest', 'notes': 'Preencha com API Key / Bearer / OAuth as needed (do NOT commit).'},
        'cred-google-oauth': {'type': 'oAuth2', 'notes': 'client_id, client_secret, redirect_uri'},
        'cred-authy': {'type': 'httpRequest', 'notes': 'Authy API key'},
        'cred-stripe-webhook': {'type': 'generic', 'notes': 'Webhook secret for signature verification'}
    }
    for name, body in creds.items():
        path = output_dir / f'{name}.json'
        if path.exists():
            print(f'skipping existing {path}')
            continue
        path.write_text(json.dumps(body, indent=2, ensure_ascii=False))
        print(f'created placeholder: {path}')


def import_workflow(file_path: Path, n8n_url: str, api_key: str):
    # Best-effort import to n8n REST API. Endpoint may vary by version.
    url = n8n_url.rstrip('/') + '/workflows/import'
    headers = {'Accept': 'application/json', 'Authorization': f'Bearer {api_key}'}
    files = {'file': (file_path.name, open(file_path, 'rb'), 'application/json')}
    print(f'Importando {file_path.name} -> {url}')
    try:
        r = requests.post(url, headers=headers, files=files, timeout=30)
        print('status', r.status_code)
        print(r.text)
        return r.status_code == 200 or r.status_code == 201
    except Exception as e:
        print('erro ao importar:', e)
        return False


def deploy_all(n8n_url: str | None, api_key: str | None):
    files = sorted(EXAMPLES_DIR.rglob('*.json'))
    for f in files:
        print('\n---')
        print('template:', f)
        if n8n_url and api_key:
            ok = import_workflow(f, n8n_url, api_key)
            if not ok:
                print('Import falhou para', f)
        else:
            print('N8N_URL/N8N_API_KEY não setados. Apenas listando arquivo (sem import).')


def ping(url: str):
    try:
        r = requests.get(url, timeout=10)
        print('status', r.status_code)
        return True
    except Exception as e:
        print('ping failed:', e)
        return False


def main():
    p = argparse.ArgumentParser(description='n8n tools for n8n-specialist')
    sub = p.add_subparsers(dest='cmd')

    sub.add_parser('list', help='Listar templates locais')

    cph = sub.add_parser('create-creds', help='Criar placeholders de credentials')
    cph.add_argument('--out', default='credentials-placeholders', help='Diretório de saída')

    imp = sub.add_parser('import', help='Tentar importar um workflow para n8n via API')
    imp.add_argument('file', type=str, help='Caminho para o JSON do workflow')

    dc = sub.add_parser('deploy-cloud', help='Importar todos os workflows passando URL e API key')
    dc.add_argument('--url', type=str, help='URL do n8n (ex: https://seu-n8n.example.com)')
    dc.add_argument('--api-key', type=str, help='API key do n8n (ou use N8N_API_KEY env)')

    sub.add_parser('deploy-all', help='Deploy/import de todos os templates (se N8N_URL/N8N_API_KEY setados)')

    pingp = sub.add_parser('ping', help='Fazer GET simples para testar endpoint')
    pingp.add_argument('url')

    args = p.parse_args()

    if args.cmd == 'list':
        list_templates()
    elif args.cmd == 'create-creds':
        out = Path(args.out)
        create_credentials_placeholder(out)
    elif args.cmd == 'import':
        n8n_url = os.environ.get('N8N_URL')
        api_key = os.environ.get('N8N_API_KEY')
        if not n8n_url or not api_key:
            print('N8N_URL ou N8N_API_KEY não configurados. Abortando import. Variáveis de ambiente necessárias.')
            sys.exit(2)
        import_workflow(Path(args.file), n8n_url, api_key)
    elif args.cmd == 'deploy-all':
        n8n_url = os.environ.get('N8N_URL')
        api_key = os.environ.get('N8N_API_KEY')
        deploy_all(n8n_url, api_key)
    elif args.cmd == 'deploy-cloud':
        n8n_url = args.url or os.environ.get('N8N_URL')
        api_key = args.api_key or os.environ.get('N8N_API_KEY')
        if not n8n_url or not api_key:
            print('Forneça --url e --api-key, ou configure N8N_URL/N8N_API_KEY no ambiente.')
            sys.exit(2)
        deploy_all(n8n_url, api_key)
    elif args.cmd == 'ping':
        ping(args.url)
    else:
        p.print_help()


if __name__ == '__main__':
    main()
