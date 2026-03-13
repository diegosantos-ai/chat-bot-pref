"""
Script de Validação de Infraestrutura e Variáveis de Ambiente
==============================================================
Versão: 1.0
Escopo: Validar todos os componentes necessários para o funcionamento da aplicação

Este script verifica:
1. Variáveis de ambiente obrigatórias
2. Conectividade com PostgreSQL
3. ChromaDB (diretório de persistência)
4. Tokens da Meta Platform (Facebook/Instagram)
5. Gemini API Key
6. Dependências Python
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple
import importlib.util

# Ajuste de sys.path para permitir imports após migração de scripts
SCRIPT_DIR = Path(__file__).parent.resolve()
ROOT_DIR = SCRIPT_DIR.parent.parent  # chat-bot-pref/
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Evita falhas de encode em consoles Windows (cp1252) quando o script imprime Unicode.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # py3.7+
except Exception:
    pass


# Cores para output no terminal
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    END = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str):
    """Imprime cabeçalho formatado."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")


def print_success(text: str):
    """Imprime mensagem de sucesso."""
    print(f"{Colors.GREEN}[OK] {text}{Colors.END}")


def print_error(text: str):
    """Imprime mensagem de erro."""
    print(f"{Colors.RED}[ERRO] {text}{Colors.END}")


def print_warning(text: str):
    """Imprime mensagem de aviso."""
    print(f"{Colors.YELLOW}[AVISO] {text}{Colors.END}")


def print_info(text: str):
    """Imprime mensagem informativa."""
    print(f"{Colors.BLUE}[INFO] {text}{Colors.END}")


def check_python_version() -> bool:
    """Verifica se a versão do Python é compatível (3.11+)."""
    print_header("1. Verificando Versão do Python")
    version = sys.version_info

    if version.major == 3 and version.minor >= 11:
        print_success(
            f"Python {version.major}.{version.minor}.{version.micro} - Compatível"
        )
        return True
    else:
        print_error(
            f"Python {version.major}.{version.minor}.{version.micro} - Requer Python 3.11+"
        )
        return False


def check_dependencies() -> bool:
    """Verifica se as dependências críticas estão instaladas."""
    print_header("2. Verificando Dependências Python")

    critical_deps = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "pydantic_settings",
        "python-multipart",
        "asyncpg",
        "chromadb",
        "google-genai",
        "httpx",
        "python_dotenv",
    ]

    module_name_map = {
        "python_dotenv": "dotenv",
        "google-genai": "google.genai",
        "python-multipart": "multipart",
    }

    missing = []
    for dep in critical_deps:
        module_name = module_name_map.get(dep, dep)

        spec = importlib.util.find_spec(module_name)
        if spec is None:
            missing.append(dep)
            print_error(f"{dep} - Não instalado")
        else:
            print_success(f"{dep} - Instalado")

    if missing:
        print_error(f"\nDependências faltando: {', '.join(missing)}")
        print_info("Execute: pip install -r requirements.txt")
        return False

    return True


def check_env_file() -> bool:
    """Verifica se o arquivo .env existe."""
    print_header("3. Verificando Arquivo .env")

    env_path = Path(".env")
    if env_path.exists():
        print_success(f"Arquivo .env encontrado: {env_path.absolute()}")
        return True
    else:
        print_error("Arquivo .env não encontrado")
        print_info("Crie um arquivo .env baseado no exemplo do README.md")
        return False


