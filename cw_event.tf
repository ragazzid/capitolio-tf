resource "aws_cloudwatch_event_rule" "this" {
  name        = "capture_start_terminate_instance"
  description = "Get signal of start/terminating instances"

  event_pattern = file("${path.module}/files/ec2_event_pattern.json")
}

resource "aws_cloudwatch_event_target" "this" {
  rule      = aws_cloudwatch_event_rule.this.name
  target_id = "sendToDnsExporter"
  arn       = aws_lambda_function.dns_helper.arn
}