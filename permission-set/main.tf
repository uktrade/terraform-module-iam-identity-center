# Permission Set

resource "aws_ssoadmin_permission_set" "permission_set" {
  instance_arn = var.identity_store.arns[0]
  name = var.args.name
  description = var.args.description
  relay_state = try( var.args.relay_state, null )
  session_duration = try( var.args.relay_state, "PT1H" )
  tags = var.tags
}

## Attached Inline Policy

resource "aws_ssoadmin_permission_set_inline_policy" "inline_policy" {
  count = can(var.args.inline_policy) ? 1 : 0
  instance_arn = var.identity_store.arns[0]
  permission_set_arn = aws_ssoadmin_permission_set.permission_set.arn
  inline_policy = jsonencode(var.args.inline_policy)
}

