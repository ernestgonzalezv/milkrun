# Lo que hace falta despues del apply: para desplegar, para probar y para
# verificar que el destroy no dejo nada.

output "api_url" {
  description = "Base de la API. Sin dominio propio se queda en HTTP; los outputs no mienten sobre eso."
  value       = local.https_habilitado ? "https://${var.domain_name}" : "http://${aws_lb.principal.dns_name}"
}

output "dashboard_url" {
  description = "Dashboard servido por CloudFront, con HTTPS del certificado por defecto."
  value       = "https://${aws_cloudfront_distribution.web.domain_name}"
}

output "seguimiento_publico_ejemplo" {
  description = "Endpoint sin autenticacion: es el que se le manda a alguien para que vea la demo."
  value       = "${local.https_habilitado ? "https://${var.domain_name}" : "http://${aws_lb.principal.dns_name}"}/api/v1/track/CODIGO/"
}

output "ecr_repository_url" {
  description = "Destino del docker push en el pipeline de despliegue."
  value       = aws_ecr_repository.api.repository_url
}

output "comando_migrar" {
  description = "Migraciones antes de cada despliegue. Es un paso del deploy, no del arranque."
  value = join(" ", [
    "aws ecs run-task",
    "--cluster ${aws_ecs_cluster.principal.name}",
    "--task-definition ${aws_ecs_task_definition.migrate.family}",
    "--launch-type FARGATE",
    "--network-configuration 'awsvpcConfiguration={subnets=[${join(",", aws_subnet.privada[*].id)}],securityGroups=[${aws_security_group.ecs.id}],assignPublicIp=DISABLED}'",
  ])
}

output "s3_bucket_dashboard" {
  description = "Destino del `aws s3 sync` del build de Vite."
  value       = aws_s3_bucket.web.id
}

output "db_endpoint" {
  description = "Host de Postgres. Solo alcanzable desde las subnets privadas."
  value       = aws_db_instance.principal.address
}

# La contrasena NO se expone como output, ni siquiera marcada como sensitive:
# un output sensitive sigue siendo legible con `terraform output -json`.
# Quien la necesite la lee de Parameter Store, que deja registro en CloudTrail.
output "parametros_ssm" {
  description = "Donde viven los secretos. El valor se lee con `aws ssm get-parameter --with-decryption`."
  value = {
    django_secret_key = aws_ssm_parameter.django_secret_key.name
    database_url      = aws_ssm_parameter.database_url.name
  }
}

output "verificar_destroy" {
  description = "Tras el destroy esto debe devolver una lista vacia. La cuenta es prestada."
  value       = "aws resourcegroupstaggingapi get-resources --tag-filters Key=Project,Values=${var.project} --region ${var.aws_region}"
}
