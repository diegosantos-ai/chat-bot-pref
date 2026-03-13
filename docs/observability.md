# Observabilidade — {bot_name} (Fase 5)

Objetivo: garantir visibilidade de saúde, qualidade e segurança do atendimento, com métricas e alertas acionáveis.

## KPIs principais
- Disponibilidade API (SLA): >= 99.5%
- Latência p95 de resposta: < 2s
- Taxa de erro (5xx): < 1%
- Fallback rate (24h): < 12%
- Crises detectadas (suicídio/violência): 0 falso-negativos
- RAG: `melhor_score` p50 >= 0.6 e sem picos de `sem_documentos`

## Métricas (fonte: PostgreSQL)
- Volume por tipo de resposta (SUCCESS, FALLBACK, BLOCKED, ESCALATED)
- Fallbacks por motivo (out_of_scope, no_docs_found, policy_blocked)
- Crises/blocked por período e canal
- Erros por tipo/código
- Latência média, p90 e p95 por canal (tempo_resposta_ms)
- RAG: consultas sem docs e `melhor_score` mais baixo

## Logs e Correlação
- Campos-chave: id_requisicao, id_mensagem_externa, canal, tipo_superficie, intencao, decisao, tipo_resposta
- Política de retenção: 180 dias (oltp) + agregados/relatórios mensais

## Alertas (sugestões)
- API 5xx > 1% por 5m
- p95 tempo_resposta_ms > 3s por 10m
- FALLBACK rate > 20% por 15m
- Crises bloqueadas > 0 nos últimos 5m (notificação imediata)
- RAG `sem_documentos` > 10 em 15m

## Dashboards (Views SQL)
Use `analytics/v1/views.sql` para criar views base de observabilidade:
- v_events_last_24h
- v_perf_channel_24h
- v_fallbacks_24h
- v_errors_24h
- v_crisis_48h
- v_rag_no_docs_24h
- v_intents_7d

## Grafana (Monitoramento Visual)
O projeto inclui um dashboard pré-configurado no Grafana.

 ### Como Acessar
1. Suba os serviços: `docker-compose up -d grafana`
2. Acesse: `http://localhost:3001`
3. Login padrão: `admin` / `admin`

 ### Configuração Inicial
 - O Grafana está configurado para conectar ao PostgreSQL local (mesmo banco usado pela aplicação).
 - Para importar o dashboard oficial:
  1. Vá em Dashboards > Import.
  2. Carregue o arquivo `grafana/dashboard_terezia.json`.
  3. Selecione o datasource PostgreSQL configurado.

### O que monitorar no painel
- **Latência p95**: Se subir acima de 3s, investigue a API da OpenAI ou gargalos no banco.
- **Taxa de Fallback**: Se > 20%, revise a base RAG (novos documentos necessários).
- **Erros 5xx**: Falhas técnicas graves.
- **Top Perguntas sem Resposta**: Use para priorizar a criação de novos conteúdos Markdown.

## Boas práticas
- Executar ANALYZE periódico; revisar índices conforme consultas
- Consultas de dashboard via views (evitar full scans repetidos)
- Amostragem de logs em alto volume; materializar visões quando necessário

## Operação
- Checklist diário: quedas, taxa de erro, mudanças em fallbacks e crises
- Semanal: revisão de perguntas sem docs (alimentar base RAG)
- Mensal: auditoria de retenção/expurgo e restauração de backup de teste
