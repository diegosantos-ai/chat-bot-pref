# Scripts de Configuração do Grafana

Este diretório contém scripts para configurar o Grafana com o PostgreSQL local.

## Arquivos

### `setup_grafana.py`

Script principal para configurar o Grafana automaticamente.

**O que faz:**
1. Verifica conexão com PostgreSQL local
2. Aguarda o Grafana ficar disponível
3. Configura a fonte de dados PostgreSQL
4. Importa o dashboard oficial do {bot_name}

**Uso:**
```bash
# Certifique-se de que o Grafana está rodando
docker-compose up -d grafana

# Execute o script de configuração
python scripts/setup_grafana.py
```

**Requisitos:**
- PostgreSQL local configurado (terezia/pandora@localhost:5432)
- Grafana rodando (docker-compose up -d grafana)
- Python 3.11+ com requests instalado

## Configuração Manual

Se preferir configurar manualmente:

### 1. Acesse o Grafana
- URL: http://localhost:3001
- Usuário: admin
- Senha: admin

### 2. Configure a Fonte de Dados
1. Vá em Configuration > Data Sources
2. Clique em "Add data source"
3. Selecione "PostgreSQL"
4. Configure:
   - Host: `host.docker.internal:5432`
   - Database: `terezia`
   - User: `terezia`
   - Password: `pandora`
   - SSL Mode: `disable`
5. Clique em "Save & Test"

### 3. Importe o Dashboard
1. Vá em Dashboards > Import
2. Carregue o arquivo `grafana/dashboard_terezia.json`
3. Selecione a fonte de dados "PostgreSQL"
4. Clique em "Import"

## Solução de Problemas

### Grafana não consegue se conectar ao PostgreSQL
- Verifique se o PostgreSQL está rodando: `sudo systemctl status postgresql@16-main`
- Teste a conexão manualmente: `PGPASSWORD=pandora psql -h localhost -U terezia -d terezia`
- Verifique se o Docker tem acesso ao host: `docker run --rm alpine ping host.docker.internal`

### Dashboard não mostra dados
- Verifique se as tabelas `audit_events` e `rag_queries` existem
- Execute uma consulta manual: `SELECT COUNT(*) FROM audit_events;`
- Verifique se o time range do dashboard está correto

## Notas

- O Grafana usa o mesmo banco de dados da aplicação para garantir consistência
- As tabelas são otimizadas para leitura de observabilidade
- Não há sobrecarga significativa, pois o Grafana faz apenas consultas SELECT
