# Log de Testes E2E - Fallback & Drive
**Data:** 11/02/2026
**Status:** ✅ VALIDADO (Com observações)

## 1. Ferramenta de Teste
Criamos o script interativo `scripts/e2e_sequence.py` para validar o fluxo completo do usuário.

**Como rodar:**
```bash
python scripts/e2e_sequence.py
```

## 2. Cenários de Teste

### A. Web Scraper & Escalation (Fluxo Real)
**Teste Realizado:** Pergunta sobre "curso de MODELAGEM E HENNA".
**Resultado:** `Decision.ESCALATE` -> **Sucesso!**
**Evidência:** Usuário confirmou recebimento do email.
**Análise:** O termo não estava na base nem no site, então o sistema escalou corretamente para o humano.

### B. Tratamento de Ruído (Input Inválido)
**Teste Realizado:** Input aleatório "eragsadfgasdgfsad".
**Resultado:** `Decision.FALLBACK`.
**Análise:** O sistema identificou corretamente como conteúdo fora de escopo/inválido e **não enviou email** (correto para evitar spam).

### C. Google Drive Auto-Update
**Teste Realizado:** Sincronização de pasta.
**Resultado:** Lógica de ingestão acionada.
**Alerta:** Erro de conexão com Banco de Dados detectado (`WinError 1225`).
**Alerta:** Erro de conexão com Banco de Dados detectado (`WinError 1225`).
**RESOLUÇÃO:** IP do banco atualizado para `192.168.3.23`. Conexão restabelecida e validada com sucesso via script `test_db.py`.

## 3. Conclusão
O pipeline de resiliência está funcional. O orquestrador segue corretamente a lógica:
`RAG -> Web Scraper -> Escalation (Email)`

A integração com o Drive está ativa e monitorando a pasta configurada.

---

## 4. Reteste técnico (11/02/2026 - noite)
Após correção do script `scripts/e2e_sequence.py` e do scraper:

- **Teste 1 (Scraper):** `Decision.ANSWER_RAG` com evento `source=web_scraper` confirmado.
- **Teste 2 (Escalation):** `ResponseType.ESCALATED` com template `escalation_email_sent` (email automático).
- **Teste 3 (Drive):** conexão OK, mas retorno `files_seen=0` e `files_updated=0`.

### Observação operacional
A sincronização do Drive está funcional, porém sem arquivos visíveis para ingestão na pasta configurada (`GOOGLE_DRIVE_FOLDER_ID`). Para confirmar atualização automática, incluir ao menos 1 arquivo suportado (PDF, DOCX, TXT, MD) na pasta compartilhada com a Service Account e repetir o teste.

---

## 5. Reteste técnico (12/02/2026 - madrugada)
Após compartilhamento correto da pasta com a Service Account e implementação de varredura recursiva + export de Google Docs:

- **Teste 1 (Scraper):** `Decision.ANSWER_RAG` com `source=web_scraper`.
- **Teste 2 (Escalation):** `ResponseType.ESCALATED` com template `escalation_email_sent`.
- **Teste 3 (Drive):** `STATUS=ok`, `vistos=8`, `atualizados=6`, `pastas_varridas=8`.

### Evidência de ingestão
Arquivos ingeridos incluem conteúdos em subpastas e Google Docs exportados automaticamente para texto, por exemplo:
- `Educação/INAUGURAÇÃO DA ESCOLA VILSON REDIVO`
- `Infraestrutura/A obra de reconstrução da ponte que liga as comunidades do Guavirá e Pinhalzinho`
- `Treinamento - Resposta para perguntas nao respondidas/REFIS 2025`
