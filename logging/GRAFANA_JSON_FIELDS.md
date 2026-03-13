# Como Usar Campos JSON no Grafana

## 📊 Visão Geral

Os logs do {bot_name} agora incluem JSON estruturado que pode ser visualizado em colunas separadas no Grafana.

## 🖱️ Como Visualizar os Campos

### Passo a Passo:

1. **Acesse o Dashboard**
   - Vá em: https://nexobasis.com.br/grafana
   - Dashboards → {bot_name} Services
   - Clique em: **{bot_name} - API Logs (Parsed)**

2. **Expanda um Log**
   - Clique na seta (▶) ao lado esquerdo de qualquer log
   - Os campos JSON serão expandidos

3. **Visualize os Campos Extraídos**

### Exemplo de Log Expandido:

```
📋 Detalhes do Log
├── timestamp: 2026-02-04T13:22:18.381420Z
├── level: INFO
├── logger: app.integrations.meta.client
├── message: Mensagem enviada com sucesso via FACEBOX
└── taskName: starlette.middleware.base...
```

---

## 🎨 Dashboards Disponíveis

### 1. {bot_name} - API Logs
Dashboard básico com todos os logs
📌 URL: https://nexobasis.com.br/grafana/d/terezia-api-logs

### 2. {bot_name} - API Logs (JSON)  
Dashboard com JSON prettificado
📌 URL: https://nexobasis.com.br/grafana/d/terezia-api-logs-json

### 3. {bot_name} - API Logs (Parsed) ⭐ **Recomendado**
Dashboard com:
- Logs com campos extraídos
- Gráficos por nível (INFO/WARNING/ERROR)
- Por logger/origem
- Filtros para ERROS e Webhooks
📌 URL: https://nexobasis.com.br/grafana/d/terezia-api-logs-parsed

---

## 📈 Campos Disponíveis

| Campo | Descrição | Exemplo |
|-------|-----------|---------|
| `timestamp` | Data/hora ISO do evento | 2026-02-04T13:22:18.381420Z |
| `level` | Nível do log | INFO, WARNING, ERROR, CRITICAL |
| `logger` | Origem do log | app.integrations.meta.client |
| `message` | Mensagem descritiva | Mensagem enviada via FACEBOOK |
| `taskName` | Task que gerou o log | starlette.middleware... |

---

## 🔍 Queries LogQL Úteis

### Filtrar por Nível

```logql
{unit="terezia-api.service"} | json | level="ERROR"
{unit="terezia-api.service"} | json | level=~"ERROR|CRITICAL"
{unit="terezia-api.service"} | json | level!="INFO"
```

### Filtrar por Logger

```logql
{unit="terezia-api.service"} | json | logger=~"app.integrations.*"
{unit="terezia-api.service"} | json | logger="httpx"
```

### Buscar no Message

```logql
{unit="terezia-api.service"} | json | message=~"webhook|WEBHOOK"
{unit="terezia-api.service"} | json | message!~"health|ping"
```

### Combinar Filtros

```logql
{unit="terezia-api.service"} | json | level="ERROR" or level="CRITICAL"
```

---

## 🎛️ Painéis do Dashboard "{bot_name} - API Logs (Parsed)"

### Painel 1: Todos os Logs
- Mostra todos os logs com campos expandidos
- Clique em qualquer log para ver detalhes

### Painel 2: Por Nível (Pizza)
- Visualização rápida da distribuição de níveis
- INFO vs WARNING vs ERROR

### Painel 3: Por Logger (Pizza)  
- Mostra quais módulos estão gerando mais logs
- Útil para identificar módulos problemáticos

### Painel 4: Taxa de Logs/min
- Gráfico de linha mostrando atividade ao longo do tempo

### Painel 5: Apenas ERROS
- Filtro para ver só erros e críticos

### Painel 6: Webhooks Recebidos
- Filtro específico para logs de webhook

---

## 💡 Dicas

### Como usar detected fields:
1. Clique no log para expandir
2. Use o botão "Detected fields" para ver todos os campos
3. Clique em um campo para copiar o valor

### Como criar filtro rápido:
1. Clique no valor de um campo (ex: "ERROR")
2. Selecione "Show values" ou "Filter out"
3. O filtro é aplicado automaticamente

### Atalhos:
- `f` → Abrir menu de filtros
- `o` → Alternar modo de visualização
- `Enter` → Expandir/recuar log selecionado

---

## 🔧 Troubleshooting

### Os campos não aparecem?
1. Verifique se o log contém JSON válido
2. Clique em "Toggle parsed fields" no painel
3. Aguarde alguns segundos para refresh

### Logs muito longos?
1. Use `wrapLogMessage: false` para não quebrar linhas
2. Use o campo "message" para ver só o texto

### Query não retorna dados?
1. Verifique se há logs no período selecionado
2. Teste a query: `{unit="terezia-api.service"}`
3. Expanda a janela de tempo (mude de "1h" para "6h")

---

## 📞 Suporte

Se tiver dúvidas:
1. Verifique os logs do Promtail: `docker logs terezia-promtail`
2. Verifique se há dados no Loki: Query `{unit="terezia-api.service"}`
3. Entre em contato com a equipe de desenvolvimento
