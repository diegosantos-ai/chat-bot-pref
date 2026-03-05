
import os
import psycopg2
from pathlib import Path
from dotenv import load_dotenv


# Carrega variáveis do .env, se existir
load_dotenv(Path(__file__).resolve().parent.parent / '.env')

# Caminho para o arquivo de views
VIEWS_SQL = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'analytics', 'v1', 'views.sql')


# Configurações do banco vindas do ambiente
DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'pilot_atendimento'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
}

def executar_views():
    with open(VIEWS_SQL, 'r', encoding='utf-8') as f:
        sql = f.read()
    # Divide comandos por ponto e vírgula, ignora linhas vazias
    comandos = [cmd.strip() for cmd in sql.split(';') if cmd.strip()]
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn:
            with conn.cursor() as cur:
                for cmd in comandos:
                    cur.execute(cmd)
        print('Views criadas com sucesso!')
    finally:
        conn.close()

if __name__ == '__main__':
    executar_views()
