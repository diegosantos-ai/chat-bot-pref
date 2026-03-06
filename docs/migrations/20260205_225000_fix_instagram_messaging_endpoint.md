# Fix: Instagram Messaging API endpoint

**Data**: 2026-02-05
**Tipo**: Bugfix (codigo)
**Impacto**: Corrige envio de mensagens via Instagram DM

## Problema

O `MetaClient` usava o **Instagram Business Account ID** (`META_PAGE_ID_INSTAGRAM`) como path parameter no endpoint da Instagram Messaging API:

```
POST https://graph.facebook.com/v19.0/{instagram-business-account-id}/messages
```

Isso retornava erro 400: `"(#3) Application does not have the capability to make this API call."`

## Causa Raiz

A Instagram Messaging API exige que o endpoint use o **Facebook Page ID** da pagina vinculada a conta Instagram, nao o Instagram Business Account ID. O endpoint correto e:

```
POST https://graph.facebook.com/v19.0/{facebook-page-id}/messages
```

## Alteracoes

### `app/integrations/meta/client.py`

1. **`__init__`**: Para plataforma `instagram`, `self._page_id` agora usa `META_PAGE_ID_FACEBOOK` (em vez de `META_PAGE_ID_INSTAGRAM`). Adicionado `self._ig_business_id` para manter referencia ao IG Business Account ID se necessario.

2. **`send_message`**: O endpoint agora usa `self._page_id` (Facebook Page ID) diretamente, ignorando o parametro `ig_user_id` (mantido para retrocompatibilidade).

3. **`send_private_reply`**: Ja usava `self._page_id`, agora aponta para o Facebook Page ID corretamente.

## Requisitos no Servidor

- **Nenhuma alteracao de infraestrutura necessaria**. Apenas deploy do codigo atualizado.
- Verificar que `META_PAGE_ID_FACEBOOK` esta configurado corretamente no `.env` do servidor (ja deve estar, pois o Facebook Messenger funciona).
- O token em `META_ACCESS_TOKEN_FACEBOOK` precisa ter a permissao `instagram_manage_messages`.

## Como Validar

1. Fazer deploy do codigo
2. Enviar mensagem DM para a conta Instagram da prefeitura
3. Verificar nos logs que o endpoint agora usa o Facebook Page ID
4. Confirmar que a resposta e enviada com sucesso (HTTP 200)
