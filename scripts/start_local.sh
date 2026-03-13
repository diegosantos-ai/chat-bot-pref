#!/bin/bash
# Inicia o ambiente local do Chat Pref com Docker Compose.

set -e

if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
else
    echo -e "\033[1;31mDocker Compose nao encontrado. Instale o plugin 'docker compose' ou 'docker-compose'.\033[0m"
    exit 1
fi

echo -e "\033[1;36m=========================================\033[0m"
echo -e "\033[1;36m      Iniciando Chat Pref - Local Demo   \033[0m"
echo -e "\033[1;36m=========================================\033[0m"
echo ""

echo -e "\n\033[1;33mSubindo containers com Docker Compose...\033[0m"
"${COMPOSE_CMD[@]}" -f docker-compose.local.yml up -d --build

echo -e "\n\033[1;36m=========================================\033[0m"
echo -e "\033[1;32m🚀 Ambiente Iniciado com Sucesso\033[0m"
echo -e "\033[1;36m=========================================\033[0m"
echo -e "🌐 Admin Panel (Frontend): http://localhost:8080"
echo -e "⚙️  Admin Backend (API):   http://localhost:8093/health"
echo -e "🤖 Chatbot Core (API):    http://localhost:8101/health"
echo -e "\033[1;36m=========================================\033[0m"
echo -e "\nPara encerrar: ${COMPOSE_CMD[*]} -f docker-compose.local.yml down"
