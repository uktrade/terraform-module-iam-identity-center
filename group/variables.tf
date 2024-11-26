variable "args" {
  description = "A map of arguments to apply to IDC Groups."
  type = any
}

variable "identity_store" {
  description = "AWS Identity Centre configuration."
  type = any
}

variable "permission_sets" {
  description = "A map of outputs (resources) from the permission_set module."
  type = map(any)
}

variable "applications" {
  description = "A map of application resources from the application module."
  type = map(any)
  default = {}
}

variable "aws_account_map" {
  description = "A map of organisation accounts, keyed by name."
  type = map(string)
}

variable "org_ou_account_map" {
  description = "A map of organisation OUs and AWS accounts."
  type = map(any)
  default = {}
}
