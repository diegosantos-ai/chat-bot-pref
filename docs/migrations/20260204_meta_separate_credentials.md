# Migration: Separação de Credenciais Meta (Facebook/Instagram)

**Data:** 2026-02-04  
**Versão:** v1.2  
**Status:** Aplicar no próximo deploy

## Resumo

Refatoração das variáveis de ambiente para suportar credenciais separadas para Facebook e Instagram, permitindo que cada plataforma tenha seu próprio App Secret e Page ID.

## Mudanças no Código

### 1. Novas Variáveis no `.env`

```bash
# Facebook
META_PAGE_ID_FACEBOOK=1017832368069356
META_APP_SECRET_FACEBOOK=c5788367a89a260447acbedd57b8e52f
META_ACCESS_TOKEN_FACEBOOK=<token_facebook>

# Instagram
META_PAGE_ID_INSTAGRAM=17841444437465719
META_APP_SECRET_INSTAGRAM=
META_ACCESS_TOKEN_INSTAGRAM=<token_instagram>

# Webhook Verify Token (comum para ambos)
META_WEBHOOK_VERIFY_TOKEN=terezia_dev_2026
```

### 2. Arquivos Modificados

- `app/settings.py`: Adicionadas novas variáveis com sufixos `_FACEBOOK` e `_INSTAGRAM`
- `app/integrations/meta/security.py`: Verificação de assinatura suporta ambos os secrets
- `app/integrations/meta/client.py`: Seleção de page ID baseada na plataforma
- `app/channels/meta_sender.py`: Método `_get_page_id()` para retornar ID correto
- `.env`: Atualizado com novas variáveis

### 3. Retrocompatibilidade

As variáveis antigas (`META_PAGE_ID`, `META_APP_SECRET`) ainda funcionam como fallback se as novas não estiverem configuradas. Serão removidas em versão futura.

## Instruções de Deploy

### 1. Antes do Deploy

Faça backup do `.env` atual:
```bash
cp .env .env.backup.$(date +%Y%m%d)
```

### 2. Durante o Deploy

1. Copiar o novo arquivo `.env` para o servidor
2. Preencher as novas variáveis:
   - `META_PAGE_ID_INSTAGRAM`: ID da conta business do Instagram (ex: 17841444437465719)
   - `META_APP_SECRET_INSTAGRAM`: App Secret específico para Instagram (se diferente do Facebook)

3. Reiniciar a aplicação:
```bash
sudo systemctl restart terezia-api
```

### 3. Verificação Pós-Deploy

Verifique se o webhook está funcionando:
```bash
tail -f /var/log/terezia-api.log | grep -E "(instagram|facebook|webhook)"
```

Envie mensagens de teste tanto no Facebook quanto no Instagram e verifique se ambos são processados corretamente.

## Rollback

Se necessário, restaure o backup:
```bash
cp .env.backup.20260204 .env
sudo systemctl restart terezia-api
```

## Notas

- O App Secret geralmente é o mesmo para Facebook e Instagram quando vêm do mesmo aplicativo Meta
- O Page ID do Instagram é na verdade o Instagram Business Account ID
- Para obter o Instagram Business Account ID, use o endpoint: `https://graph.facebook.com/v19.0/{page-id}?fields=instagram_business_account`
