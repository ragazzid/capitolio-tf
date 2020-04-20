
data "aws_iam_policy_document" "dns_helper" {
  statement {

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]

    resources = [
      "arn:aws:logs:*:*:*",
    ]
  }

  statement {
    actions = [
      "dynamodb:BatchGetItem",
      "dynamodb:BatchWriteItem",
      "dynamodb:CreateTable",
      "dynamodb:ListTables",
      "dynamodb:DeleteItem",
      "dynamodb:DescribeTable",
      "dynamodb:GetItem",
      "dynamodb:GetRecords",
      "dynamodb:GetShardIterator",
      "dynamodb:PutItem"
    ]

    resources = [
      var.dynamo_arn,
    ]
  }
  statement {
    actions = [
      "route53:ChangeResourceRecordSets",
      "route53:ListHostedZones"
    ]

    resources = [
      var.hosted_zone
    ]
  }

  statement {
    actions = [
      "ec2:DescribeFleetInstances",
      "ec2:DescribeFleets",
      "ec2:DescribeInstanceAttribute",
      "ec2:DescribeInstanceStatus",
      "ec2:DescribeInstances",
      "ec2:DescribeSubnets",
      "ec2:DescribeTags"
    ]

    resources = [
      "*"
    ]
  }
}
resource "aws_iam_policy" "dns_helper" {
  name        = "capitolio"
  description = "Permisions to allow Ec2/Logs/Route53/DynamoDB"

  policy = data.aws_iam_policy_document.dns_helper.json
}
