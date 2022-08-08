
output "role_info" {
  value = aws_iam_role.dns_helper
}

output "lambda_info" {
  value = aws_lambda_function.dns_helper
}