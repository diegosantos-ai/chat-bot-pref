## Checklist de Deploy – Fase 5 (TerezIA)

1. **Validação do Ambiente de Produção**
    - [x] Conferir infraestrutura (servidores, cloud, permissões de acesso) - Script criado: `scripts/ops/validate_infrastructure.py`
    - [x] Validar variáveis de ambiente, tokens e segredos (Meta, Gemini, banco de dados) - Documentação: `docs/infrastructure_validation.md`
    - [x] Garantir backup dos dados e configurações atuais (Scripts de backup Postgres e Chroma criados)

2. **Deploy dos Serviços**
    - [x] Containerização via Docker (Dockerfile, docker-compose.yml)
    - [x] Subir serviços auxiliares: ChromaDB, PostgreSQL, Grafana
    - [ ] Configurar domínios, endpoints e webhooks (Facebook/Instagram)

3. **Configuração de Observabilidade**
    - [x] Integrar ferramentas de monitoramento: Grafana + PostgreSQL Logs
    - [x] Configurar dashboards para acompanhamento de uso, erros e performance (dashboard_terezia.json)
    - [ ] Definir alertas para falhas críticas (ex: queda de serviço, falha de integração)

4. **Auditoria e Segurança**
    - [x] Validar logging de interações para rastreabilidade (Tabela `audit_events`)
    - [x] Testar funcionamento dos guardrails (policy guard) - Script de teste: `scripts/run_validation_test.py`
    - [x] Verificar anonimização e proteção de dados sensíveis (Prompts atualizados para redirecionamento inbox)

5. **Validação Pós-Deploy**
    - [x] Realizar smoke tests em produção (fluxos principais, redirecionamentos, respostas de crise) - Script automatizado disponível
        - [x] Validar respostas de emergência/crise
        - [x] Validar respostas de zeladoria/infraestrutura (Novos docs RAG)
    - [ ] Validar integração com canais (Facebook/Instagram)
    - [x] Testar respostas automáticas e fallback (Dataset de validação executado)

6. **Treinamento e Handoff**
    - [x] Documentar procedimentos de operação e contingência (`docs/observability.md`, `README.md`)
    - [ ] Treinar equipe de atendimento para uso do painel de observabilidade
    - [ ] Definir responsáveis por monitoramento e escalonamento

7. **Go-Live e Monitoramento Contínuo**
    - [ ] Liberar acesso ao público
    - [ ] Monitorar métricas e logs em tempo real
    - [ ] Ajustar fluxos conforme feedback e incidentes
# Plano de Implementação: Adequação ao "Estudo de Melhorias"

## Visão Geral (Panorama)
A análise comparativa entre o estado atual e o documento `docs/estudo.md` revela uma necessidade de evolução do agente de um "respondente genérico" para um **Assistente Especializado e Seguro**.
As principais mudanças são:
1.  **Refinamento de Persona**: Adoção explicita da identidade "IA em treinamento" e uso de **Linguagem Simples** (Plain Language), abandonando o tom excessivamente formal.
2.  **Protocolos de Segurança Rígidos**: Substituição de bloqueios genéricos por **scripts pré-definidos de acolhimento** para casos de Suicídio, Violência Doméstica e Abuso.
3.  **Matriz de Redirecionamento**: Implementação de uma tabela oficial de contatos para garantir que todo "Não sei" venha acompanhado de um "Quem sabe" (telefone/endereço correto).
4.  **Enriquecimento da Base RAG**: Atualização dos documentos com dados granulares (Tabelas de horários de ônibus, regras específicas de REFIS 2025, detalhes de PSFs).

---

## User Review Required
> [!IMPORTANT]
> **Protocolos de Crise**: A implementação de respostas automáticas para *suicídio* e *violência* envolve riscos. Os textos sugeridos em `estudo.md` serão implementados ipsis litteris.
> **Dados Datados**: O estudo menciona "REFIS 2025" e horários de ônibus da vigência 2024/2025. Confirmar se estes dados já são vigentes. Assumiremos que sim.

---

## Proposed Changes

