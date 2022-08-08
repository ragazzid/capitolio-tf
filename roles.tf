data "aws_iam_policy_document" "dns_helper_role" {
  statement {
    actions = [
      "sts:AssumeRole"
    ]

    principals {
      identifiers = [
        "lambda.amazonaws.com"
      ]
      type = "Service"
    }
  }
}

resource "aws_iam_role" "dns_helper" {
  name = "dns_helper"

  assume_role_policy = data.aws_iam_policy_document.dns_helper_role.json
}

resource "aws_iam_role_policy_attachment" "lambda" {
  role       = aws_iam_role.dns_helper.name
  policy_arn = aws_iam_policy.dns_helper.arn
}


output "role_info" {
  value = aws_iam_role.dns_helper
}