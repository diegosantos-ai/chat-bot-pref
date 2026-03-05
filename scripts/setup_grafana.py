#!/usr/bin/env python3
"""
Script para configurar o Grafana com o PostgreSQL local.

Este script:
1. Verifica se o PostgreSQL local está acessível
2. Configura a fonte de dados do PostgreSQL no Grafana
3. Importa o dashboard oficial

Uso: python scripts/setup_grafana.py
"""

import requests
import json
import time
import subprocess
import sys
import os
from pathlib import Path


def check_postgres_connection():
    """Verifica se o PostgreSQL local está acessível."""
    print("🔍 Verificando conexão com PostgreSQL local...")
    try:
        env = os.environ.copy()
        env["PGPASSWORD"] = "pandora"
        result = subprocess.run(
            [
                "psql",
                "-h",
                "localhost",
                "-U",
                "terezia",
                "-d",
                "terezia",
                "-c",
                "SELECT 1",
            ],
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        print("✅ PostgreSQL local está acessível!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao conectar ao PostgreSQL: {e.stderr}")
        return False


def wait_for_grafana(grafana_url: str):
    """Aguarda o Grafana ficar disponível."""
    print("🕒 Aguardando Grafana iniciar...")
    for i in range(30):
        try:
            response = requests.get(f"{grafana_url}/api/health", timeout=5)
            if response.status_code == 200:
                print("✅ Grafana está disponível!")
                return True
        except requests.RequestException:
            time.sleep(2)
    print("❌ Grafana não ficou disponível após 60 segundos")
    return False


def get_grafana_auth(session: requests.Session, grafana_url: str) -> bool:
    """Autentica no Grafana usando o endpoint de login e mantém uma sessão.

    Lê a senha do admin em `GRAFANA_ADMIN_PASSWORD` (fallback: 'admin').
    """
    admin_user = os.environ.get("GRAFANA_ADMIN_USER", "admin")
    admin_pass = os.environ.get("GRAFANA_ADMIN_PASSWORD", "admin")
    print("🔐 Autenticando no Grafana...")
    try:
        resp = session.post(
            f"{grafana_url}/login",
            data={"user": admin_user, "password": admin_pass},
            timeout=10,
            allow_redirects=False,
        )
        # Grafana returns 200 even on failed login with a page; check cookie
        if resp.status_code in (200, 302) and any(
            cookie.name.startswith("grafana") for cookie in session.cookies
        ):
            print("✅ Autenticação bem-sucedida!")
            return True
        else:
            print(f"❌ Falha na autenticação: status={resp.status_code}")
            return False
    except requests.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return False


def configure_postgres_datasource(session: requests.Session, grafana_url: str):
    """Configura a fonte de dados do PostgreSQL no Grafana."""
    print("🛠️ Configurando fonte de dados PostgreSQL...")

    # Verificar se já existe
    try:
        response = session.get(
            f"{grafana_url}/api/datasources/name/PostgreSQL",
            timeout=10,
        )
        if response.status_code == 200:
            print("ℹ️  Fonte de dados já existe, atualizando...")
            datasource_id = response.json()["id"]
            method = "PUT"
            url = f"{grafana_url}/api/datasources/{datasource_id}"
        else:
            print("ℹ️  Criando nova fonte de dados...")
            method = "POST"
            url = f"{grafana_url}/api/datasources"
    except requests.RequestException as e:
        print(f"⚠️  Não foi possível verificar fonte de dados existente: {e}")
        method = "POST"
        url = "http://localhost:3001/api/datasources"

    datasource_config = {
        "name": "PostgreSQL",
        "type": "postgres",
        "url": "host.docker.internal:5432",
        "database": "terezia",
        "user": "terezia",
        "secureJsonData": {"password": "pandora"},
        "jsonData": {
            "sslmode": "disable",
            "postgresVersion": 1600,
            "timescaledb": False,
        },
    }

    try:
        response = session.request(
            method,
            url,
            json=datasource_config,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if response.status_code in [200, 201]:
            print("✅ Fonte de dados PostgreSQL configurada com sucesso!")
            return True
        else:
            print(f"❌ Falha ao configurar fonte de dados: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"❌ Erro ao configurar fonte de dados: {e}")
        return False


def import_dashboard(session: requests.Session, grafana_url: str):
    """Importa o dashboard oficial do {bot_name}."""
    print("📊 Importando dashboard...")

    dashboard_path = Path("/root/pilot-atendimento/grafana/dashboard_terezia.json")
    if not dashboard_path.exists():
        print(f"❌ Dashboard não encontrado em {dashboard_path}")
        return False

    try:
        with open(dashboard_path, "r") as f:
            dashboard_json = json.load(f)
    except Exception as e:
        print(f"❌ Erro ao ler arquivo de dashboard: {e}")
        return False

    # Configurar dashboard para usar a fonte de dados PostgreSQL
    dashboard_json["datasource"] = {"type": "postgres", "uid": "PostgreSQL"}

    try:
        response = session.post(
            f"{grafana_url}/api/dashboards/import",
            json={"dashboard": dashboard_json, "folderId": 0, "overwrite": True},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        if response.status_code == 200:
            print("✅ Dashboard importado com sucesso!")
            return True
        else:
            print(f"❌ Falha ao importar dashboard: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"❌ Erro ao importar dashboard: {e}")
        return False


def main():
    print("🚀 Configurando Grafana para {bot_name}")
    print("=" * 50)

    # Verificar PostgreSQL
    if not check_postgres_connection():
        print("\n❌ Abortando: PostgreSQL não está acessível")
        sys.exit(1)

    grafana_url = os.environ.get("GRAFANA_URL", "http://localhost:3001")

    # Verificar se Grafana está rodando
    if not wait_for_grafana(grafana_url):
        print("\n❌ Abortando: Grafana não está disponível")
        sys.exit(1)

    # Autenticar
    session = requests.Session()
    if not get_grafana_auth(session, grafana_url):
        print("\n❌ Abortando: Falha na autenticação")
        sys.exit(1)

    # Configurar fonte de dados
    if not configure_postgres_datasource(session, grafana_url):
        print("\n⚠️  Configuração da fonte de dados falhou, mas continuando...")

    # Importar dashboard
    if not import_dashboard(session, grafana_url):
        print("\n⚠️  Importação do dashboard falhou, mas continuando...")

    print("\n" + "=" * 50)
    print("✅ Configuração do Grafana concluída!")
    print(f"📊 Acesse o dashboard em: {grafana_url}")
    print("   Usuário: admin")
    print("   Senha: (verifique GRAFANA_ADMIN_PASSWORD or secret manager)")


if __name__ == "__main__":
    main()
