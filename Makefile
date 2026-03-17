# Makefile para DevOps Workspace Central

.PHONY: help setup lint test update dbg

# Cores para output
CYAN := \033[36m
RESET := \033[0m

help: ## Mostra esta mensagem de ajuda
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "$(CYAN)%-20s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: ## Bootstrapping inicial da nova máquina (instala pacotes, links de dotfiles)
	@echo "Iniciando setup da máquina..."
	@bash scripts/setup-machine.sh

lint: ## Roda linters em todo o repositório (Shell, Terraform, Python, Markdown)
	@echo "Executando pre-commit hooks..."
	@pre-commit run --all-files

update: ## Atualiza repositórios, dotfiles e pacotes locais
	@echo "Atualizando ambiente local..."
	@git pull origin main
	# Adicionar comandos de update do sistema operacional aqui

morning: ## Roda a rotina matinal (abre arquivos de playbook e executa o check)
	@bash scripts/open_devops_routine.sh

audit: ## Dispara script completo de auditoria do sistema operacional e CLI libs
	@bash scripts/check_devops_env.sh
