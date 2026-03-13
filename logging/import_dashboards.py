#!/usr/bin/env python3
"""
Import all {bot_name} dashboards to Grafana
"""

import json
import sys
import requests

GRAFANA_URL = "http://localhost:3001"
GRAFANA_USER = "admin"
GRAFANA_PASS = "admin24052014"
DASHBOARDS_DIR = "/root/pilot-atendimento/dashboards"

# Dashboards to import
DASHBOARDS = [
    "01-overview-services.json",
    "02-terezia-api.json",
    "03-nginx.json",
    "04-postgresql.json",
    "05-n8n.json",
    "06-loki-infrastructure.json",
]


def get_or_create_folder():
    """Get or create folder for dashboards"""
    response = requests.get(
        f"{GRAFANA_URL}/api/folders", auth=(GRAFANA_USER, GRAFANA_PASS)
    )
    folders = response.json()

    for folder in folders:
        if folder.get("title") == "{bot_name} Services":
            return folder["uid"]

    # Create folder
    response = requests.post(
        f"{GRAFANA_URL}/api/folders",
        auth=(GRAFANA_USER, GRAFANA_PASS),
        json={"title": "{bot_name} Services"},
    )
    return response.json().get("uid")


def import_dashboard(filename):
    """Import a single dashboard"""
    filepath = f"{DASHBOARDS_DIR}/{filename}"

    try:
        with open(filepath, "r") as f:
            dashboard_data = json.load(f)

        # Remove 'id' if present to avoid conflicts
        if "id" in dashboard_data.get("dashboard", {}):
            del dashboard_data["dashboard"]["id"]

        payload = {
            "dashboard": dashboard_data.get("dashboard", {}),
            "folderId": FOLDER_ID,
            "overwrite": True,
        }

        response = requests.post(
            f"{GRAFANA_URL}/api/dashboards/db",
            auth=(GRAFANA_USER, GRAFANA_PASS),
            json=payload,
        )

        result = response.json()
        if result.get("status") == "success":
            return True, filename, None
        else:
            return False, filename, result.get("message", "Unknown error")

    except FileNotFoundError:
        return False, filename, "File not found"
    except json.JSONDecodeError as e:
        return False, filename, f"Invalid JSON: {e}"
    except Exception as e:
        return False, filename, f"Error: {e}"


def main():
    global FOLDER_ID

    print("=" * 60)
    print("📊 Importando Dashboards para Grafana")
    print("=" * 60)
    print()

    # Check connection
    try:
        response = requests.get(
            f"{GRAFANA_URL}/api/health", auth=(GRAFANA_USER, GRAFANA_PASS)
        )
        if response.status_code != 200:
            print(f"❌ Erro: Grafana não está acessível em {GRAFANA_URL}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Erro ao conectar: {e}")
        sys.exit(1)

    print("✅ Grafana está online")
    print()

    # Get or create folder
    print("📁 Configurando pasta de dashboards...")
    FOLDER_ID = get_or_create_folder()
    print(f"✅ Pasta '{bot_name} Services' pronta (ID: {FOLDER_ID})")  # noqa: F821
    print()

    # Import dashboards
    print("📈 Importando dashboards...")
    print()

    imported = 0
    failed = 0

    for dashboard_file in DASHBOARDS:
        success, filename, error = import_dashboard(dashboard_file)

        if success:
            print(f"✅ {filename} - Importado com sucesso!")
            imported += 1
        else:
            print(f"❌ {filename} - Erro: {error}")
            failed += 1

    print()
    print("=" * 60)
    print("📊 Importação Concluída!")
    print("=" * 60)
    print()
    print(f"✅ Importados: {imported}")
    print(f"❌ Falhas: {failed}")
    print()
    print("📊 Acesse os dashboards em:")
    print("   https://nexobasis.com.br/grafana")
    print()


if __name__ == "__main__":
    main()
