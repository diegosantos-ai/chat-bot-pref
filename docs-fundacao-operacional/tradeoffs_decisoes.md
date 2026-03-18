# Decisões de Engenharia e Trade-offs

Este artefato mapeia as principais decisões arquiteturais tomadas durante a construção deste projeto, priorizando transparência técnica sobre adoção cega de ferramentas do ecossistema de dados.

## 1. Isolamento Tenant-Aware vs. Complexidade de Injeção
**Decisão:** O `tenant_id` tornou-se uma fronteira nativa de request e um guardrail físico.
**Trade-off:** Exige configuração manual rigorosa no RAG e no ChromaDB (partição/subdiretório de metadata), mas garante que dados entre prefeituras nunca cruzem a camada estocástica do modelo de IA por falha de prompt.

## 2. Auditoria Operacional vs. LLM-as-a-Judge Online
**Decisão:** O fluxo online registra o comportamento sob um rastreador único de trace estruturado. A decisão de qualidade ou alucinação acontece nos logs, off-request, não adicionando chamadas avaliadoras (LLM-judge) na requisição HTTP original.
**Trade-off:** Nós abrimos mão de correções on-the-fly "inteligentes" em troca de manter a latência (TP99) o mais baixa possível para o usuário final, relegando heurísticas refinadas ao fallback controlável e à trilha transacional.

## 3. Composição Transparente vs. Frameworks Mágicos (LangChain/LlamaIndex)
**Decisão:** Optou-se por isolar a camada de composição, escrevendo diretamente prompts de injeção em python simples (FastAPI), conectando o `RagService` ao provedor sem wraps ocultos.
**Trade-off:** O projeto escreve boilerplate trivial (ex.: chamadas de embed) que outros hooks abstrairiam. Em contrapartida, ganha-se 100% de visibilidade de execução, menor peso no deploy dos containers locais e isolamento para trocar "mock" e "gemini" sem refatorar o engine complexo inteiro.

## 4. Benchmark Offline vs. Runtime Transacional
**Decisão:** Avaliação e Tracking Experimental não atuam dentro das regras de negócio ativas para consumo público.
**Trade-off:** Nós temos dois repositórios lógicos (docs da fundação vs docs de observabilidade), separados por domínios. A sincronização entre um sucesso experimental e a subida via proxy ao vivo necessita de passo manual do mantenedor. Em troca, blindamos pipelines contra interrupções desnecessárias geradas por libs de métricas pesadas rodando a cada API call.
