Sessão: Deploy e Configuração — pilot-atendimento

Resumo rápido
- Projeto: FastAPI "pilot-atendimento" implantado em uma instância Amazon Linux (EC2) sob o domínio `nexobasis.com.br`.
- Nginx atua como terminador TLS (Let's Encrypt) e reverse proxy; serve site estático em `/var/www/nexobasis` e proxy para a API local em `/tereziapi/` → `http://127.0.0.1:8000/`.
- Uvicorn roda sob `systemd` (unidade `pilot_atendimento.service`) e está ligado a `127.0.0.1:8000` (não em 0.0.0.0).

O que foi feito nesta sessão
- Criado / reescrito o site estático moderno em `/var/www/nexobasis` (landing multi‑seção: hero, serviços, cases, processo, equipe, contato).
- Animatei o cabeçalho com uma digitação caractere‑a‑caractere para a marca "NEXO BASIS" e um cursor sublinhado que pisca e mantém tamanho sincronizado via JavaScript (MutationObserver + hooks de resize/scroll).
- Substituí o formulário de contato por dois botões modernos: `mailto:` e `wa.me` (WhatsApp), com estilos modernos e ícones (Material Symbols). Planejada troca do ícone de chat pelo SVG oficial do WhatsApp.
- Seções de equipe e ativos: dois membros (Diego Santos, Fernando Lopes); avatars carregados externamente (GitHub, Gravatar). Pequenos SVGs/placeholder e `og-image.png` placeholder adicionados.
- Hardening do nginx: criado snippet `deny_sensitive.conf` (negar dotfiles) e `security_headers.conf` com CSP ajustado (libera Google Fonts e domínios de avatar externos). Arquivo de configuração do site: `/etc/nginx/conf.d/pilot_atendimento.conf`.
- Systemd: `pilot_atendimento.service` ajustado para executar uvicorn com `--host 127.0.0.1 --port 8000`; backup criado em `/etc/systemd/system/pilot_atendimento.service.bak`.
- TLS: certificados gerados via Let's Encrypt em `/etc/letsencrypt/live/nexobasis.com.br/`.
- Testes operacionais e reloads de nginx / systemd feitos durante a sessão.

Arquivos importantes modificados
- `/home/ec2-user/pilot-atendimento/.env` (variáveis de ambiente — contém segredos; não postar em chat)
- `/etc/systemd/system/pilot_atendimento.service` (unit systemd para uvicorn)
- `/etc/systemd/system/pilot_atendimento.service.bak` (backup)
- `/etc/nginx/conf.d/pilot_atendimento.conf` (server block nginx para `nexobasis.com.br`)
- `/etc/nginx/snippets/deny_sensitive.conf` (deny dotfiles)
- `/etc/nginx/snippets/security_headers.conf` (CSP + security headers)
- `/var/www/nexobasis/index.html` (landing page)
- `/var/www/nexobasis/styles.css` (CSS moderno, variáveis, animações)
- `/var/www/nexobasis/script.js` (typing animation, cursor sync, nav toggle)
- `/var/www/nexobasis/assets/` (SVGs, `og-image.png` placeholder)

Estado em tempo de execução & comportamentos esperados
- Nginx: TLS terminator e proxy reverso; site estático servido corretamente e rotas `/tereziapi/` proxied para uvicorn.
- Uvicorn: processado por `systemd` e escutando em 127.0.0.1:8000.
- CSP: configurado para permitir Google Fonts (`fonts.googleapis.com`, `fonts.gstatic.com`) e imagens de `avatars.githubusercontent.com` e `www.gravatar.com`.
- Interações de UI: header realiza animação de digitação na carga; cursor pisca e é mantido em tamanho correto via JS; ao rolar a página, a marca encolhe.
- Contato: botões `mailto:` e `wa.me` abrem cliente de e‑mail e WhatsApp, respectivamente.

Problemas conhecidos / quirks
- Cursor sublinhado: MutationObserver e handlers de resize/scroll foram adicionados para corrigir casos onde o cursor não redimensionava; ainda pode haver edge cases em dispositivos muito lentos.
- CSP: se novos recursos externos forem adicionados (CDN, analytics, novas imagens), será necessário atualizar `/etc/nginx/snippets/security_headers.conf`.
- Avatares e Google Fonts são carregados externamente; para reduzir solicitações externas ou apertar CSP, recomenda‑se hospedar localmente os fonts (woff2) e imagens em `/var/www/nexobasis/assets/`.

O que falta / próximos passos recomendados
1) Polir botões de contato (substituir ícone de chat por SVG WhatsApp oficial; adicionar micro‑interações: hover, ripple, foco acessível).
2) Criar endpoint backend `POST /lead` no FastAPI para receber leads e permitir tracking dos cliques do site (ex.: chamada `fetch('/tereziapi/lead', ...)`).
3) Implementar webhooks skeletons no FastAPI para Facebook/Instagram/WhatsApp (validar assinaturas HMAC/sha256, tokens de verificação).
4) Gerar e substituir `assets/og-image.png` por uma imagem otimizada (1200×630) para redes sociais.
5) Opcional: self‑host Google Fonts e avatars; atualizar CSP em `/etc/nginx/snippets/security_headers.conf` e recarregar nginx.
6) Garantir AWS Security Group fecha portas públicas desnecessárias (principalmente 8000).

