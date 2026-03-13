#!/bin/bash
# Inicia a demonstração do Nexo Gov SaaS localmente.

echo -e "\033[1;36m=========================================\033[0m"
echo -e "\033[1;36m   Iniciando Nexo Gov SaaS - Local Demo  \033[0m"
echo -e "\033[1;36m=========================================\033[0m"
echo ""

echo -e "\033[1;33mVerificando rede infra_nexo-network...\033[0m"
if ! docker network ls | grep -q "infra_nexo-network"; then
    echo -e "\033[1;33mRede infra_nexo-network não encontrada. Criando rede local bridge...\033[0m"
    docker network create infra_nexo-network
    echo -e "\033[1;32mRede criada com sucesso.\033[0m"
else
    echo -e "\033[1;32mRede infra_nexo-network já existe.\033[0m"
fi

echo -e "\n\033[1;33mSubindo containers com Docker Compose...\033[0m"
docker-compose -f docker-compose.local.yml up -d --build

if [ $? -ne 0 ]; then
    echo -e "\n\033[1;31mErro ao subir o Docker Compose. Verifique os logs acima.\033[0m"
    exit 1
fi

echo -e "\n\033[1;36m=========================================\033[0m"
echo -e "\033[1;32m🚀 Ambiente Iniciado com Sucesso\033[0m"
echo -e "\033[1;36m=========================================\033[0m"
echo -e "🌐 Admin Panel (Frontend): http://localhost:8080"
echo -e "⚙️  Admin Backend (API):   http://localhost:8093/health"
echo -e "🤖 Chatbot Core (API):    http://localhost:8101/health"
echo -e "\033[1;36m=========================================\033[0m"
echo -e "\nPara encerrar: docker-compose -f docker-compose.local.yml down"
