variable "dns_helper" {
  default = "capitolio"
}

variable "variables" {
  type = map
  default = {
    ZONE_NAME = "example.com"
    ZONE_ID   = "Z3VXULJR1UZ2O"
    PUBLIC    = "True"
  }
}

variable "dynamo_arn" {
  default = "*"
}

variable "hosted_zone" {
    default = "*"
}

variable "timeout" {
  default = "60"
}