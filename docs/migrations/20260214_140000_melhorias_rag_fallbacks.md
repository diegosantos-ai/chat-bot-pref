# Migração: Melhorias no RAG para Redução de Fallbacks

**Data:** 2026-02-14
**Autor:** Agente TerezIA
**Versão:** v0.8.0

## Resumo

Esta migração implementa melhorias críticas no sistema RAG para reduzir a taxa de fallback de ~50% para ~20%, através de correções em thresholds, busca híbrida, expansão de siglas e melhorias na base de conhecimento.

## Problemas Identificados

1. **Taxa de fallback elevada:** 50.2% (608/1.210 requisições)
2. **Thresholds inconsistentes:** RAG_MIN_SCORE variava entre 0.30, 0.35 e 0.40
3. **Busca híbrida falha:** Não executava busca por siglas quando semântica retornava vazio
4. **Chunks pequenos:** Overlap de apenas 50 caracteres causava perda de contexto
5. **Siglas não expandidas:** "REFIS" e "Programa de Recuperação Fiscal" eram tratados como conceitos diferentes
6. **Prompt do classifier conservador:** Threshold de 0.7 rejeitava queries válidas

## Alterações Realizadas

### 1. Thresholds do RAG (`app/settings.py`)

```python
# Antes
RAG_TOP_K: int = 7
RAG_MIN_SCORE: float = 0.35

# Depois
RAG_TOP_K: int = 5  # Reduzido para diminuir redundância
RAG_MIN_SCORE: float = 0.30  # Aumenta recuperação de resultados relevantes
```

**Impacto:** Permite recuperar chunks com scores 0.30-0.35 que antes eram filtrados.

### 2. Chunking (`app/rag/ingest.py`)

```python
# Antes
CHUNK_OVERLAP = 50

# Depois
CHUNK_OVERLAP = 150  # Aumentado para melhorar contexto entre chunks
```

**Impacto:** Reduz perda de contexto entre chunks adjacentes.

### 3. Busca Híbrida (`app/rag/retriever.py`)

**Mudança:** Executar busca por siglas **mesmo quando a busca semântica retorna vazio**.

```python
# Lógica anterior (problemática)
if query_acronyms and chunks:  # Só buscava se já houvesse chunks
    ...

# Lógica nova (corrigida)
if query_acronyms:
    # Verifica se há match de boost (loop async compatível)
    has_boost_match = False
    for chunk in chunks:
        boost = await get_total_boost(query, chunk.text, chunk.tags)
        if boost > 0:
            has_boost_match = True
            break
    
    if not chunks or not has_boost_match:  # Busca se sem resultados ou sem boost
        # Executa busca por siglas
```

**Correção de Bug:** A primeira versão usava `any()` com async generator, causando `TypeError`. Corrigido para usar loop explícito.

**Impacto:** Queries como "REFIS 2025" ou "PSF central" agora encontram documentos mesmo quando o embedding semântico falha.

### 4. Expansão de Siglas (`app/rag/acronyms.py`)

**Adicionada função:** `expand_query_with_acronyms()`

```python
def expand_query_with_acronyms(query: str) -> str:
    """
    Expande siglas na query adicionando seus significados.
    
    Exemplo:
    Input: "quero aderir ao REFIS 2025"
    Output: "quero aderir ao REFIS 2025 Programa de Recuperação Fiscal"
    """
```

**Impacto:** Melhora busca semântica conectando siglas aos seus significados completos.

### 5. Sinônimos (`app/nlp/synonyms.py`)

**Adicionados sinônimos críticos:**

```python
# Documentos
"CNH": ["carteira de motorista", "habilitação", ...]
"comprovante de residência": ["conta de luz", "conta de água", ...]

# Serviços digitais (novo)
SERVICOS_DIGITAIS_SYNONYMS = {
    "site da prefeitura": ["portal", "website", ...],
    "agendamento": ["marcar hora", "agendar", ...],
}

# Emergência/Segurança (novo)
EMERGENCIA_SEGURANCA_SYNONYMS = {
    "defesa civil": ["emergencia", "desastre", ...],
    "guarda municipal": ["guarda", "segurança", ...],
}
```

