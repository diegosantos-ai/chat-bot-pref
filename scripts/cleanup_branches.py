#!/usr/bin/env python3
"""
Script para limpar branches do repositório.
Mantém apenas main e develop, mergeando todas as outras na develop.
"""

import subprocess
import sys
from typing import List


def run_command(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Executa um comando e retorna o resultado."""
    print(f"🔧 Executando: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    
    if check and result.returncode != 0:
        print(f"❌ Erro ao executar comando: {' '.join(cmd)}")
        print(f"   stdout: {result.stdout}")
        print(f"   stderr: {result.stderr}")
        sys.exit(1)
    
    return result


def get_current_branch() -> str:
    """Retorna o nome da branch atual."""
    result = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    return result.stdout.strip()


def get_remote_branches() -> List[str]:
    """Retorna lista de branches remotas (exceto main e develop)."""
    result = run_command(["git", "branch", "-r"])
    branches = []
    
    for line in result.stdout.split("\n"):
        line = line.strip()
        if not line or "->" in line:
            continue
        
        # Remove 'origin/' prefix
        if line.startswith("origin/"):
            branch = line[7:]  # len("origin/") = 7
            
            # Skip main and develop
            if branch not in ["main", "develop"]:
                branches.append(branch)
    
    return branches


def main():
    print("🔧 Iniciando limpeza de branches...")
    print()
    
    # Verificar se estamos em um repositório git
    result = run_command(["git", "rev-parse", "--git-dir"], check=False)
    if result.returncode != 0:
        print("❌ Erro: Este não é um repositório git!")
        sys.exit(1)
    
    # Fetch all branches
    print("📥 Fazendo fetch de todas as branches remotas...")
    run_command(["git", "fetch", "--all"])
    print()
    
    # Checkout para develop
    current_branch = get_current_branch()
    if current_branch != "develop":
        print("🔄 Fazendo checkout para develop...")
        run_command(["git", "checkout", "develop"])
        print()
    
    # Pull latest develop
    print("📥 Atualizando develop...")
    result = run_command(["git", "pull", "origin", "develop"], check=False)
    print()
    
    # Obter lista de branches para merge
    print("📋 Identificando branches para merge...")
    branches_to_merge = get_remote_branches()
    
    if not branches_to_merge:
        print("✅ Nenhuma branch adicional encontrada para merge")
    else:
        print(f"🔍 Branches encontradas para merge: {len(branches_to_merge)}")
        for branch in branches_to_merge:
            print(f"   - {branch}")
        print()
        
        # Merge each branch into develop
        for branch in branches_to_merge:
            print(f"🔀 Mergeando branch: {branch}")
            
            # Tentar merge
            result = run_command(
                ["git", "merge", f"origin/{branch}", "--no-edit", "-m", f"Merge branch '{branch}' into develop"],
                check=False
            )
            
            if result.returncode != 0:
                print(f"⚠️  Conflito ao mergear {branch} - resolvendo automaticamente usando theirs")
                run_command(["git", "merge", "--abort"], check=False)
                run_command(
                    ["git", "merge", f"origin/{branch}", "-X", "theirs", "--no-edit", "-m", f"Merge branch '{branch}' into develop"]
                )
            else:
                print(f"✅ Branch {branch} mergeada com sucesso")
            print()
    
    # Push develop
    print("📤 Fazendo push de develop...")
    run_command(["git", "push", "origin", "develop"])
    print()
    
    # Delete remote branches
    if branches_to_merge:
        print("🗑️  Deletando branches remotas...")
        for branch in branches_to_merge:
            print(f"🗑️  Deletando branch remota: {branch}")
            result = run_command(["git", "push", "origin", "--delete", branch], check=False)
            if result.returncode != 0:
                print(f"⚠️  Falha ao deletar {branch} (pode já estar deletada)")
        print()
    
    # Cleanup local branches
    print("🧹 Limpando branches locais...")
    result = run_command(["git", "branch"], check=False)
    local_branches = [b.strip().replace("* ", "") for b in result.stdout.split("\n") if b.strip()]
    
    for branch in local_branches:
        if branch not in ["main", "develop"]:
            print(f"🗑️  Deletando branch local: {branch}")
            run_command(["git", "branch", "-D", branch], check=False)
    print()
    
    print("✅ Limpeza concluída!")
    print("📊 Branches restantes:")
    result = run_command(["git", "branch", "-a"])
    for line in result.stdout.split("\n"):
        if "main" in line or "develop" in line:
            print(f"   {line}")


if __name__ == "__main__":
    main()
