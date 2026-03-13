# Plano de Refino RAG - Fase 2 (Baseado na Análise do Site Oficial)

**Objetivo:** Reduzir fallbacks de "Não encontrei resposta" incorporando os fluxos oficiais e protocolos de atendimento identificados na análise forense do site municipal.

## 1. Atualização de Conteúdo (Base de Conhecimento)

### 1.1 Zeladoria e Infraestrutura (`0010_zeladoria_infraestrutura.md`)
- [ ] **Tapa-Buracos:** Adicionar fluxo oficial (Protocolo Online/Tel 1000) e explicar centralização.
- [ ] **Iluminação (COSIP):** Incluir prazos (48-72h) e distinção entre lâmpada (Prefeitura) vs Rede/Poste (Copel).
- [ ] **Coleta de Lixo:** Adicionar frequências inferidas (Centro vs Bairros) e contato na falta de cronograma online.
- [ ] **Poda de Árvores:** Explicar regra de Risco Elétrico (Copel) vs Estética (Meio Ambiente) e proibição de poda particular.
- [ ] **Terrenos Baldios/Dengue:** Adicionar fluxo de denúncia na Vigilância Sanitária (Tel 1093).
- [ ] **Drenagem/Bueiros:** Orientar como Solicitação Preventiva (Obras).
- [ ] **Pavimentação:** Explicar processo de Abaixo-Assinado/Ofício (Investimento vs Manutenção).
- [ ] **Lombadas:** Explicar necessidade de estudo técnico (JARI) e proibição de obra própria.

### 1.2 Saúde (`0004_saude.md`)
- [ ] **Horários:** Reforçar que UBS não abre sábado (exceto campanhas).
- [ ] **Odontologia:** Explicar porta de entrada via UBS.
- [ ] **CAPS:** Explicar regulação via Secretaria/CISOP.
- [ ] **Castração:** Adicionar Programa de Castração Gratuita (Sec. Agricultura - Tel 1090).

### 1.3 Administração e Fiscal (`0006_tributacao.md`, `0002_contatos.md`)
- [ ] **IPTU/Lixo:** Explicar acesso via site e atualização cadastral.
- [ ] **Procon:** Adicionar canais estaduais/consumidor.gov.br e falta de posto fixo.
- [ ] **Queimadas:** Adicionar canais de denúncia (Bombeiros 193 vs Fiscalização).

### 1.4 Educação e Social (`0008_educacao.md`, `0007_assistencia_social.md`)
- [ ] **Material Escolar:** Orientar consulta na escola.
- [ ] **Lista CMEI:** Mencionar link de transparência.
- [ ] **Cursos:** Mencionar Sala do Empreendedor/CRAS.

### 1.5 Protocolos de Atendimento e Governança (Novo: `0011_protocolos_governanca.md`)
- [ ] **Gestão de Crise Hídrica:** Protocolo Sanepar.
- [ ] **Neutralidade/Política:** Resposta padrão sobre leis e isenção.
- [ ] **Privacidade:** Protocolo de não fornecer contatos pessoais de autoridades.
- [ ] **Empatia/Reclamações:** Script para lidar com frustração e redirecionar para Ouvidoria.

## 2. Ações Técnicas
- [ ] **Ingestão:** Reexecutar `python -m app.rag.ingest data/knowledge_base/BA-RAG-PILOTO-2026.01.v1`.
- [ ] **Validação:** Rodar `python scripts/run_validation_test.py` com foco nas perguntas de zeladoria e saúde que falhavam.

## 3. Matriz de Contatos Consolidada
Atualizar `0002_contatos.md` com a tabela forense extraída do relatório.
