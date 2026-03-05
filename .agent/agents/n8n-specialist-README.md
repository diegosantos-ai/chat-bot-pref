# n8n-specialist — README

Agente `n8n-specialist` — especialista em n8n (pt-BR).

Resumo:
- Skills: `connectors`, `auth`, `templates`, `debugging`.
- Local dos exemplos: `C:\Users\santo\.agent\skills\templates\examples`.

Quickstart:
1. Crie as `Credentials` recomendadas no n8n (`cred-api`, `cred-google-oauth`, `cred-authy`, `cred-stripe-webhook`).
2. Importe os JSONs em `skills/templates/examples` no n8n (Workflows → Import from File).
3. Atualize as credentials locais no workflow importado.
4. Teste em `staging` com `Execute Node` antes de ativar.

Como pedir ajuda (exemplos em pt-BR):
- "Ajude a depurar um HTTP Request que retorna 429"
- "Crie template para webhook Stripe com verificação de assinatura"
- "Como configurar OAuth2 Google para refresh token no n8n?"

Recomendações de segurança:
- Nunca embutir tokens em workflows; sempre use `Credentials`.
- Testar rotacionamento de chaves em staging.
- Habilitar observability (logs/alerts) para workflows críticos.
