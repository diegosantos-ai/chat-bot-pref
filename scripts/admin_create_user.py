#!/usr/bin/env python3
"""
Script para criar usuário administrador do painel {bot_name}.

Uso:
    python scripts/admin_create_user.py <username> <password> [--role admin|operator|viewer]
    python scripts/admin_create_user.py --list

Exemplo:
    python scripts/admin_create_user.py admin123 minhaSenha123 --role admin
"""

import sys
import os
import asyncio
import argparse
import getpass

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncpg
import bcrypt
from app.settings import settings


async def create_user(username: str, password: str, role: str = "admin") -> bool:
    """Cria um novo usuário administrador."""

    valid_roles = ["admin", "operator", "viewer"]
    if role not in valid_roles:
        print(f"❌ Role inválida: {role}")
        print(f"   Roles válidas: {', '.join(valid_roles)}")
        return False

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )

    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)

        try:
            existing = await conn.fetchrow(
                "SELECT id, username FROM admin_users WHERE username = $1", username
            )

            if existing:
                print(f"❌ Usuário '{username}' já existe!")
                return False

            await conn.execute(
                "INSERT INTO admin_users (username, password_hash, role) VALUES ($1, $2, $3)",
                username,
                password_hash,
                role,
            )

            print(f"✅ Usuário '{username}' criado com role '{role}'")
            return True

        finally:
            await conn.close()

    except Exception as e:
        print(f"❌ Erro ao criar usuário: {e}")
        return False


async def list_users() -> None:
    """Lista todos os usuários administradores."""

    try:
        conn = await asyncpg.connect(settings.DATABASE_URL)

        try:
            users = await conn.fetch(
                "SELECT id, username, role, ativo, criado_em, ultimo_login FROM admin_users ORDER BY username"
            )

            if not users:
                print("📭 Nenhum usuário administrador encontrado.")
                return

            print(f"\n👥 Usuários administradores ({len(users)}):")
            print("-" * 80)
            for u in users:
                status = "✅ Ativo" if u["ativo"] else "❌ Inativo"
                ultimo = (
                    u["ultimo_login"].strftime("%d/%m/%Y %H:%M")
                    if u["ultimo_login"]
                    else "Nunca"
                )
                print(
                    f"  • {u['username']:20s} | {u['role']:10s} | {status} | último login: {ultimo}"
                )
            print()

        finally:
            await conn.close()

    except Exception as e:
        print(f"❌ Erro ao listar usuários: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Gerenciar usuários administradores do painel {bot_name}"
    )
    parser.add_argument("username", nargs="?", help="Nome de usuário")
    parser.add_argument("password", nargs="?", help="Senha do usuário")
    parser.add_argument(
        "--role",
        default="admin",
        choices=["admin", "operator", "viewer"],
        help="Papel do usuário (default: admin)",
    )
    parser.add_argument(
        "--list", action="store_true", help="Listar usuários existentes"
    )

    args = parser.parse_args()

    if args.list:
        asyncio.run(list_users())
    elif args.username and args.password:
        asyncio.run(create_user(args.username, args.password, args.role))
    else:
        print("🐍 Modo interativo - Criar usuário administrador")
        print("=" * 50)

        username = input("Username: ").strip()
        if not username:
            print("❌ Username não pode ser vazio")
            sys.exit(1)

        password = getpass.getpass("Senha: ")
        if not password:
            print("❌ Senha não pode ser vazia")
            sys.exit(1)

        password_confirm = getpass.getpass("Confirmar senha: ")
        if password != password_confirm:
            print("❌ Senhas não conferem")
            sys.exit(1)

        print("\nRoles disponíveis:")
        print("  1. admin   - Acesso completo")
        print("  2. operator - Operações (logs, RAG)")
        print("  3. viewer   - Apenas visualização")

        role_choice = input("Escolha (1-3) [1]: ").strip() or "1"
        role_map = {"1": "admin", "2": "operator", "3": "viewer"}
        role = role_map.get(role_choice, "admin")

        asyncio.run(create_user(username, password, role))


if __name__ == "__main__":
    main()