def check_environment_variables() -> Tuple[bool, List[str]]:
    """Verifica se todas as variáveis de ambiente obrigatórias estão definidas."""
    print_header("4. Verificando Variáveis de Ambiente")

    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        print_warning("python-dotenv não instalado, tentando carregar do sistema")

    required_vars = {
        "GEMINI_API_KEY": "Chave API da Google Gemini",
        "DATABASE_URL": "URL de conexão do PostgreSQL",
        "META_ACCESS_TOKEN_FACEBOOK": "Token de acesso do Facebook",
        "META_ACCESS_TOKEN_INSTAGRAM": "Token de acesso do Instagram",
        "META_PAGE_ID_FACEBOOK": "ID da Página Facebook",
        "META_PAGE_ID_INSTAGRAM": "ID da Conta Business do Instagram",
        "META_APP_SECRET_FACEBOOK": "App Secret do Facebook",
        "META_WEBHOOK_VERIFY_TOKEN": "Token de verificação do Webhook",
    }

    # Variáveis opcionais novas (Instagram App Secret pode ser vazio se igual ao Facebook)

    optional_vars = {
        "CHROMA_PERSIST_DIR": "Diretório de persistência do ChromaDB",
        "RAG_BASE_ID": "ID da base RAG",
        "GEMINI_MODEL": "Modelo Gemini a ser usado",
        "META_APP_SECRET_INSTAGRAM": "App Secret do Instagram (opcional se igual ao Facebook)",
        "META_PAGE_ID": "ID da Página (legacy - será removido)",
        "META_APP_SECRET": "App Secret (legacy - será removido)",
        "META_ACCESS_TOKEN": "Token de acesso (legacy - será removido)",
    }

    missing = []
    empty = []

    # Verificar variáveis obrigatórias
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value is None:
            missing.append(var)
            print_error(f"{var} - Não definida ({description})")
        elif value.strip() == "":
            empty.append(var)
            print_warning(f"{var} - Definida mas vazia ({description})")
        else:
            # Não mostrar o valor completo por segurança
            masked_value = value[:4] + "..." + value[-4:] if len(value) > 8 else "***"
            print_success(f"{var} - Definida ({masked_value})")

    # Verificar variáveis opcionais
    print_info("\nVariáveis Opcionais:")
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print_success(f"{var} - Definida: {value}")
        else:
            print_info(f"{var} - Usando padrão ({description})")

    if missing:
        print_error(f"\nVariáveis obrigatórias faltando: {', '.join(missing)}")
        return False, missing

    if empty:
        print_warning(f"\nVariáveis definidas mas vazias: {', '.join(empty)}")
        return False, empty

    return True, []


