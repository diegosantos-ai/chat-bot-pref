# Central de Logs - {bot_name}

## 🎉 Instalação Concluída!

A centralização de logs está **ativa e funcionando**!

## 📊 Acesso

**URL do Grafana:** https://nexobasis.com.br/grafana  
**Usuário:** admin  
**Senha:** admin24052014

**Explorar Logs:** https://nexobasis.com.br/grafana/explore

---

## 🔍 Como Usar

### 1. Acessar o Explore
1. Vá para https://nexobasis.com.br/grafana/explore
2. Selecione o data source **"Loki"** no dropdown

### 2. Queries Básicas (LogQL)

```logql
# Logs do Nginx
{job="nginx"}

# Logs do Nginx - apenas access
{job="nginx", logtype="access"}

# Logs do Nginx - apenas errors
{job="nginx", logtype="error"}

# Todos os logs do journald
{job="systemd-journal"}

# Logs de autenticação (SSH/login)
{job="auth"}

# Logs do sistema
{job="syslog"}

# Buscar texto específico
{job="nginx"} |= "webhook"

# Buscar erros
{job="nginx"} |= "error"
```

### 3. Filtros Avançados

```logql
# Erros em qualquer serviço
{job=~".+"} |= "ERROR"

# Combinar múltiplos jobs
{job=~"nginx|auth"}

# Busca por método HTTP no nginx
{job="nginx", logtype="access"} | json | request_method="POST"
```

---

## 📁 Estrutura de Labels

### Jobs Disponíveis:
- `nginx` - Logs do nginx (access e error)
- `systemd-journal` - Logs de todos os serviços systemd (quando disponível)
- `auth` - Logs de autenticação (/var/log/auth.log)
- `syslog` - Logs do sistema (/var/log/syslog)
- `postgresql` - Logs do PostgreSQL (via journald)

### Labels Adicionais:
- `logtype` - Tipo de log (access, error) para nginx
- `unit` - Nome do serviço systemd (quando disponível)
- `host` - Hostname
- `level` - Nível de log (debug, info, warning, error)

---

## 🎛️ Serviços em Execução

```bash
# Ver status
docker ps | grep -E "(loki|promtail)"

# Logs do Loki
docker logs -f terezia-loki

# Logs do Promtail
docker logs -f terezia-promtail

# Reiniciar
cd /root/pilot-atendimento/logging
docker compose -f docker-compose-loki.yml restart

# Parar
docker compose -f docker-compose-loki.yml down
```

---

## ⚙️ Configuração

**Arquivos:**
- `/root/pilot-atendimento/logging/loki-config.yml` - Configuração do Loki
- `/root/pilot-atendimento/logging/promtail-config.yml` - Configuração do Promtail
- `/root/pilot-atendimento/logging/docker-compose-loki.yml` - Docker Compose

**Retenção:** 7 dias (logs antigos são automaticamente removidos)

**Porta:** 3100 (Loki API - acesso local apenas)

---

## 🔧 Solução de Problemas

### Não aparecem logs?
1. Verifique se os containers estão rodando: `docker ps`
2. Verifique logs do Promtail: `docker logs terezia-promtail`
3. Aguarde 1-2 minutos para a primeira ingestão

### Loki não responde?
```bash
# Verificar status
curl http://localhost:3100/ready

# Reiniciar
docker restart terezia-loki
```

### Dashboard não aparece?
O dashboard pode ser importado manualmente:
1. Grafana → Dashboards → Import
2. Upload JSON: `/root/pilot-atendimento/dashboards/terezia-logs-dashboard.json`

---

## 📝 Notas

- **Logs Docker**: A descoberta automática de containers Docker está temporariamente desabilitada devido a incompatibilidade de versão de API. Os logs do journald capturam os serviços principais.
- **Performance**: O Loki é otimizado para consultas de label, não para buscas de texto completo em grandes volumes.
- **Retenção**: Logs são mantidos por 7 dias e automaticamente removidos após esse período.

---

## 💡 Dicas

- Use `{job="nginx"} |= "500"` para ver erros 500
- Use `{job="nginx"} | json` para parsear logs JSON do nginx
- A busca com `|=` é mais rápida que `|~` (regex)
- Filtros de label são mais eficientes que filtros de linha

---

## 📞 Suporte

Para problemas ou dúvidas, verifique:
1. Logs do Loki: `docker logs terezia-loki`
2. Logs do Promtail: `docker logs terezia-promtail`
3. Configurações em `/root/pilot-atendimento/logging/`
