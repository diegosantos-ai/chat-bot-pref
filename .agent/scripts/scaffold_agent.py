import os
import sys
import argparse
from pathlib import Path

def create_scaffold(name, desc, skills):
    base_dir = Path(r"C:\Users\santo\.agent")
    templates_dir = base_dir / "templates" / "agent_base"
    agents_dir = base_dir / "agents"
    skills_dir = base_dir / "skills"

    # Ler templates
    agent_tpl_path = templates_dir / "AGENT_TEMPLATE.md"
    skill_tpl_path = templates_dir / "SKILL_TEMPLATE.md"

    if not agent_tpl_path.exists() or not skill_tpl_path.exists():
        print(f"ERRO: Templates base não encontrados em {templates_dir}")
        sys.exit(1)

    with open(agent_tpl_path, "r", encoding="utf-8") as f:
        agent_content = f.read()

    with open(skill_tpl_path, "r", encoding="utf-8") as f:
        skill_content = f.read()

    # Formatar o bloco YAML de skills
    skills_list = [s.strip() for s in skills.split(",")]
    skills_yaml = "\n".join([f"  - {s}" for s in skills_list]) if skills_list else "  - default-skill"

    # Substituir no Agente
    agent_output = agent_content.replace("{AGENT_NAME_TITLE}", name.replace("-", " ").title())
    agent_output = agent_output.replace("{AGENT_DESCRIPTION}", desc)
    agent_output = agent_output.replace("{SKILLS_LIST}", skills_yaml)

    # Escrever Agente
    agent_file = agents_dir / f"{name}.md"
    with open(agent_file, "w", encoding="utf-8") as f:
        f.write(agent_output)
    print(f"✅ Agente '{name}' criado com sucesso em: {agent_file}")

    # Escrever Skills
    for skill in skills_list:
        if not skill: continue
        skill_path = skills_dir / skill
        skill_path.mkdir(parents=True, exist_ok=True)
        
        skill_file = skill_path / "SKILL.md"
        # Substitui na Skill
        s_out = skill_content.replace("{SKILL_NAME_TITLE}", skill.replace("-", " ").title())
        s_out = s_out.replace("{SKILL_DESCRIPTION}", f"Atribuição delegada pelo agente {name}")
        
        with open(skill_file, "w", encoding="utf-8") as f:
            f.write(s_out)
        print(f"✅ Skill '{skill}' criada com sucesso em: {skill_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent Scaffolding Factory")
    parser.add_argument("--name", required=True, help="O nome exato do arquivo do agente (em kebab-case). Ex: neo-backend")
    parser.add_argument("--desc", required=True, help="Uma linha curta explicando a persona")
    parser.add_argument("--skills", required=True, help="Lista de nomes das skills separados por virgula. Ex: fastpi-pro,sql-patterns")
    
    args = parser.parse_args()
    create_scaffold(args.name, args.desc, args.skills)
