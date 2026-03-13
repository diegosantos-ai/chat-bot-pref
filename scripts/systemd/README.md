# Serviços Systemd para {bot_name}

Este diretório contém os arquivos de configuração do systemd para iniciar automaticamente a API e o Grafana do {bot_name} com a máquina.

## Arquivos

### `terezia-api.service`
Serviço systemd para a API {bot_name}.

**Características:**
- Inicia a API usando uvicorn
- Dependências: network, postgresql, docker
- Reinicia automaticamente em caso de falha
- Logs via syslog

### `terezia-grafana.service`
Serviço systemd para o Grafana.

**Características:**
- Inicia o Grafana usando docker-compose
- Dependências: network, docker
- Reinicia automaticamente em caso de falha
- Logs via syslog

### `setup_systemd.sh`
Script para configurar automaticamente os serviços systemd.

**O que faz:**
1. Copia os arquivos de serviço para `/etc/systemd/system/terezia/`
2. Cria symlinks para ativação
3. Recarrega o daemon do systemd
4. Habilita os serviços para iniciar na boot
5. Inicia os serviços
6. Mostra o status

## Como Usar

### Instalação

```bash
# Torne o script executável
chmod +x /root/chat-bot-pref/scripts/systemd/setup_systemd.sh

# Execute o script de configuração (requer sudo)
sudo bash /root/chat-bot-pref/scripts/systemd/setup_systemd.sh
```

### Comandos Manuais

Se preferir configurar manualmente:

```bash
# Copiar arquivos de serviço
sudo cp /root/chat-bot-pref/scripts/systemd/*.service /etc/systemd/system/

# Recarregar daemon
sudo systemctl daemon-reload

# Habilitar serviços
sudo systemctl enable terezia-api.service
sudo systemctl enable terezia-grafana.service

# Iniciar serviços
sudo systemctl start terezia-api.service
sudo systemctl start terezia-grafana.service
```

## Gerenciamento

### Verificar Status

```bash
# Verificar status da API
sudo systemctl status terezia-api.service

# Verificar status do Grafana
sudo systemctl status terezia-grafana.service
```

### Verificar Logs

```bash
# Logs da API (em tempo real)
sudo journalctl -u terezia-api -f

# Logs do Grafana (em tempo real)
sudo journalctl -u terezia-grafana -f

# Ver logs históricos
sudo journalctl -u terezia-api --since "2026-01-25"
```

### Reiniciar Serviços

```bash
# Reiniciar API
sudo systemctl restart terezia-api

# Reiniciar Grafana
sudo systemctl restart terezia-grafana
```

### Parar Serviços

```bash
# Parar API
sudo systemctl stop terezia-api

# Parar Grafana
sudo systemctl stop terezia-grafana
```

### Desabilitar Serviços

```bash
# Desabilitar inicialização automática
sudo systemctl disable terezia-api
sudo systemctl disable terezia-grafana
```

## Solução de Problemas

### Serviço não inicia

1. Verifique os logs:
   ```bash
   sudo journalctl -u terezia-api -xe
   ```

2. Verifique se as dependências estão rodando:
   ```bash
   sudo systemctl status postgresql
   sudo systemctl status docker
   ```

3. Teste a execução manual:
   ```bash
   cd /root/chat-bot-pref
   source venv/bin/activate
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### Permissão negada

Se receber erros de permissão:

```bash
# Verifique as permissões do diretório
sudo chown -R root:root /root/chat-bot-pref

# Verifique permissões do venv
sudo chmod -R 755 /root/chat-bot-pref/venv
```

### Docker não está rodando

```bash
# Iniciar docker
sudo systemctl start docker

# Habilitar docker na boot
sudo systemctl enable docker
```

## Notas

- Os serviços são configurados para iniciar automaticamente na boot
- Ambos os serviços têm reinício automático em caso de falha
- Os logs são enviados para o syslog e podem ser visualizados com `journalctl`
- Certifique-se de que o PostgreSQL e o Docker estejam instalados e configurados
