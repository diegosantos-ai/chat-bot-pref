#!/usr/bin/env python3
"""
Script para remover usuário administrador do painel TerezIA.

Uso:
    python scripts/admin_delete_user.py <username>

Exemplo:
    python scripts/admin_delete_user.py admin123
"""

import sys
import os
import asyncio
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncpg
from app.settings import settings


async def delete_user(username: str, force: bool = False) -> bool:
    """Remove um usuário administrador."""
    
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        
        try:
            # Verificar se usuário existe
            user = await conn.fetchrow(
                "SELECT id, username FROM admin_users WHERE username = $1",
                username
            )
            
            if not user:
                print(f"❌ Usuário '{username}' não encontrado!")
                return False
            
            if not force:
                confirm = input(f"❓ Tem certeza que deseja remover '{username}'? (s/N): ").strip().lower()
                if confirm != "s":
                    print("ℹ️  Cancelado.")
                    return False
            
            # Remover usuário
            await conn.execute(
                "DELETE FROM admin_users WHERE username = $1",
                username
            )
            
            print(f"✅ Usuário '{username}' removido com sucesso!")
            return True
            
        finally:
            await conn.close()
            
    except Exception as e:
        print(f"❌ Erro ao remover usuário: {e}")
        return False


async def deactivate_user(username: str) -> bool:
    """Desativa um usuário sem remover."""
    
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        
        try:
            user = await conn.fetchrow(
                "SELECT id, username FROM admin_users WHERE username = $1",
                username
            )
            
            if not user:
                print(f"❌ Usuário '{username}' não encontrado!")
                return False
            
            await conn.execute(
                "UPDATE admin_users SET ativo = FALSE WHERE username = $1",
                username
            )
            
            print(f"✅ Usuário '{username}' desativado!")
            return True
            
        finally:
            await conn.close()
            
    except Exception as e:
        print(f"❌ Erro ao desativar usuário: {e}")
        return False


async def reactivate_user(username: str) -> bool:
    """Reativa um usuário desativado."""
    
    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)
        
        try:
            user = await conn.fetchrow(
                "SELECT id, username FROM admin_users WHERE username = $1",
                username
            )
            
            if not user:
                print(f"❌ Usuário '{username}' não encontrado!")
                return False
            
            await conn.execute(
                "UPDATE admin_users SET ativo = TRUE WHERE username = $1",
                username
            )
            
            print(f"✅ Usuário '{username}' reativado!")
            return True
            
        finally:
            await conn.close()
            
    except Exception as e:
        print(f"❌ Erro ao reativar usuário: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Remover usuários administradores do painel TerezIA")
    subparsers = parser.add_subparsers(dest="command", help="Comandos")
    
    # Comando delete
    delete_parser = subparsers.add_parser("delete", help="Remover usuário permanentemente")
    delete_parser.add_argument("username", help="Nome de usuário")
    delete_parser.add_argument("-f", "--force", action="store_true", 
                              help="Não pedir confirmação")
    
    # Comando deactivate
    deactivate_parser = subparsers.add_parser("deactivate", help="Desativar usuário")
    deactivate_parser.add_argument("username", help="Nome de usuário")
    
    # Comando reactivate
    reactivate_parser = subparsers.add_parser("reactivate", help="Reativar usuário")
    reactivate_parser.add_argument("username", help="Nome de usuário")
    
    args = parser.parse_args()
    
    if args.command == "delete":
        asyncio.run(delete_user(args.username, args.force))
    elif args.command == "deactivate":
        asyncio.run(deactivate_user(args.username))
    elif args.command == "reactivate":
        asyncio.run(reactivate_user(args.username))
    else:
        # Interactive mode
        print("🐍 Modo interativo - Remover usuário administrador")
        print("=" * 50)
        
        username = input("Username a remover: ").strip()
        if not username:
            print("❌ Username não pode ser vazio")
            sys.exit(1)
        
        asyncio.run(delete_user(username, force=False))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
