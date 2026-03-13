# Skill: deploy-aws-ec2

## Quando usar
- Em tarefas de desenho ou execucao de deploy minimo em AWS com EC2 e Terraform.

## Objetivo
- Manter uma estrategia de deploy simples, explicavel e coerente com o case demonstrativo.

## Checklist
1. Confirmar precondicoes: Docker confiavel, variaveis de ambiente definidas e alvo AWS escolhido.
2. Limitar a infraestrutura ao minimo necessario.
3. Separar claramente provisionamento, configuracao e deploy da aplicacao.
4. Registrar dependencias externas, segredos e validacao pos-deploy.

## Evidencias minimas
- componentes provisionados
- segredo fora do repositorio
- comando ou fluxo de deploy
- validacao do servico publicado
