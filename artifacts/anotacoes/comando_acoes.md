# COMANDOS PARA EXECUTAR O PROGRAMA (SQL, PYTHON)

## Estrutura:
Quando usar:
Como usar:
Codigo:
O que esperar:

---

### 1. Criar views de analytics no banco
**Quando usar:**
Após atualizar ou criar views SQL em analytics/v1/views.sql.

**Como usar:**
Executar o script Python responsável pela criação das views.

**Código:**
python scripts/executar_views.py

**O que esperar:**
Mensagem "Views criadas com sucesso!" indicando que as views SQL foram aplicadas no banco.

---

### 2. Rodar a API principal (FastAPI)
**Quando usar:**
Para iniciar o backend da TerezIA localmente.

**Como usar:**
Ative o ambiente virtual e execute o comando abaixo.

**Código:**
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

**O que esperar:**
API disponível em http://localhost:8000 e documentação interativa em /docs.

---

### 3. Executar testes automatizados
**Quando usar:**
Após alterações no código para garantir que tudo está funcionando.

**Como usar:**
No terminal, execute:

**Código:**
pytest tests/

**O que esperar:**
Relatório de testes, indicando sucesso ou falhas.

---

### 4. Rodar testes E2E
**Quando usar:**
Para validar o pipeline completo (classificador, policy guard, RAG e auditoria).

**Como usar:**
No terminal, execute:

**Código:**
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe -m pytest tests/e2e/test_pipeline_e2e.py

**O que esperar:**
Relatório de testes com 9 cenários. Para passar os casos que chamam o Gemini,
é necessário acesso à rede.

---

### 5. Ativar ambiente virtual Python
**Quando usar:**
Antes de rodar scripts, API ou instalar dependências.

**Como usar:**
No terminal, execute:

**Código:**
.venv\Scripts\Activate.ps1  # PowerShell
# ou
source .venv/bin/activate     # Linux/Mac

**O que esperar:**
Prompt do terminal indicando que o ambiente virtual está ativo.

---

### 6. Instalar dependências do projeto
**Quando usar:**
Após clonar o repositório ou atualizar requirements.txt.

**Como usar:**
No terminal, execute:

**Código:**
pip install -r requirements.txt

**O que esperar:**
Todas as dependências instaladas no ambiente virtual.
