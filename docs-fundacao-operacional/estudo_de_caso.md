# Estudo de Caso: Chat Pref

## Resumo Executivo
O **Chat Pref** é a consolidação arquitetural de uma plataforma de atendimento baseada em IA e Recuperação Semântica (RAG). Seu objetivo nunca foi implementar soluções apenas pelo hype tecnológico, mas demonstrar a maturação de um pipeline robusto capaz de operar em ambientes sensíveis (como prefeituras e órgãos públicos) onde o controle e o isolamento de informações são de extrema importância.

## O Problema
Sistemas LLM ingênuos misturam fluxos que abrem portas para:
- Vazamento de contexto (um cliente acessando PDFs de outro).
- Respostas não controláveis gerando danos institucionais ("Brand Safety").
- Altíssima latência na ponta por abstrações inúteis de bibliotecas encadeadas.

## A Solução e Estrutura
Foi modelada a base de **Fundação Operacional**, caracterizada por:
- Backend escalável suportado via FastAPI e Python moderno.
- Isolamento contextual com `tenant_aware` explícito (da rota web até a coleção vetorial no Chroma).
- Pipeline de guardrails acionado antes (policy_pre) e depois (policy_post) da chamada generativa principal.
- CI/CD que intercepta alterações de lógica que firam compatibilidade comportamental com baseline esperado.

## Artefatos para Exploração
1. **[Arquitetura Ativa](arquitetura.md):** Mapa de componentes atuais que sustentam o projeto validado.
2. **[Decisões de Engenharia (Trade-offs)](tradeoffs_decisoes.md):** Um olhar profundo nos motivos de adoção/restrição de padronizações.
3. **[Roteiro de Demonstração](roteiro_demonstracao.md):** Um passo-a-passo testável na máquina do revisor/auditor da base.
4. **[Capacidades vs Padrões de Indústria](matriz_capacidades.md):** Como a aplicação responde verticalmente às demandas comuns do ecossistema e indústria padrão.

## Limitações Atuais e Próximos Passos (Evolução Contínua)
A arquitetura encoraja transparência sobre seus próprios limites.

*Limitações de Runtime*
- O banco local atual (ChromaDB embarcado em disco) atende a volumetrias modestas, visando simplicidade num ambiente de prova. Em uma transição corporativa pesada requer migração para cluster (ex. Qdrant / Milvus) com ingestão dissociada.
- Orquestração nativa transacional roda apenas um nó principal na AWS (single-EC2 deploy via Terraform), não estando suportada momentaneamente carga via replicas múltiplas de Kubernetes por fugir do escopo inicial de validação dos *Guardrails*.

*Extensões Futuras Previstas*
- Migração dos pipelines do `MLflow` (rastreados offline em ramificação paralela/LLMOps) para uma tomada de decisão adaptativa dentro do síncrono.
- Criação de interface rica (Admin Panel). Este escopo está mantido suspenso e "fora de escopo" das entregas fundamentais visto que o valor-chave arquitetural residia nos pipelines analíticos de backend.
