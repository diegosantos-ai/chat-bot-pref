# Migration: Busca Híbrida, Boost de Siglas e Melhorias no Envio de Mensagens

**Data**: 2026-02-12
**Autor**: TerezIA Dev Team
**Tipo**: Feature Enhancement - Melhorias no RAG e Envio de Mensagens

## Resumo

Esta migração implementa melhorias significativas no sistema RAG (busca híbrida com boost de siglas) e no envio de mensagens para Instagram (suporte a mensagens longas e remoção de formatação Markdown).

## Mudanças Implementadas

### 1. Busca Híbrida no RAG (Retriever)

**Arquivo**: `app/rag/retriever.py`

**Funcionalidade**:
- Quando a busca semântica não retorna chunks com siglas presentes na query, o sistema faz uma busca adicional por chunks que contenham a sigla explicitamente
- Chunks encontrados por sigla recebem score base 0.7 + 0.2 boost = **0.9** (prioridade máxima)
- Garante que queries como "até quando posso pagar o REFIS 2025?" encontrem o chunk correto mesmo com baixa similaridade semântica

**Métodos Adicionados**:
- `_retrieve_by_acronyms()`: Busca chunks contendo siglas específicas

### 2. Sistema de Siglas (Acronyms)

**Arquivo**: `app/rag/acronyms.py` (novo)

**Funcionalidade**:
- Mapeamento de 51+ siglas municipais organizadas por categoria:
  - Tributos e Finanças (REFIS, IPTU, ISS, ICMS, MEI, etc.)
  - Saúde (SUS, PSF, UBS, PA, NASF, CAPS, SAMU)
  - Assistência Social (CRAS, BPC, LOAS, CadÚnico)
  - Empreendedorismo (ME, EPP, SEBRAE, JUCEPAR)
  - Educação (CMEI, CEI, NEE)
  - Trânsito (DETRAN, CIRETRAN, CONTRAN, JARI)
  - Infraestrutura (COSIP, COPEL)
  - Planejamento (PPA, LOA, LDO)
  - Emergência (PM, BM)

**Funções**:
- `extract_acronyms_from_query()`: Extrai siglas da query do usuário (case-insensitive)
- `get_acronym_boost()`: Calcula boost de +0.2 quando há match de sigla
- `get_acronym_meaning()`: Retorna significado da sigla
- `list_all_acronyms()`: Lista todas as siglas disponíveis

### 3. Remoção de Formatação Markdown

**Arquivos**:
- `app/integrations/meta/client.py` - Função `strip_markdown()`
- `prompts/v1/system.txt` - Instrução ao LLM
- `prompts/v1/rag_answer.txt` - Instrução ao LLM

**Funcionalidade**:
- Remove automaticamente formatação Markdown antes de enviar para Instagram
- Remove: **negrito**, *itálico*, `código`, listas numeradas, marcadores, blocos de citação
- Dupla proteção: LLM é instruído a não usar markdown + client sanitiza como fallback

### 4. Suporte a Mensagens Longas

**Arquivo**: `app/integrations/meta/client.py`

**Funcionalidade**:
- Detecta quando mensagem excede 1000 caracteres (limite Instagram)
- Divide automaticamente em múltiplas partes sem cortar palavras
- Prioriza divisão por:
  1. Parágrafos (quebras duplas)
  2. Sentenças (pontos finais)
  3. Palavras (último recurso)
- Envia partes sequencialmente

**Métodos Adicionados**:
- `split_message()`: Divide mensagem respeitando limites
- `_send_single_message()`: Envia mensagem individual
- `_send_single_private_reply()`: Envia resposta privada individual

### 5. Correção do Filtro min_score

**Arquivo**: `app/rag/retriever.py`

**Problema**: Filtro `min_score` era aplicado antes do boost de siglas, fazendo chunks relevantes serem descartados

**Solução**: Filtro agora é aplicado **após** o boost, permitindo que chunks com siglas passem no filtro mesmo com score semântico baixo

### 6. Testes de Siglas

**Arquivo**: `tests/test_acronyms.py` (novo)

**Cobertura**:
- Extração básica de siglas
- Case-insensitive (REFIS = refis = Refis)
- Múltiplas siglas na mesma query
- Não extrai match parcial ("ME" não casa com "como")
- Boost aplicado corretamente
- Cenário real do REFIS
- Integração simulada com retriever

## Arquivos Modificados/Criados

### Novos Arquivos
- `app/rag/acronyms.py` - Sistema de siglas (51+ siglas mapeadas)
- `tests/test_acronyms.py` - Testes do sistema de siglas

### Arquivos Modificados
- `app/rag/retriever.py` - Busca híbrida e correção do min_score
- `app/integrations/meta/client.py` - strip_markdown(), split_message()
- `prompts/v1/system.txt` - Instrução para não usar Markdown
- `prompts/v1/rag_answer.txt` - Instrução para não usar Markdown
- `AGENTS.md` - Documentação atualizada

## Testes Realizados

### Busca Híbrida
```bash
# Query: "até quando posso pagar o REFIS 2025?"
# Antes: REFIS não aparecia nos top 10
# Depois: REFIS em 1º lugar (score 0.90)
```

### Remoção de Markdown
```bash
# Antes: "Para **pagar** o `IPTU`..."
# Depois: "Para pagar o IPTU..."
```

### Mensagens Longas
```bash
# Mensagem de 1500 caracteres
# Divide em 2 partes: ~1000 + ~500 caracteres
# Sem cortar palavras no meio
```

## Rollback

Em caso de problemas:

1. **Busca Híbrida**: Remover chamada a `_retrieve_by_acronyms()` no `retrieve()`
2. **Siglas**: Remover import de `acronyms` no retriever
3. **Markdown**: As instruções nos prompts são inofensivas se mantidas
4. **Mensagens Longas**: Remover lógica de split em `send_message()`

## Referências

- Documentação Instagram API: https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/messaging-api/
- Testes: `python tests/test_acronyms.py`
- Query RAG: `python scripts/query_rag.py "sua pergunta"`

## Notas

- Não é necessário reingestão da base RAG (mudanças são apenas no código)
- Todos os testes passam (`14/14 testes de acronyms`)
- Sistema retrocompatível (funciona sem siglas também)
- Dupla proteção anti-Markdown (prompt + código)