**Impacto:** Melhora recuperação de queries com linguagem popular.

### 6. Prompt do Classifier (`prompts/v1/classifier.txt`)

**Alterações:**
- Threshold de confiança: 0.7 → **0.6**
- Removido exemplo problemático: `"Tá tudo sujo aqui"` como OUT_OF_SCOPE
- Adicionada instrução: Mensagens sobre infraestrutura ambíguas devem ser COMPLAINT

**Impacto:** Reduz classificações incorretas como OUT_OF_SCOPE.

### 7. Prompt de Resposta (`prompts/v1/rag_answer.txt`)

**Adições:**
- Instrução para expandir siglas na primeira menção
- Frase de fallback melhorada com direcionamento
- Instruções claras de formatação

```
# Fallback antigo
"Não encontrei essa informação na minha base de conhecimento."

# Fallback novo
"Não encontrei essa informação específica na minha base de conhecimento. 
Posso ajudar você com:
- Horários de atendimento: pergunte sobre horários
- Telefones úteis: pergunte sobre contatos  
- Documentos necessários: descreva o que você precisa
- Falar com atendente humano: digite 'atendente'"
```

### 8. Correção de Bugs (`app/orchestrator/service.py`)

**Problema:** Referências a `self.scraper` e `self.mailer` não inicializados.

**Correções:**
- Adicionada importação: `from app.services.mailer import mailer`
- Adicionada inicialização: `self.mailer = mailer`
- Removido código de web scraping (serviço não implementado)

## Ações Pós-Deploy

### 1. Reingestão da Base RAG

```bash
# Reingestão necessária devido ao aumento do CHUNK_OVERLAP
python -m app.rag.ingest data/knowledge_base/BA-RAG-PILOTO-2026.01.v1 --force
```

### 2. Verificação de Configurações

Certifique-se de que o `.env` contém:
```bash
RAG_MIN_SCORE=0.30
RAG_TOP_K=5
```

### 3. Testes de Validação

Execute testes para validar as melhorias:

```bash
# Testar queries com siglas
python -c "
import asyncio
from app.rag.retriever import retrieve

queries = [
    'quero aderir ao REFIS 2025',
    'onde fica o PSF central',
    'como emitir NFS-e',
    'quero agendar consulta médica'
]

for query in queries:
    result = asyncio.run(retrieve(query))
    print(f'{query}: {len(result.chunks)} chunks, best_score={result.best_score:.3f}')
"
```

### 4. Monitoramento

Após deploy, monitore as métricas:

```sql
-- Taxa de fallback por hora
SELECT 
    date_trunc('hour', created_at) as hour,
    response_type,
    COUNT(*) as count
FROM audit_events
WHERE event_type = 'RESPONSE_SELECTED'
GROUP BY hour, response_type
ORDER BY hour DESC;
```

## Resultados Esperados

| Métrica | Antes | Depois |
|---------|-------|--------|
| Taxa de Fallback | 50.2% | ~20% |
| Taxa de Sucesso | 45.4% | ~75% |
| Recuperação de siglas | Baixa | Alta |
| Cobertura de sinônimos | Limitada | Ampliada |

## Rollback

Em caso de problemas, reverter:

1. **Thresholds:**
   ```python
   # app/settings.py
   RAG_TOP_K: int = 7
   RAG_MIN_SCORE: float = 0.35
   ```

2. **Chunking:**
   ```python
   # app/rag/ingest.py
   CHUNK_OVERLAP = 50
   ```

3. **Prompts:** Restaurar versões anteriores em `prompts/v1/`

## Referências

- Issue: Taxa de fallback elevada
- Análise completa em: `/docs/migrations/20260214_rag_improvements_analysis.md`
