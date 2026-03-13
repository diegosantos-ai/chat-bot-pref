```skill
---
name: Auth
description: Habilidade para projetar, configurar e depurar autenticação em n8n (OAuth2, API Key, JWT, Authy)
---

# Auth

## Objetivo

Fornecer diretrizes e templates para configurar autenticação segura no n8n, incluindo OAuth2, API Keys, JWT e integrações com provedores de 2FA como Authy.

## Princípios Centrais

- Princípio do menor privilégio: conceder apenas scopes necessários.
- Segurança das credenciais: armazenar em `Credentials` do n8n e não em nodes ou texto.
- Automatizar refresh de tokens e tratamento de erros comuns (401/403).

## OAuth2 — Guia prático (n8n Credentials)

1. Crie uma credencial do tipo OAuth2 em `Credentials` no n8n com client_id, client_secret e URLs (auth/token).
2. Configure callbacks/redirecionamento para o ambiente (n8n Cloud/self-hosted) e adicione scopes mínimos.
3. Use o node `HTTP Request` com Auth configurada apontando para a credencial criada.
4. Para refresh automático, habilite o mecanismo de refresh do próprio n8n (quando suportado) ou implemente um node que renove antes do expirar.

## API Key / JWT

- API Key: armazenar como `API Key` credential; não logar valores.
- JWT: validar expiração, aud/iss e usar jwks endpoint para rotacionamento.

## Authy (exemplo de integração OTP)

Use Authy para verificação por SMS/APP:
1. Criar credenciais Authy (API Key) em `Credentials`.
2. Fluxo de exemplo:
	- Enviar OTP: HTTP Request POST para `https://api.authy.com/protected/json/phones/verification/start` com `api_key`.
	- Verificar OTP: HTTP Request GET/POST para `https://api.authy.com/protected/json/phones/verification/check`.
3. Valide respostas e trate códigos de erro específicos (ex.: 401 chave inválida, 429 rate limit).

## Manejo de erros de auth comuns

- 401 Unauthorized: verificar credenciais, escopos e token expirado.
- 403 Forbidden: checar scopes e permissões do usuário/aplicação.
- 429 Rate Limit: aplicar retry/backoff, log e alertas.

## Boas práticas

- Rotação de chaves: documentar procedimento e automatizar quando possível.
- Logs: mascarar qualquer valor sensível (mostrar apenas metadata como tipo e expiration).
- Testes: criar workflows de integração que validem autenticação em ambiente de staging.

``` 