### 1. Ingestão de Conteúdo (RAG Base)
Atualização completa dos arquivos Markdown na pasta `base/` com o conteúdo rico extraído de `docs/estudo.md`.

#### [base/BA-RAG-PILOTO-2026.01.v1/items](file:///c:/Users/santo/pilot-atendimento/base/BA-RAG-PILOTO-2026.01.v1/items)
*   #### [MODIFY] `0001_horarios.md`
    *   *Adicionar*: Tabela de horários de ônibus (Expresso Santa Tereza) e atualização de horários de secretarias.
*   #### [MODIFY] `0002_contatos.md`
    *   *Substituir*: Pela "Matriz de Redirecionamento" completa (Seção 7.2 do estudo).
*   #### [MODIFY] `0004_saude.md`
    *   *Refinar*: Adicionar tabela detalhada de PSFs (Endereços, Telefones, Especialidades) e distinção clara de *Urgent Care* (SAMU/PA).
*   #### [MODIFY] `0006_info_geral.md` -> `0006_tributacao.md`
    *   *Focar*: Detalhes do IPTU 2025, REFIS e Nota Fiscal.
*   #### [NEW] `0007_assistencia_social.md`
    *   *Conteúdo*: Detalhes do CRAS, Conselho Tutelar e Auxílios (Seção 6.4).

### 2. Engenharia de Prompts e Persona
Ajuste nos prompts do sistema para alinhar tom de voz e regras de negócio.

#### [prompts/v1](file:///c:/Users/santo/pilot-atendimento/prompts/v1)
*   #### [MODIFY] `system.txt`
    *   *Adicionar*: Instrução de "Linguagem Simples".
    *   *Adicionar*: Identidade "Sou uma IA em treinamento".
    *   *Adicionar*: Regra de "Redirecionamento Assistido" (Sempre fornecer contato quando falhar).
    *   *Adicionar*: **Disclaimer Obrigatório** sobre IA e limitações legais (Seção 6.1 do apoio_faq).
*   #### [MODIFY] `classifier.txt`
    *   *Refinar*: Melhorar distinção entre "Saúdo Administrativa" (Permitido) e "Saúde Clínica" (Bloqueado).

### 2.1 Refinamento dos Clusters RAG (baseado em `docs/apoio_faq.md`)
*   **Cluster A (Institucional)**: Garantir Telefone Geral, Endereço e CNPJ em `0002_contatos.md`.
*   **Cluster B (Educação)**: Adicionar datas de matrícula 2026 e docs necessários em `0008_educacao.md` (Novo).
*   **Cluster C (Saúde)**: Refinar horários de farmácia e distinção de Dengue em `0004_saude.md`.
*   **Cluster D (Tributos)**: Reforçar REFIS 2025 em `0006_tributacao.md`.
*   **Cluster E (Serviços)**: Detalhar Agência do Trabalhador em `0007_assistencia_social.md`.

### 3. Protocolos de Segurança (Policy Guard)
Implementação Hardcoded (Python) ou via Prompts Específicos para os temas sensíveis.

#### [prompts/v1](file:///c:/Users/santo/pilot-atendimento/prompts/v1)
*   #### [NEW] `crisis_suicide.txt`
    *   *Conteúdo*: Script do CVV/SAMU (Seção 5.1).
*   #### [NEW] `crisis_violence.txt`
    *   *Conteúdo*: Script de Violência 180/190 (Seção 5.2).

#### [app/policy_guard](file:///c:/Users/santo/pilot-atendimento/app/policy_guard)
*   #### [MODIFY] `service.py`
    *   *Lógica*: Detectar intents/keywords de crise e retornar os prompts estáticos acima *antes* de chamar o LLM.

## Verification Plan

### Automated Tests
*   **Testes de Crise**: Criar novos casos de teste que simulem inputs como "quero me matar" ou "meu marido me bateu" e verificar se a resposta corresponde EXATAMENTE ao script de segurança.
*   **Testes de RAG**: Verificar se perguntas específicas ("Qual horário do ônibus para Cascavel?", "Telefone do PSF Vila Operária") retornam os dados novos.

### Manual Verification
*   Revisar manualmente os arquivos .md gerados para garantir formatação correta.
