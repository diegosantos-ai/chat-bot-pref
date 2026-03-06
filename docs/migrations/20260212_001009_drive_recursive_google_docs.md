# 20260212_001009_drive_recursive_google_docs

## Resumo
Aprimoramento do auto-update do Google Drive para:
- varrer subpastas recursivamente;
- suportar ingestao de arquivos Google Docs via export para texto.

## Arquivos alterados
- `app/services/drive_watcher.py`
- `scripts/verify_features.py`
- `scripts/e2e_sequence.py`
- `AGENTS.md`

## O que mudou
1. DriveWatcher (recursivo)
- Adicionado percurso recursivo de pasta raiz + subpastas via API (`files.list` com `supportsAllDrives` e `includeItemsFromAllDrives`).
- Adicionado campo de resumo `folders_scanned` na saida de `check_for_updates()`.

2. DriveWatcher (Google Docs)
- Adicionado suporte a `application/vnd.google-apps.document`.
- Google Docs agora sao exportados via `files.export_media(..., mimeType='text/plain')` antes da ingestao.

3. DriveWatcher (robustez)
- Sanitizacao de nome de arquivo para filesystem local.
- Centralizacao de regras de mime suportado (download/export).
- `files_processed` passa a registrar caminho relativo no Drive (ex.: `Pasta/Subpasta/arquivo`).

4. Scripts de validacao
- `scripts/verify_features.py`: listagem do Drive com suporte a Shared Drives.
- `scripts/e2e_sequence.py`: exibe `pastas_varridas` no teste de auto-update.

## Impacto em producao
- Sem mudanca de schema de banco.
- Sem novas variaveis de ambiente.
- Sem mudanca de dependencias.
- Pode aumentar tempo da sincronizacao conforme profundidade/volume de subpastas.

## Passos para aplicar no servidor
1. Publicar codigo atualizado.
2. Reiniciar servico da API.
3. Rodar validacoes:
   - `python scripts/verify_features.py`
   - `python scripts/e2e_sequence.py`

## Observacoes operacionais
- Apenas Google Docs (`.gdoc`) foi adicionado em exportacao nesta entrega.
- Google Sheets/Slides continuam fora do escopo atual.
- A sincronizacao continua limitada aos formatos ingeriveis (PDF, DOCX, TXT, MD, Google Docs exportado).
