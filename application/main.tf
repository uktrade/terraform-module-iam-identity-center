# Applications

resource "aws_ssoadmin_application" "sso_application" {
  name = var.args.name
  instance_arn = try ( var.args.instance_arn, var.identity_store.arns[0] )
  application_provider_arn = var.args.application_provider_arn
  client_token = try ( var.args.client_token, null )
  description = try ( var.args.description, null )
  status = try ( var.args.status, null )

  dynamic "portal_options" {
    for_each = try ( var.args.portal_options, [] )
    content {
      visibility = try ( portal_options.value.visibility, null )
      dynamic "sign_in_options" {
        for_each = try ( portal_options.value.sign_in_options, [] )
        content {
          application_url = try ( sign_in_options.value.application_url, null )
          origin = sign_in_options.value.origin
        }
      }
    }
  }

  tags = try ( var.args.tags, null )

}
