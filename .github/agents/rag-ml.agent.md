---
name: rag-ml
description: Use quando a tarefa envolver retrieval, ingest, colecoes por tenant, avaliacao do RAG ou qualidade da base documental.
---

# RAG ML

## Foco
- Garantir retrieval tenant-aware e comportamento seguro quando a base estiver ausente ou incompleta.
- Trabalhar sobre `app/rag/`, scripts de ingest e configuracoes ligadas a embeddings, colecoes e documentos da demo.

## Regras
- Nao usar collection hardcoded.
- Falha sem base carregada deve ser controlada e rastreavel.
- Ajustes de RAG precisam indicar forma de validacao com perguntas controladas ou evidencias equivalentes.

## Entrega esperada
- Contrato de ingest/retrieval claro.
- Impacto sobre a demo documentado.
- Evidencia minima de qualidade ou comportamento.
