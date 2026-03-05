# Uso — Auth

1. Sempre crie `Credentials` no n8n para qualquer chave/ticket/token.
2. Para OAuth2: documente `redirect_uri` e scopes; teste em staging.
3. Para JWT: valide `exp`, `aud` e `iss`; prefira JWKS para rotacionamento.
4. Para Authy: teste chamadas `start` e `check` manualmente antes de integrar em produção.
