# Exemplos — Templates

Contém exemplos JSON prontos para importação no n8n. Arquivos:

- `webhook_api_persist.json` — Webhook → API → Persist
- `oauth2_google_example.json` — Exemplo OAuth2 Google
- `authy_otp_example.json` — Envio e verificação de OTP via Authy
- `stripe_webhook_example.json` — Handler de webhook Stripe (modelo de verificação de assinatura)

Importação rápida:

1. No n8n: *Workflows* → *Import from File* → selecione o JSON.
2. Atualize as `Credentials` referenciadas.
3. Teste com `Execute Node` e em ambiente de staging.
