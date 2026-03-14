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

output "health_url" {
  description = "URL remota do healthcheck."
  value       = "http://${aws_eip.app.public_ip}:${var.service_port}/health"
}

output "metrics_url" {
  description = "URL remota das metricas."
  value       = "http://${aws_eip.app.public_ip}:${var.service_port}/metrics"
}

output "ssm_start_session_command" {
  description = "Comando sugerido para abrir sessao remota via AWS SSM."
  value       = "aws ssm start-session --target ${aws_instance.app.id} --region ${var.aws_region}"
}
