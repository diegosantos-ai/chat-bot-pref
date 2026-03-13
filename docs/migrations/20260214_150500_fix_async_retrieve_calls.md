# 20260214_150500_fix_async_retrieve_calls

## Data: 2026-02-14 15:05:00

## Descrição
Correção de bug crítico onde chamadas ao método `RAGRetriever.retrieve()` não estavam sendo aguardadas com `await`, causando erro `AttributeError: 'coroutine' object has no attribute 'chunks'`.

## Problema
O método `retrieve()` na classe `RAGRetriever` foi alterado para ser assíncrono (`async def`) em uma atualização anterior, mas as chamadas no código não foram atualizadas para usar `await`. Isso resultava em:
- Erro: `AttributeError: 'coroutine' object has no attribute 'chunks'`
- Warning: `RuntimeWarning: coroutine 'RAGRetriever.retrieve' was never awaited`

## Arquivos Modificados

### 1. app/orchestrator/service.py
- **Linha 301**: Adicionado `await` na chamada `self.retriever.retrieve(query)`
- **Mudança**: `retrieval = self.retriever.retrieve(query)` → `retrieval = await self.retriever.retrieve(query)`

### 2. app/rag/composer.py
- **Linha 162**: Adicionado `await` na chamada dentro do método `compose()`
- **Linha 251**: Adicionado `await` na chamada dentro do método `compose_with_history()`

### 3. app/rag/retriever.py
- **Linha 388-390**: Atualizado função global `retrieve()` para ser `async def`
- **Linha 406**: Adicionado `asyncio.run()` no bloco `__main__` para executar a função async

## Impacto
- **Correção imediata**: Webhook do Instagram/Messenger volta a funcionar corretamente
- **Sem breaking changes**: A API permanece a mesma, apenas aguarda corretamente as coroutines
- **Testado**: Syntax check validado com sucesso

## Aplicação no Servidor
1. Fazer pull do código atualizado
2. Reiniciar o serviço `terezia-api`:
   ```bash
   sudo systemctl restart terezia-api
   ```
3. Verificar logs:
   ```bash
   sudo journalctl -u terezia-api -f
   ```

## Rollback
Caso necessário, o rollback é simples: remover os `await` das três chamadas (mas isso reintroduziria o bug).
