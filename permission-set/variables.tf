variable "args" {
  description = "A map of arguments to apply to IAM."
  type = any
}

variable "identity_store" {
  description = "AWS Identity Centre configuration."
  type = any
}

variable "tags" {
  description = "A map of tags to assign to the resources."
  type = map(any)
  default = {}
}

