# GTM Elevation Plan - Nexo Gov SaaS

## Goal
Elevar as duas aplicações (Api Core e Admin System) do nível MVP local para uma versão Demo Comercial "Uau", implementando recursos visuais e simulações de "Killer Features" que ancoram a venda para prefeituras.

## Tarefas de Elevação Comercial

- [x] **Task 1:** Refinar fluxo de "Emissão de 2ª via de IPTU" no Chatbot. → *Verify: Mandar mensagem pedindo IPTU, bot reconhece, explica as opções e envia link oficial do portal da prefeitura.*
- [x] **Task 2:** Adicionar painel de "Análise de Sentimento" no Admin System (mock). → *Verify: Acessar aba de Dashboard no Admin e ver gráficos com métricas de "Satisfação do Cidadão".*
- [x] **Task 3:** Implementar simulação (mock) do módulo de "Disparo de Alertas em Massa" (Defesa Civil/Vacinação). → *Verify: Acessar módulo no Admin, preencher formulário e visualizar preview da mensagem.*
- [x] **Task 4:** Expandir base do RAG (Demo Tenant) com FAQs hiper-realistas de uma prefeitura real. → *Verify: Perguntar ao bot sobre processos complexos de alvará e ver a resposta baseada nos documentos.*
- [x] **Task 5:** Otimizar UI do Admin System com tema "Brutalismo Industrial" aprimorado (cores de conversão, tipografia legível). → *Verify: Navegar no admin e verificar consistência visual e experiência premium.*
- [x] **Task 6:** Refinar fluxo "Abrir Chamado" no Bot. → *Verify: Bot coleta informações iniciais do problema (ex: foto de buraco) e instrui o cidadão a usar o App oficial ou telefone enviando os contatos.*
- [x] **Task 7:** Adicionar módulo de "Análise de Intenções de Ouvidoria" no Admin System para visualizar volume de requisições de zeladoria. → *Verify: Histórico de intenções geradas na Task 6 aparece nos gráficos do Admin.*

## Done When
- [ ] O fluxo do bot suportar triagem inteligente e redirecionamento oficial para emissão de documentos e ouvidoria.
- [ ] Admin System possuir dashboards executivos reais (sentimento, intenções, métricas RAG) lendo do banco de auditoria.
- [ ] UI do Admin System estiver padronizada e polida para apresentação aos gestores públicos.
- [ ] Configuração de ambiente local (docker-compose) unificada para testar API + Admin Backend + Admin Panel simultaneamente com 1 comando.