Comandos úteis para teste
- Ver status do serviço systemd: `sudo systemctl status pilot_atendimento.service`
- Logs do serviço: `sudo journalctl -u pilot_atendimento.service -f`
- Testar nginx e reload: `sudo nginx -t && sudo systemctl reload nginx`
- Ver portas escutando: `ss -ltnp | egrep ':8000|:443|:80'`
- Requisição HTTPS: `curl -vkI https://nexobasis.com.br/`
- Testar renovação certbot: `sudo certbot renew --dry-run`

Backups e onde checar antes de editar
- Faça cópias antes de editar: `sudo cp /var/www/nexobasis/index.html{,.bak}` e `sudo cp /var/www/nexobasis/styles.css{,.bak}`.
- Backup do systemd já em: `/etc/systemd/system/pilot_atendimento.service.bak`.

Observação final
- Não poste conteúdos secretos (chaves em `.env`, arquivos de certificados privados) em qualquer chat. Qualquer alteração operacional (ex.: alteração de Security Group, reinício forçado, exposição de portas) peça confirmação explícita.

EOF && sudo tee /home/ec2-user/pilot-atendimento/agents.md > /dev/null <<'EOF'
Guia para agentes/IA — pilot-atendimento (nexobasis.com.br)

Propósito
- Orientar agentes de IA sobre a topologia do servidor, rotas públicas/privadas, serviços, arquivos relevantes e boas práticas ao automatizar tarefas ou sugerir mudanças.

Visão geral do ambiente
- Host: instância Amazon Linux (EC2).
- Domínio: `nexobasis.com.br` (DNS deve apontar para a instância).
- Web server: Nginx atua como TLS terminator e reverse proxy.
- App server: FastAPI executando via Uvicorn, gerenciado por `systemd` (unidade: `pilot_atendimento.service`) escutando em `127.0.0.1:8000`.
- Conteúdo estático: `/var/www/nexobasis` (index.html, styles.css, script.js, assets/).
- Certificados TLS: `/etc/letsencrypt/live/nexobasis.com.br/` (certbot usado).

Rotas relevantes
- Site público (estático):
  - https://nexobasis.com.br/ → servido por nginx a partir de `/var/www/nexobasis/index.html`.
- Proxy API:
  - https://nexobasis.com.br/tereziapi/ → proxied por nginx para `http://127.0.0.1:8000/` (FastAPI).
- Sugeridas/planejadas:
  - `POST /tereziapi/lead` — endpoint para registrar leads (recomenda-se autenticação via token).
  - `POST /tereziapi/webhook/facebook` — FB webhook (validar X-Hub-Signature / verify_token).
  - `POST /tereziapi/webhook/whatsapp` — WhatsApp Business webhook (validar assinatura e token).
  - Não exponha `:8000` diretamente ao público — somente via nginx.

Arquivos e caminhos importantes
- Código app / env:
  - `/home/ec2-user/pilot-atendimento/` — projeto FastAPI e `.env` (contém segredos: NÃO expor).
- Systemd:
  - `/etc/systemd/system/pilot_atendimento.service` — unit file (uvicorn ExecStart usa 127.0.0.1:8000).
  - `/etc/systemd/system/pilot_atendimento.service.bak` — backup.
- Nginx:
  - `/etc/nginx/conf.d/pilot_atendimento.conf` — server block para `nexobasis.com.br`.
  - `/etc/nginx/snippets/security_headers.conf` — CSP e security headers.
  - `/etc/nginx/snippets/deny_sensitive.conf` — deny dotfiles.
