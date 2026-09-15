# Observabilidad y control de gasto.
#
# El presupuesto esta aqui a proposito y no como nota en el README: la cuenta
# de AWS es prestada, y una alarma de gasto declarada en codigo es la unica
# que no se olvida de crear.

resource "aws_budgets_budget" "mensual" {
  name         = "${var.project}-mensual"
  budget_type  = "COST"
  limit_amount = tostring(var.budget_limit_usd)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  cost_filter {
    name = "TagKeyValue"
    # El formato que espera Budgets es "user:Clave$Valor". No se interpola
    # dentro de la cadena porque `$${` es el escape de un `${` literal en HCL
    # y saldria el texto sin sustituir.
    values = [format("user:Project$%s", var.project)]
  }

  # Al 80% avisa de lo gastado; al 100% avisa de lo PREVISTO, que llega antes
  # de que el dano este hecho.
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.alert_email]
  }
}

resource "aws_sns_topic" "alarmas" {
  name = "${var.project}-alarmas"
  tags = { Name = "${var.project}-alarmas" }
}

resource "aws_sns_topic_subscription" "alarmas_email" {
  topic_arn = aws_sns_topic.alarmas.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# Errores 5xx que devuelve la propia aplicacion. Los del ALB (502/503) son otra
# metrica distinta: esos significan que el contenedor ni contesto.
resource "aws_cloudwatch_metric_alarm" "api_5xx" {
  alarm_name        = "${var.project}-api-5xx"
  alarm_description = "La API devuelve errores de servidor de forma sostenida"

  namespace   = "AWS/ApplicationELB"
  metric_name = "HTTPCode_Target_5XX_Count"
  statistic   = "Sum"
  period      = 300

  # Dos periodos seguidos, no uno: un pico aislado de 5xx durante un despliegue
  # es normal y no debe despertar a nadie.
  evaluation_periods  = 2
  threshold           = 5
  comparison_operator = "GreaterThanThreshold"

  # Si no hubo trafico no hay datos, y "sin datos" no es un fallo.
  treat_missing_data = "notBreaching"

  dimensions = {
    LoadBalancer = aws_lb.principal.arn_suffix
    TargetGroup  = aws_lb_target_group.api.arn_suffix
  }

  alarm_actions = [aws_sns_topic.alarmas.arn]
  ok_actions    = [aws_sns_topic.alarmas.arn]

  tags = { Name = "${var.project}-api-5xx" }
}

# Sin tareas sanas el servicio esta caido, sin matices.
resource "aws_cloudwatch_metric_alarm" "sin_tareas_sanas" {
  alarm_name        = "${var.project}-sin-tareas-sanas"
  alarm_description = "Ninguna tarea de la API pasa el health check"

  namespace   = "AWS/ApplicationELB"
  metric_name = "HealthyHostCount"
  statistic   = "Minimum"
  period      = 60

  evaluation_periods  = 2
  threshold           = 1
  comparison_operator = "LessThanThreshold"
  treat_missing_data  = "breaching" # aqui la ausencia de datos SI es un fallo

  dimensions = {
    LoadBalancer = aws_lb.principal.arn_suffix
    TargetGroup  = aws_lb_target_group.api.arn_suffix
  }

  alarm_actions = [aws_sns_topic.alarmas.arn]

  tags = { Name = "${var.project}-sin-tareas-sanas" }
}

# El disco de RDS no crece solo mas alla de max_allocated_storage, y quedarse
# sin espacio deja la base en read-only.
resource "aws_cloudwatch_metric_alarm" "rds_disco" {
  alarm_name        = "${var.project}-rds-disco-bajo"
  alarm_description = "Queda menos de 2 GB libres en la instancia de Postgres"

  namespace   = "AWS/RDS"
  metric_name = "FreeStorageSpace"
  statistic   = "Average"
  period      = 300

  evaluation_periods  = 1
  threshold           = 2 * 1024 * 1024 * 1024 # bytes
  comparison_operator = "LessThanThreshold"

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.principal.identifier
  }

  alarm_actions = [aws_sns_topic.alarmas.arn]

  tags = { Name = "${var.project}-rds-disco-bajo" }
}
