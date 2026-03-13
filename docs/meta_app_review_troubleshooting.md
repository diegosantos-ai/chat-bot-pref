# Guia: Resolvendo a Trava no App Review do Meta

## Problema
A permissão `pages_utility_messaging` não carrega o formulário para preenchimento, travando o processo de App Review.

## Solução Imediata

### Opção 1: Remover a Permissão (RECOMENDADO)

Para o **{bot_name}**, você **NÃO PRECISA** de `pages_utility_messaging`. Esta permissão é para enviar mensagens proativas (ex: "Sua consulta é amanhã"). Como o bot só responde quando o usuário envia mensagem primeiro, remova-a:

1. No topo da página de App Review, clique no link **"editá-lo"** (azul)
2. Localize `pages_utility_messaging` na lista
3. **Desmarque** a permissão
4. Clique em **"Salvar"**
5. A etapa travada desaparecerá

**Permissões necessárias para o {bot_name}:**
- ✅ `pages_messaging` (já tem)
- ✅ `pages_show_list` (já tem)
- ✅ `pages_manage_metadata` (já tem)
- ✅ `pages_read_engagement` (já tem)
- ✅ `business_management` (já tem)
- ❌ `pages_utility_messaging` (REMOVER - não necessária)

### Opção 2: Resolver Bug de Carregamento

Se você realmente precisa dessa permissão, tente:

1. **Limpar cache**: Ctrl+F5 ou Cmd+Shift+R
2. **Modo anônimo**: Abra em janela privada (Ctrl+Shift+N)
3. **Outro navegador**: Chrome → Firefox/Edge/Safari
4. **Trocar idioma**: Altere para **English (US)** no canto superior direito
5. **Desativar extensões**: Ad blockers podem bloquear o formulário
6. **Horário**: Tente em horários diferentes (manhã EUA tem menos tráfego)

## Justificativas Prontas (caso precise)

Se conseguir acessar o formulário de `pages_utility_messaging`, use estas respostas:

### 1. Como seu aplicativo usa esta permissão?
```
O {bot_name} é um chatbot de atendimento ao cidadão para a Prefeitura de {client_name}. 

Usamos pages_utility_messaging para enviar mensagens utilitárias proativas como:
- Confirmação de recebimento de documentos
- Lembretes de horários de atendimento solicitados pelo usuário
- Atualizações sobre processos administrativos

Todas as mensagens são relacionadas a interações iniciadas pelo usuário e contêm apenas informações utilitárias (não promocionais).
```

### 2. Screencast (vídeo demonstrativo)
Grave um vídeo de 2-3 minutos mostrando:
- [ ] Usuário envia mensagem na página do Facebook
- [ ] Bot responde automaticamente
- [ ] Bot envia mensagem utilitária (se aplicável)
- [ ] Fluxo completo de ponta a ponta

**Ferramentas para gravar:**
- Loom (gratuito): https://www.loom.com
- OBS Studio (gratuito)
- Screen Recorder do Windows

### 3. Ligações de teste de API
No Graph API Explorer, execute e capture prints:

```
# Teste 1: Verificar token
GET /me?fields=id,name

# Teste 2: Listar páginas
GET /me/accounts

# Teste 3: Enviar mensagem (use um PSID de teste)
POST /me/messages
{
  "recipient": {"id": "<PSID_DO_TESTE>"},
  "message": {"text": "Teste de mensagem"},
  "messaging_type": "RESPONSE"
}
```

## Checklist Final para Submissão

Antes de clicar em "Enviar para análise", verifique:

- [ ] App Secret configurado
- [ ] Política de Privacidade URL acessível
- [ ] Termos de Serviço URL acessível
- [ ] Ícone 1024x1024 carregado
- [ ] Categoria correta: "Bots do Messenger para empresas"
- [ ] Empresa verificada (Nexo Basis ✓)
- [ ] Permissões desnecessárias REMOVIDAS
- [ ] Todas as permissões necessárias com justificativas preenchidas
- [ ] Webhook configurado e funcionando (modo desenvolvedor)
- [ ] Página do Facebook conectada ao app

## Dados do Seu App

```
App ID: 795355290232003
Nome: terezIA
Namespace: terezia
Empresa: Nexo Basis (Verificada)
Email: fvlopestecnologia@gmail.com
```

## Configuração do Webhook (Após App Review)

Antes de aprovar o app, teste o webhook em modo desenvolvedor:

1. Configure o webhook no painel:
   - Callback URL: `https://<seu-servidor>/webhook/meta`
   - Verify Token: `terezia_dev_2026`
   - Eventos: messages, messaging_postbacks

2. Assine a página:
   ```bash
   curl -X POST "https://graph.facebook.com/v19.0/{PAGE_ID}/subscribed_apps" \
     -d "access_token={ACCESS_TOKEN}"
   ```

3. Teste enviando mensagem para a página

## Contato Meta (se nada funcionar)

Se o formulário continuar travado após todas as tentativas:

1. Acesse: https://developers.facebook.com/support
2. Crie um ticket com a categoria **"App Review"**
3. Descreva: "Formulário da permissão pages_utility_messaging não carrega, impossibilitando finalizar o App Review"
4. Inclua screenshots do erro

**Tempo de resposta:** Geralmente 3-5 dias úteis

---

## Resumo da Ação Imediata

**PASSO 1**: Clique em "editá-lo" no topo da página
**PASSO 2**: Desmarque `pages_utility_messaging`
**PASSO 3**: Salve e avance

Pronto! A etapa travada desaparecerá e você poderá finalizar o App Review.