def check_database_connection() -> bool:
    """Verifica conectividade com o PostgreSQL."""
    print_header("5. Verificando Conexão com PostgreSQL")

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print_error("DATABASE_URL não definida, pulando teste de conexão")
        return False

    try:
        import asyncio
        import asyncpg

        print_info("Tentando conectar ao banco de dados...")

        async def _check_db(url: str):
            connection = await asyncpg.connect(url)
            try:
                version = await connection.fetchval("SELECT version();")
                pgcrypto = await connection.fetchval(
                    "SELECT exists(select 1 from pg_extension where extname='pgcrypto');"
                )
                tables_result = await connection.fetch("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('audit_events', 'rag_queries', 'conversas', 'usuarios_anonimos')
                """)
                tables = [row[0] for row in tables_result]
                return version, tables, pgcrypto
            finally:
                await connection.close()

        version, tables, pgcrypto = asyncio.run(_check_db(database_url))

        print_success("Conexão estabelecida com sucesso!")
        print_info(f"Versão do PostgreSQL: {version}")
        if pgcrypto:
            print_success("Extensão 'pgcrypto' instalada")
        else:
            print_warning(
                "Extensão 'pgcrypto' NÃO instalada - execute: CREATE EXTENSION pgcrypto;"
            )

        if "audit_events" in tables:
            print_success("Tabela 'audit_events' encontrada")
        else:
            print_warning("Tabela 'audit_events' não encontrada - execute setup_db.py")

        if "rag_queries" in tables:
            print_success("Tabela 'rag_queries' encontrada")
        else:
            print_warning("Tabela 'rag_queries' não encontrada - execute setup_db.py")

        if "usuarios_anonimos" in tables:
            print_success("Tabela 'usuarios_anonimos' encontrada")
        else:
            print_warning(
                "Tabela 'usuarios_anonimos' não encontrada - execute setup_db.py"
            )

        if "conversas" in tables:
            print_success("Tabela 'conversas' encontrada")
        else:
            print_warning("Tabela 'conversas' não encontrada - execute setup_db.py")

        return True

    except ImportError:
        print_error("asyncpg não instalado")
        return False
    except Exception as e:
        print_error(f"Erro ao conectar ao banco de dados: {str(e)}")
        print_info(
            "Verifique se o PostgreSQL está rodando e as credenciais estão corretas"
        )
        return False


def check_chromadb() -> bool:
    """Verifica o diretório de persistência do ChromaDB."""
    print_header("6. Verificando ChromaDB")

    chroma_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
    chroma_path = Path(chroma_dir)

    if chroma_path.exists():
        if chroma_path.is_dir():
            # Contar arquivos no diretório
            files = list(chroma_path.rglob("*"))
            file_count = len([f for f in files if f.is_file()])

            print_success(f"Diretório ChromaDB encontrado: {chroma_path.absolute()}")
            print_info(f"Arquivos no diretório: {file_count}")

            if file_count == 0:
                print_warning("Diretório vazio - execute a ingestão de documentos")
                return True
            else:
                print_success("Dados ChromaDB presentes")
                return True
        else:
            print_error(f"{chroma_path} existe mas não é um diretório")
            return False
    else:
        print_warning(f"Diretório ChromaDB não encontrado: {chroma_path.absolute()}")
        print_info("O diretório será criado automaticamente na primeira ingestão")
        return True


def check_gemini_api() -> bool:
    """Verifica se a chave Gemini é válida."""
    print_header("7. Verificando Google Gemini API")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print_error("GEMINI_API_KEY não definida")
        return False

    try:
        import httpx

        print_info("Testando autenticação com Google Gemini API...")

        # Testa gerando conteúdo simples
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": "Hello!"}]}]}

        with httpx.Client(timeout=10.0) as client:
            response = client.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            print_success("Chave Gemini válida!")
            configured_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
            print_success(f"Modelo configurado '{configured_model}' está disponível")
            return True
        elif response.status_code == 401:
            print_error("Chave Gemini inválida ou expirada")
            return False
        else:
            error_msg = (
                response.json().get("error", {}).get("message", "Erro desconhecido")
            )
            print_error(
                f"Erro ao validar chave Gemini: {response.status_code} - {error_msg}"
            )
            return False

    except ImportError:
        print_error("httpx não instalado")
        return False
    except Exception as e:
        print_error(f"Erro ao conectar com Google Gemini API: {str(e)}")
        return False


def _check_single_meta_token(
    platform: str, access_token: str, page_id: str, app_secret: str
) -> bool:
    """Verifica um token específico (Facebook ou Instagram)."""
    import httpx

    print_info(f"\nTestando autenticação {platform}...")

    url = "https://graph.facebook.com/v19.0/me"
    params = {"access_token": access_token, "fields": "id,name"}

    with httpx.Client(timeout=10.0) as client:
        response = client.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        api_id = data.get("id")
        name = data.get("name")

        print_success(f"Token {platform} válido! Conectado como: {name}")
        print_info(f"ID retornado por /me: {api_id}")

        # Detecta se o token parece ser de usuário (me/accounts funciona)
        accounts_url = "https://graph.facebook.com/v19.0/me/accounts"
        with httpx.Client(timeout=10.0) as client:
            acc_resp = client.get(accounts_url, params={"access_token": access_token})

        if acc_resp.status_code == 200:
            pages = acc_resp.json().get("data", [])
            if pages:
                print_warning(
                    f"Token {platform} parece ser um User Token (me/accounts disponível)."
                )
                page_ids = [str(p.get("id")) for p in pages if p.get("id")]

                if str(page_id) in page_ids:
                    print_success(
                        "PAGE_ID confere com uma página disponível em /me/accounts"
                    )
                else:
                    print_warning(
                        f"PAGE_ID no .env ({page_id}) NÃO aparece em /me/accounts"
                    )
                    if len(pages) == 1:
                        print_info(
                            f"Sugestão: use PAGE_ID={pages[0].get('id')} (pagina: {pages[0].get('name')})"
                        )

                print_info("Para envio de mensagens, use um Page Access Token.")
                return True

        # Se /me/accounts não estiver disponível, assumimos que já é Page Token.
        if api_id == page_id:
            print_success("PAGE_ID confere com o ID retornado pela API (Page Token)")
        else:
            print_warning(
                f"PAGE_ID no .env ({page_id}) difere do ID retornado ({api_id})"
            )

        return True
    elif response.status_code == 401 or response.status_code == 400:
        print_error(f"Token {platform} inválido ou expirado")
        print_info(f"Resposta: {response.text}")
        return False
    else:
        print_error(f"Erro ao validar token {platform}: {response.status_code}")
        return False


def check_meta_tokens() -> bool:
    """Verifica se os tokens da Meta Platform são válidos."""
    print_header("8. Verificando Meta Platform Tokens")

    # Facebook
    fb_token = os.getenv("META_ACCESS_TOKEN_FACEBOOK")
    fb_page_id = os.getenv("META_PAGE_ID_FACEBOOK")
    fb_secret = os.getenv("META_APP_SECRET_FACEBOOK")

    # Instagram
    ig_token = os.getenv("META_ACCESS_TOKEN_INSTAGRAM")
    ig_page_id = os.getenv("META_PAGE_ID_INSTAGRAM")
    ig_secret = os.getenv("META_APP_SECRET_INSTAGRAM")

    # Legacy (fallback)
    legacy_token = os.getenv("META_ACCESS_TOKEN")
    legacy_page_id = os.getenv("META_PAGE_ID")
    legacy_secret = os.getenv("META_APP_SECRET")

    results = []

    try:
        import httpx  # noqa: F401

        # Verificar Facebook
        if all([fb_token, fb_page_id, fb_secret]):
            results.append(
                _check_single_meta_token("Facebook", fb_token, fb_page_id, fb_secret)
            )
        elif legacy_token and legacy_page_id:
            print_warning(
                "Usando tokens legados para Facebook (META_ACCESS_TOKEN, META_PAGE_ID)"
            )
            results.append(
                _check_single_meta_token(
                    "Facebook", legacy_token, legacy_page_id, legacy_secret or ""
                )
            )
        else:
            print_error("Tokens Facebook incompletos")
            results.append(False)

        # Verificar Instagram
        if all([ig_token, ig_page_id]):
            # Instagram pode usar o mesmo secret do Facebook se não estiver configurado
            secret_to_use = ig_secret if ig_secret else fb_secret
            results.append(
                _check_single_meta_token(
                    "Instagram", ig_token, ig_page_id, secret_to_use or ""
                )
            )
        else:
            print_warning("Tokens Instagram não configurados (opcional)")

        return all(results) if results else False

    except ImportError:
        print_error("httpx não instalado")
        return False
    except Exception as e:
        print_error(f"Erro ao conectar com Meta API: {str(e)}")
        return False


def check_file_structure() -> bool:
    """Verifica estrutura de arquivos e diretórios importantes."""
    print_header("9. Verificando Estrutura de Arquivos")

    critical_paths = {
        "app/main.py": "Aplicação FastAPI principal",
        "app/settings.py": "Configurações da aplicação",
        "requirements.txt": "Dependências Python",
        "base": "Diretório de documentos RAG (deve ser diretório)",
        "prompts": "Diretório de prompts (deve ser diretório)",
    }

    all_ok = True
    for path, description in critical_paths.items():
        path_obj = Path(path)
        if path_obj.exists():
            if "diretório" in description.lower():
                if path_obj.is_dir():
                    print_success(f"{path} - {description}")
                else:
                    print_error(f"{path} existe mas não é um diretório")
                    all_ok = False
            else:
                print_success(f"{path} - {description}")
        else:
            print_error(f"{path} - Não encontrado ({description})")
            all_ok = False

    return all_ok


def generate_report(results: dict):
    """Gera relatório final da validação."""
    print_header("RELATÓRIO FINAL DE VALIDAÇÃO")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    print(f"\n{Colors.BOLD}Total de Verificações: {total}{Colors.END}")
    print(f"{Colors.GREEN}Passou: {passed}{Colors.END}")
    print(f"{Colors.RED}Falhou: {failed}{Colors.END}")
    print()

    if failed == 0:
        print_success("Todas as verificações passaram! A infraestrutura está pronta.")
        print_info(
            "Você pode iniciar a aplicação com: uvicorn app.main:app --host 0.0.0.0 --port 8000 (ou APP_PORT)"
        )
        return 0
    else:
        print_error(
            "Algumas verificações falharam. Corrija os problemas antes de continuar."
        )
        print_info("\nVerificações que falharam:")
        for check, passed in results.items():
            if not passed:
                print(f"  - {check}")
        return 1


def main():
    """Função principal."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("============================================================")
    print("VALIDAÇÃO DE INFRAESTRUTURA E VARIÁVEIS DE AMBIENTE")
    print("Pilot Atendimento - {bot_name}")
    print("============================================================")
    print(f"{Colors.END}\n")

    # Executar todas as verificações
    results = {
        "Python Version": check_python_version(),
        "Dependencies": check_dependencies(),
        ".env File": check_env_file(),
    }

    env_ok, missing_vars = check_environment_variables()
    results["Environment Variables"] = env_ok

    results["PostgreSQL Connection"] = check_database_connection()
    results["ChromaDB"] = check_chromadb()
    results["Google Gemini API"] = check_gemini_api()
    results["Meta Platform API"] = check_meta_tokens()
    results["File Structure"] = check_file_structure()

    # Gerar relatório final
    return generate_report(results)


if __name__ == "__main__":
    sys.exit(main())
