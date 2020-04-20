# RagazziD AWS DNS Helper - Capitólio
It receives an EC2 event:
* running
* shutting-down

Based on the event, it creates or remove A record from a given DNS_ZONE based on the tag Name of an instance, if the instance belongs to an ASG it will add last 3 last ipv4 octets to the name
        
## Variables for the Script

| Name          | Description   | Mandatory | Default                |
| -----------   | ------------- | --------- | ---------------------- |
| ZONE_NAME     | example.com   | YES       |                        | 
| ZONE_ID       | Z3VXULJR1UZ2O | YES       |                        | 
| DYNAMO_TABLE  | String        | NO        | RagazziD_Capitolio_Dns |
| PUBLIC        | Boolean       | NO        | False                  |
| PUBLIC_PREFIX | String        | NO        | p-                     |

** Variables for the Lambda

| Name          | Description    | Mandatory | Default   |
| -----------   | -------------  | --------- | --------- |
| dynamo_arn    | used for IAM   | NO        | *         | 
| hosted_zone   | used for IAM   | NO        | *         | 
| dns_helper    | Lambda name    | NO        | capitolio |
## Deploy to AWS
### Terraform
```
resource "aws_route53_zone" "ragazzid" {
  name = "burn.ragazzid.com.br"
}

module "capitolio-tf" {
  source = "github.com/ragazzid/capitolio-tf.git"

  variables = {
    ZONE_NAME = aws_route53_zone.ragazzid.name
    ZONE_ID   = aws_route53_zone.ragazzid.zone_id
    PUBLIC    = "True"
  }
}
```