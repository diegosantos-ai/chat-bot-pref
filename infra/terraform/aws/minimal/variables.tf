variable "aws_region" {
  description = "Regiao AWS usada no provisionamento."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Nome base do projeto para tags e recursos."
  type        = string
  default     = "chat-pref"
}

variable "environment" {
  description = "Nome curto do ambiente."
  type        = string
  default     = "demo"
}

variable "availability_zone_suffix" {
  description = "Sufixo da zona publica usada no recorte minimo."
  type        = string
  default     = "a"
}

variable "vpc_cidr" {
  description = "CIDR da VPC dedicada da demonstracao."
  type        = string
  default     = "10.30.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR da subnet publica da instancia."
  type        = string
  default     = "10.30.1.0/24"
}

variable "instance_type" {
  description = "Tipo da instancia EC2."
  type        = string
  default     = "t3.micro"
}

variable "root_volume_size" {
  description = "Tamanho em GB do disco raiz."
  type        = number
  default     = 16
}

variable "service_port" {
  description = "Porta publica exposta pela API."
  type        = number
  default     = 8000
}

variable "service_ingress_cidrs" {
  description = "CIDRs autorizados a acessar a API publica."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "repo_url" {
  description = "Repositorio Git usado no bootstrap da instancia."
  type        = string
  default     = "https://github.com/diegosantos-ai/chat-bot-pref.git"
}

variable "app_ref" {
  description = "Branch, tag ou ref Git a ser deployada na instancia."
  type        = string
  default     = "develop"
}

variable "tenant_manifest" {
  description = "Manifest do tenant demonstrativo a ser bootstrapado na instancia."
  type        = string
  default     = "tenants/prefeitura-vila-serena/tenant.json"
}

variable "telemetry_allowed_hosts" {
  description = "Hosts confiaveis aceitos pelo runtime em nuvem."
  type        = list(string)
  default     = ["*"]
}

variable "cors_origins" {
  description = "Origens CORS aceitas pelo runtime em nuvem."
  type        = list(string)
  default     = ["http://localhost:8000"]
}

variable "llm_provider" {
  description = "Provedor LLM do deploy remoto."
  type        = string
  default     = "mock"
}

variable "llm_model" {
  description = "Modelo LLM usado no deploy remoto."
  type        = string
  default     = "mock-compose-v1"
}

variable "llm_api_key" {
  description = "Chave opcional do provedor LLM."
  type        = string
  default     = ""
  sensitive   = true
}

variable "telegram_bot_token" {
  description = "Token opcional do bot Telegram para o ambiente em nuvem."
  type        = string
  default     = ""
  sensitive   = true
}

variable "telegram_webhook_secret" {
  description = "Secret opcional do webhook Telegram."
  type        = string
  default     = "troque-este-secret"
  sensitive   = true
}

variable "telegram_default_tenant_id" {
  description = "Tenant padrao do Telegram no ambiente em nuvem."
  type        = string
  default     = "prefeitura-vila-serena"
}

variable "telegram_delivery_mode" {
  description = "Modo de entrega do Telegram no ambiente em nuvem."
  type        = string
  default     = "disabled"
}

variable "extra_tags" {
  description = "Tags extras aplicadas aos recursos."
  type        = map(string)
  default     = {}
}
