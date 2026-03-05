#!/usr/bin/env python3
"""
Script para criar workflow usando o node HTML correto
"""

import requests

N8N_URL = "https://n8n.nexobasis.com.br"
N8N_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlYWE0NTE0Ny1jMTdhLTRmYjYtODRjOC1lYWI2MTdjZjI4YjYiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwianRpIjoiYjU0ZmNiZTEtZTUzZC00NWY4LTg5MTItM2U3MDdlMWE0NjMyIiwiaWF0IjoxNzcwNzY4NDgyfQ.-bflzV7ybUxneGz7Sqcn2WeMgbe-pYTydJEVM8s5pfk"
WORKFLOW_ID = "qrptG5t-wImiIZhyl33e7"

headers = {"X-N8N-API-KEY": N8N_API_KEY, "Content-Type": "application/json"}

# Workflow com node HTML correto
workflow = {
    "name": "Scraping notícias {client_name}",
    "nodes": [
        # 1: Manual Trigger
        {
            "id": "1",
            "name": "Manual",
            "type": "n8n-nodes-base.manualTrigger",
            "typeVersion": 1,
            "position": [220, 280],
        },
        # 2: HTTP - Lista de notícias
        {
            "id": "2",
            "name": "HTTP Lista",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [420, 280],
            "parameters": {
                "url": "https://www.santatereza.pr.gov.br/noticias/",
                "method": "GET",
                "options": {},
            },
        },
        # 3: HTML - Extrair links
        {
            "id": "3",
            "name": "Extrai Links",
            "type": "n8n-nodes-base.html",
            "typeVersion": 1,
            "position": [620, 280],
            "parameters": {
                "operation": "getHtml",
                "attribute": "href",
                "cssSelector": "a[href*='/noticia/']",
                "options": {},
            },
        },
        # 4: Split - Loop
        {
            "id": "4",
            "name": "Loop",
            "type": "n8n-nodes-base.splitInBatches",
            "typeVersion": 3,
            "position": [820, 280],
            "parameters": {"batchSize": 1, "options": {}},
        },
        # 5: HTTP - Página da notícia
        {
            "id": "5",
            "name": "HTTP Detail",
            "type": "n8n-nodes-base.httpRequest",
            "typeVersion": 4.2,
            "position": [1020, 280],
            "parameters": {"url": "={{ $json.href }}", "method": "GET", "options": {}},
        },
        # 6: HTML - Extrair título
        {
            "id": "6",
            "name": "Extrai Titulo",
            "type": "n8n-nodes-base.html",
            "typeVersion": 1,
            "position": [1220, 120],
            "parameters": {
                "operation": "getHtml",
                "cssSelector": "h1, h2, .titulo",
                "options": {},
            },
        },
        # 7: HTML - Extrair conteúdo
        {
            "id": "7",
            "name": "Extrai Conteudo",
            "type": "n8n-nodes-base.html",
            "typeVersion": 1,
            "position": [1220, 280],
            "parameters": {
                "operation": "getHtml",
                "cssSelector": "div.leitura",
                "options": {},
            },
        },
        # 8: HTML - Extrair imagem
        {
            "id": "8",
            "name": "Extrai Imagem",
            "type": "n8n-nodes-base.html",
            "typeVersion": 1,
            "position": [1220, 440],
            "parameters": {
                "operation": "getAttribute",
                "attribute": "src",
                "cssSelector": "article img, .conteudo img",
                "options": {},
            },
        },
        # 9: Set - Montar JSON
        {
            "id": "9",
            "name": "Montar JSON",
            "type": "n8n-nodes-base.set",
            "typeVersion": 3.4,
            "position": [1420, 280],
            "parameters": {
                "mode": "manual",
                "duplicateItem": False,
                "assignments": {
                    "assignments": [
                        {
                            "id": "titulo",
                            "name": "titulo",
                            "value": "={{ $('Extrai Titulo').first().json.html }}",
                            "type": "string",
                        },
                        {
                            "id": "url",
                            "name": "url",
                            "value": "={{ $('Loop').item.json.href }}",
                            "type": "string",
                        },
                        {
                            "id": "texto",
                            "name": "texto",
                            "value": "={{ $('Extrai Conteudo').first().json.html }}",
                            "type": "string",
                        },
                        {
                            "id": "foto",
                            "name": "foto",
                            "value": "={{ $('Extrai Imagem').first().json.attribute }}",
                            "type": "string",
                        },
                    ]
                },
                "options": {},
            },
        },
        # 10: Wait
        {
            "id": "10",
            "name": "Aguardar",
            "type": "n8n-nodes-base.wait",
            "typeVersion": 1,
            "position": [1620, 280],
            "parameters": {"amount": 30, "unit": "seconds", "options": {}},
        },
    ],
    "connections": {
        "Manual": {"main": [[{"node": "HTTP Lista", "type": "main", "index": 0}]]},
        "HTTP Lista": {
            "main": [[{"node": "Extrai Links", "type": "main", "index": 0}]]
        },
        "Extrai Links": {"main": [[{"node": "Loop", "type": "main", "index": 0}]]},
        "Loop": {"main": [[{"node": "HTTP Detail", "type": "main", "index": 0}]]},
        "HTTP Detail": {
            "main": [
                [
                    {"node": "Extrai Titulo", "type": "main", "index": 0},
                    {"node": "Extrai Conteudo", "type": "main", "index": 0},
                    {"node": "Extrai Imagem", "type": "main", "index": 0},
                ]
            ]
        },
        "Extrai Titulo": {
            "main": [[{"node": "Montar JSON", "type": "main", "index": 0}]]
        },
        "Extrai Conteudo": {
            "main": [[{"node": "Montar JSON", "type": "main", "index": 0}]]
        },
        "Extrai Imagem": {
            "main": [[{"node": "Montar JSON", "type": "main", "index": 0}]]
        },
        "Montar JSON": {"main": [[{"node": "Aguardar", "type": "main", "index": 0}]]},
        "Aguardar": {"main": [[{"node": "Loop", "type": "main", "index": 0}]]},
    },
    "settings": {"executionOrder": "v1"},
}

url = f"{N8N_URL}/api/v1/workflows/{WORKFLOW_ID}"
response = requests.put(url, headers=headers, json=workflow)

print(f"Status: {response.status_code}")
if response.status_code in [200, 201]:
    print("✅ Workflow atualizado com node HTML correto!")
else:
    print(f"❌ Erro: {response.text[:1000]}")