- Certs:
  - `/etc/letsencrypt/live/nexobasis.com.br/` — certs e chaves (manter privadas).
- Estático:
  - `/var/www/nexobasis/index.html`
  - `/var/www/nexobasis/styles.css`
  - `/var/www/nexobasis/script.js`
  - `/var/www/nexobasis/assets/`

Portas e firewall
- Nginx: portas 80/443 abertas ao público.
- Uvicorn: 127.0.0.1:8000 (escuta localmente apenas). AWS Security Group deve bloquear 8000 externamente; confirmar com `ss -ltnp` e no console AWS.

Segurança e práticas recomendadas
- Nunca colocar segredos em mensagens públicas. `.env` permanece no host e não deve ser comitado.
- Validar assinaturas webhooks (Facebook/WhatsApp) usando tokens/secretos armazenados em `.env`.
- Proteger endpoints que executem ações administrativas com token HMAC/Authorization header.
- Ao alterar CSP (`/etc/nginx/snippets/security_headers.conf`), recarregar nginx: `sudo nginx -t && sudo systemctl reload nginx`.
- Fazer backups antes de alterar arquivos críticos (systemd, nginx, index.html, styles.css).
- Usar `sudo journalctl -u pilot_atendimento.service -f` para depurar erros de app.

Operações comuns e comandos úteis
- Logs do app: `sudo journalctl -u pilot_atendimento.service -f`
- Testar nginx: `sudo nginx -t`
- Recarregar nginx: `sudo systemctl reload nginx`
- Status systemd: `sudo systemctl status pilot_atendimento.service`
- Ver portas: `ss -ltnp | egrep ':8000|:443|:80'`
- Testar HTTPS: `curl -vkI https://nexobasis.com.br/`
- Certbot dry-run: `sudo certbot renew --dry-run`

Notas sobre o frontend
- Arquivos principais: `/var/www/nexobasis/index.html`, `/var/www/nexobasis/styles.css`, `/var/www/nexobasis/script.js`.
- Funcionalidades implementadas: animação de digitação do cabeçalho, cursor sincronizado, botões `mailto:` e `wa.me`.
- Tracking: planejar `fetch('/tereziapi/lead')` ao clicar nos CTAs para registrar leads no backend.
- CSP permite Google Fonts e avatars externos; para reduzir requests e apertar CSP, self-host fonts e avatars em `/var/www/nexobasis/assets/`.

Tarefas automáticas/assistidas que agentes podem executar (com cautela)
1) Criar/atualizar `POST /tereziapi/lead` no FastAPI para receber JSON de leads e persistir (arquivo, DB ou forward por email). Exigir token simples no header para prevenir spam.
2) Criar skeletons de webhooks para FB/IG/WhatsApp com validação de assinatura e token de verificação.
3) Substituir o ícone de chat por SVG oficial WhatsApp em `/var/www/nexobasis/index.html` e ajustar CSS em `/var/www/nexobasis/styles.css`.
4) Opcional: baixar Google Fonts (woff2) e colocar em `/var/www/nexobasis/assets/fonts/`; ajustar CSS e CSP.
5) Fazer backup automático antes de aplicarem mudanças (copiar arquivos modificados para `.bak`).
6) Testar mudanças em staging ou local antes de aplicar em produção; se isso não for possível, agir com passos pequenos e reversíveis.
7) ***

Restrições e avisos para agentes
- Não modificar `.env` sem autorização e sem registrar onde as chaves são armazenadas.
- Não executar comandos destrutivos (reset, force‑push) sem aprovação humana explícita.
- Quando for necessário expor portas ou alterar regras de Security Group, solicitar autorização explícita com a descrição do risco.
- Evitar enviar conteúdo sensível (chaves, certificados, tokens) em logs ou mensagens.

Contato e contexto adicional
- Departamento / contato primário: Diego Santos (contatos no site).
- Objetivo das integrações: chatbots com IA para Facebook, Instagram e WhatsApp; NLP em PT‑BR; fallback para atendente humano; integração com CRM.

---

EOF && sudo chmod 644 /home/ec2-user/pilot-atendimento/{session.md,agents.md} && sudo ls -l /home/ec2-user/pilot-atendimento/{session.md,agents.md}
