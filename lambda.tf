
resource "aws_lambda_function" "dns_helper" {
  filename         = "https://github.com/ragazzid/capitolio/archive/v0.0.2.zip"
  source_code_hash = filebase64sha256("https://github.com/ragazzid/capitolio/archive/v0.0.2.zip")

  function_name = var.dns_helper
  role          = aws_iam_role.dns_helper.arn
  handler       = "main.handler"
  timeout       = var.timeout

  runtime = "python3.7"

  environment {
    variables = var.variables
  }
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dns_helper.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.this.arn
}