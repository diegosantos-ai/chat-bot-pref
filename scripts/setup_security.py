#!/usr/bin/env python3
"""
Setup Rápido de Segurança - TerezIA
=========================================

Instala dependências de segurança e valida configurações.

Uso:
    python scripts/setup_security.py
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd: str, description: str) -> bool:
    """Executa um comando e retorna True se sucesso."""
    print(f"\n{'='*60}")
    print(f"{description}")
    print(f"{'='*60}")
    print(f"Comando: {cmd}")
    print()
    
    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=False,
        text=True
    )
    
    if result.returncode == 0:
        print(f"✅ {description} - SUCESSO")
        return True
    else:
        print(f"❌ {description} - FALHOU")
        return False

def main():
    """Executa setup de segurança."""
    project_root = Path(__file__).parent
    
    print("🚀 SETUP DE SEGURANÇA - TEREZIA")
    print(f"Diretório do projeto: {project_root}")
    
    results = []
    
    # 1. Instalar dependências
    results.append(
        run_command(
            f"cd {project_root} && pip install slowapi tenacity boto3",
            "Instalando dependências de segurança"
        )
    )
    
    # 2. Validar .env existe
    env_file = project_root / ".env"
    if env_file.exists():
        print("\n✅ Arquivo .env encontrado")
        
        # 3. Validar configurações críticas
        print("\nValidando configurações críticas:")
        
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        checks = {
            "CORS_ORIGINS": "CORS configurado",
            "RATE_LIMIT_ENABLED": "Rate limiting habilitado",
            "DEBUG=false": "DEBUG desativado",
            "USE_SECRETS_MANAGER": "AWS Secrets Manager configurado"
        }
        
        for key, description in checks.items():
            if key in env_content:
                print(f"  ✅ {description}")
            else:
                print(f"  ⚠️  {description} - Não configurado")
                if key == "DEBUG=false":
                    print("     IMPORTANTE: Configure DEBUG=false em produção!")
                if key == "CORS_ORIGINS":
                    print("     IMPORTANTE: Configure CORS_ORIGINS com domínios permitidos!")
        
    else:
        print("\n⚠️  Arquivo .env NÃO encontrado")
        print("   Copie .env.prod.example para .env e configure os valores")
        return 1
    
    # 4. Validar arquivos Python
    print("\nValidando arquivos Python:")
    
    python_files = [
        "app/main.py",
        "app/settings.py",
        "app/integrations/meta/webhook.py",
        "app/integrations/meta/client.py",
        "app/api/chat.py",
        "app/secrets.py",
    ]
    
    for py_file in python_files:
        file_path = project_root / py_file
        if file_path.exists():
            print(f"  ✅ {py_file}")
        else:
            print(f"  ❌ {py_file} - ARQUIVO NÃO ENCONTRADO")
    
    # 5. Resumo
    print("\n" + "="*60)
    print("RESUMO")
    print("="*60)
    
    if all(results):
        print("✅ Setup completo com sucesso!")
        print("\nPróximos passos:")
        print("  1. Configure o arquivo .env com valores reais")
        print("  2. Execute: docker-compose up -d --build")
        print("  3. Valide segurança seguindo docs/security_improvements.md")
        print("  4. Execute testes: pytest tests/")
        return 0
    else:
        print("❌ Setup teve falhas. Verifique os erros acima.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
