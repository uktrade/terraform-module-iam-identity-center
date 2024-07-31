output "permission_set" {
    value = aws_ssoadmin_permission_set.permission_set
}

output "inline_policy" {
    value = aws_ssoadmin_permission_set_inline_policy.inline_policy
}

output "aws_managed_policy" {
    value = data.aws_iam_policy.aws_managed_policies
}

output "aws_managed_policy_attachment" {
    value = aws_ssoadmin_managed_policy_attachment.aws_managed_policies
}

