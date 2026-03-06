# Migration: Instagram API with Instagram Login

**Data**: 2026-02-11
**Autor**: {bot_name} Dev Team
**Tipo**: Breaking Change - Migração de API

## Resumo

Migração da API do Instagram do modelo legado (Instagram Messaging API via Facebook Graph API) para a nova **Instagram API with Instagram Login**.

Esta mudança elimina a dependência obrigatória de uma Página do Facebook vinculada à conta do Instagram Business.

## Mudanças Implementadas

### 1. Base URL

| Antes | Depois |
|-------|--------|
| `https://graph.facebook.com/v19.0` | `https://graph.instagram.com` |

### 2. Endpoint de Envio de Mensagens (DM)

| Antes | Depois |
|-------|--------|
| `POST /{facebook_page_id}/messages` | `POST /me/messages` ou `POST /{ig_id}/messages` |

### 3. Token de Acesso

| Antes | Depois |
|-------|--------|
| `META_ACCESS_TOKEN_FACEBOOK` (Page Access Token) | `META_ACCESS_TOKEN_INSTAGRAM` (Instagram User Access Token) |

### 4. Page ID

| Antes | Depois |
|-------|--------|
| `META_PAGE_ID_FACEBOOK` (Facebook Page ID) | Não utilizado para Instagram (apenas `META_PAGE_ID_INSTAGRAM` para referência) |

## Arquivos Modificados

1. `app/integrations/meta/client.py`
   - Atualizada a lógica de inicialização do client para usar `graph.instagram.com` para Instagram
   - Atualizado o endpoint de envio de mensagens
   - Mantida compatibilidade com Facebook (usa `graph.facebook.com`)

## Variáveis de Ambiente Requeridas

As seguintes variáveis são obrigatórias para Instagram:

```bash
# Instagram (NOVA API)
META_ACCESS_TOKEN_INSTAGRAM=seu_instagram_user_access_token_aqui
META_PAGE_ID_INSTAGRAM=seu_instagram_business_account_id_aqui
META_APP_SECRET_INSTAGRAM=seu_app_secret_aqui
META_WEBHOOK_VERIFY_TOKEN_INSTAGRAM=seu_verify_token_aqui
```

## Variáveis de Ambiente para Facebook (Legado)

Para Facebook, continua usando as variáveis existentes:

```bash
# Facebook (API legada via graph.facebook.com)
META_ACCESS_TOKEN_FACEBOOK=seu_page_access_token_aqui
META_PAGE_ID_FACEBOOK=seu_facebook_page_id_aqui
META_APP_SECRET_FACEBOOK=seu_app_secret_aqui
META_WEBHOOK_VERIFY_TOKEN_FACEBOOK=seu_verify_token_aqui
```

## Permissões Necessárias (Nova API)

Para a nova API do Instagram, seu token precisa das seguintes permissões:

- `instagram_business_basic`
- `instagram_business_manage_messages`

## Como Gerar o Instagram User Access Token

1. Acesse o [Facebook Developers](https://developers.facebook.com/)
2. Vá em "Ferramentas" → "Graph API Explorer"
3. Selecione seu app
4. Clique em "Generate Access Token"
5. Selecione as permissões: `instagram_business_basic`, `instagram_business_manage_messages`
6. O token gerado é o `META_ACCESS_TOKEN_INSTAGRAM`

**Nota**: O token expira em 60 dias. Para uso em produção, implemente refresh automático ou use token de longa duração.

## Testes

Após a migração, teste:

1. **Receber mensagem DM**: Enviar mensagem para o Instagram Business
2. **Responder mensagem**: Verificar se a resposta é entregue
3. **Resposta a comentário**: Testar private reply em comentários

## Rollback

Em caso de problemas, o código mantém a estrutura para fácil rollback:

1. Altere `app/integrations/meta/client.py` para usar `graph.facebook.com` novamente
2. Use `META_ACCESS_TOKEN_FACEBOOK` em vez de `META_ACCESS_TOKEN_INSTAGRAM`
3. Reverta para endpoint `/{page_id}/messages`

## Referências

- [Instagram API with Instagram Login - Messaging API](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/messaging-api/)
- [Instagram API with Instagram Login - Migration Guide](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/migration-guide)
- [Send Messages - Instagram Platform](https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/messaging-api/send-messages)

## Notas

- A nova API **não requer** Facebook Page vinculada
- O formato dos webhooks permanece o mesmo
- O IGSID (Instagram Scoped ID) continua sendo usado como `recipient.id`
- A resposta a comentários (private reply) funciona da mesma forma
