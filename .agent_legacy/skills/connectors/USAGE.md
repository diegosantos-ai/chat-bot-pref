# Uso — Connectors

1. Criar novas integrações seguindo o `Padrão de Conector` descrito em `SKILL.md`.
2. Nomear conectores como `service.resource.action`.
3. Armazenar credenciais no n8n (`Credentials`) e referenciá-las nas chamadas.
4. Testar com `Execute Node` e criar testes de integração em ambiente de staging.

Exemplo curto:

- Crie credencial `myApiCreds` em `Credentials`.
- No node `HTTP Request`, selecione `myApiCreds` como auth.
