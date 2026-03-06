# Guia de Geração de Tokens Meta (Facebook/Instagram)

Para que a integração funcione, você precisa preencher o arquivo `.env` com credenciais reais da Meta.

## 1. App Secret (`META_APP_SECRET`)
1. Acesse [Meta for Developers](https://developers.facebook.com/apps/).
2. Selecione seu App.
3. Vá em **App Settings > Basic**.
4. Clique em "Show" no campo **App Secret**.
5. Copie e cole no `.env`.

## 2. Page Access Token (`META_ACCESS_TOKEN`)
Este token permite que a API envie mensagens como a Página.

### Método Rápido (Graph API Explorer)
1. Vá para o [Graph API Explorer](https://developers.facebook.com/tools/explorer/).
2. No campo "Meta App", selecione seu App.
3. Em "User or Page", selecione "User Token" primeiro.
4. Adicione as permissões:
    - `pages_manage_metadata`
    - `pages_messaging`
    - `instagram_basic`
    - `instagram_manage_messages`
5. Clique em "Generate Access Token".
6. Agora, mude "User or Page" para selecionar a **Sua Página**.
7. O token no campo "Access Token" mudará. Este é o **Page Access Token**.
8. Copie e cole no `.env`.

> **Nota**: Tokens gerados assim podem expirar. Para produção, recomenda-se criar um "System User" no Business Manager.

## 3. Page ID (`META_PAGE_ID`)
1. Vá para o [Graph API Explorer](https://developers.facebook.com/tools/explorer/).
2. Com o token da página selecionado, faça uma requisição `GET /me`.
3. O resultado JSON terá o campo `id`. Copie este valor.

## 4. Verify Token (`META_WEBHOOK_VERIFY_TOKEN`)
1. Escolha uma senha/string segura (ex: `terezia_webhook_2026`).
2. Coloque no `.env`.
3. Vá no Painel do App > **Webhooks**.
4. Selecione "Page" ou "Instagram" e clique em "Subscribe to this object".
5. No campo "Verify Token", coloque a **mesma string** que você definiu no `.env`.
6. No campo "Callback URL", coloque a URL pública da sua API (use `ngrok` para testar localmente: `https://seu-ngrok.io/webhook/meta`).

---
**Checklist do .env:**
```env
META_APP_SECRET=...        # Passo 1
META_ACCESS_TOKEN=...      # Passo 2
META_PAGE_ID=...           # Passo 3
META_WEBHOOK_VERIFY_TOKEN=... # Passo 4
```
