output "instance_id" {
  description = "ID da instancia EC2 provisionada."
  value       = aws_instance.app.id
}

output "public_ip" {
  description = "IP publico estavel do ambiente."
  value       = aws_eip.app.public_ip
}

output "public_dns" {
  description = "DNS publico da instancia EC2."
  value       = aws_instance.app.public_dns
}

output "base_url" {
  description = "URL base da API em nuvem."
  value       = "http://${aws_eip.app.public_ip}:${var.service_port}"
}

output "public_hostname" {
  description = "Hostname publico recomendado para HTTPS no deploy remoto."
  value       = local.public_https_hostname
}

output "https_base_url" {
  description = "URL HTTPS publica recomendada para o Chat Pref."
  value       = var.public_https_enabled ? "https://${local.public_https_hostname}" : null
}

output "health_url" {
  description = "URL remota do healthcheck."
  value       = "http://${aws_eip.app.public_ip}:${var.service_port}/health"
}

output "https_health_url" {
  description = "URL HTTPS remota do healthcheck."
  value       = var.public_https_enabled ? "https://${local.public_https_hostname}/health" : null
}

output "metrics_url" {
  description = "URL remota das metricas."
  value       = "http://${aws_eip.app.public_ip}:${var.service_port}/metrics"
}

output "telegram_webhook_url" {
  description = "Webhook HTTPS recomendado para ativacao do Telegram."
  value       = var.public_https_enabled ? "https://${local.public_https_hostname}/api/telegram/webhook" : null
}

output "ssm_start_session_command" {
  description = "Comando sugerido para abrir sessao remota via AWS SSM."
  value       = "aws ssm start-session --target ${aws_instance.app.id} --region ${var.aws_region}"
}
