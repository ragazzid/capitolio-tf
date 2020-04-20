data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/src"
  output_path = "${path.module}/lambda.zip"
}

resource "aws_lambda_function" "dns_helper" {
  filename         = "${path.module}/lambda.zip"
  source_code_hash = filebase64sha256("${path.module}/lambda.zip")

  function_name = var.dns_helper
  role          = aws_iam_role.dns_helper.arn
  handler       = "main.handler"
  timeout       = var.timeout

  runtime = "python3.7"

  environment {
    variables = var.variables
  }
  tags = {
    CodeSHA = data.archive_file.lambda_zip.output_base64sha256
  }
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.dns_helper.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.this.arn
}