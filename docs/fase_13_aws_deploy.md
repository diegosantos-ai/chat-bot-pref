# Fase 13 - Infraestrutura como Codigo e Deploy em AWS

## Objetivo

Provisionar um ambiente minimo e reprodutivel na AWS para hospedar a demonstracao do Chat Pref fora da maquina local.

## Corte tecnico adotado

O recorte minimo desta fase foi definido como:

- AWS `us-east-1`
- VPC dedicada minima
- uma subnet publica
- Internet Gateway e route table publica
- uma Security Group com acesso a porta da API
- uma instancia EC2 unica
- profile IAM com AWS Systems Manager
- Elastic IP para URL estavel por IP
- deploy inicial via `user_data` + `docker compose`

Esse corte evita inflar o case com ALB, ECS, ECR, RDS ou backend remoto do Terraform antes da hora.

## Arquivos principais da fase

- `infra/terraform/aws/minimal/versions.tf`
- `infra/terraform/aws/minimal/variables.tf`
- `infra/terraform/aws/minimal/main.tf`
- `infra/terraform/aws/minimal/outputs.tf`
- `infra/terraform/aws/minimal/terraform.tfvars.example`
- `infra/terraform/aws/minimal/templates/user_data.sh.tftpl`
- `scripts/deploy_aws_instance.sh`
- `scripts/smoke_remote.py`

## Estrategia de deploy

### Primeiro deploy

1. `terraform apply` cria rede, seguranca, role SSM, EC2 e Elastic IP
2. `user_data` instala Docker, Compose, Git e Python 3
3. a instancia clona o repositorio na ref configurada
4. o script `scripts/deploy_aws_instance.sh` sobe o backend
5. o script bootstrapa o tenant `prefeitura-vila-serena`
6. o endpoint `/health` passa a responder na porta publica configurada

### Redeploy minimo

Enquanto o deploy remoto automatizado por GitHub Actions nao for fechado, o redeploy pode ser executado por SSM diretamente na instancia reaproveitando `scripts/deploy_aws_instance.sh`.

## Secrets e variaveis

### Variaveis do Terraform

- `aws_region`
- `instance_type`
- `repo_url`
- `app_ref`
- `service_ingress_cidrs`
- `tenant_manifest`

### Secrets opcionais do ambiente remoto

- `llm_api_key`
- `telegram_bot_token`
- `telegram_webhook_secret`

No corte atual, o ambiente em nuvem pode operar com:

- `LLM_PROVIDER=mock`
- Telegram em `disabled`

## Validacao local do codigo da fase

```bash
terraform -chdir=infra/terraform/aws/minimal fmt -recursive
terraform -chdir=infra/terraform/aws/minimal init -backend=false
terraform -chdir=infra/terraform/aws/minimal validate
```

## Provisionamento esperado

```bash
cp infra/terraform/aws/minimal/terraform.tfvars.example infra/terraform/aws/minimal/terraform.tfvars
terraform -chdir=infra/terraform/aws/minimal init
terraform -chdir=infra/terraform/aws/minimal apply
```

## Smoke remoto minimo

Depois do `apply`, use a URL de output da API:

```bash
.venv/bin/python scripts/smoke_remote.py \
  --base-url http://SEU_IP_PUBLICO:8000 \
  --tenant-id prefeitura-vila-serena \
  --json-out artifacts/fase13-remote-smoke.json
```

## Validacao local executada nesta branch

- `terraform fmt -recursive`
- `terraform init -backend=false`
- `terraform validate`
- `terraform plan`

O `plan` validou um corte minimo com 11 recursos AWS:

- VPC dedicada
- Internet Gateway
- subnet publica
- route table publica
- associacao da route table
- security group da API
- role IAM para SSM
- policy attachment do SSM
- instance profile
- instancia EC2
- Elastic IP
