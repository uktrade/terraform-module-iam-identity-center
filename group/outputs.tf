output "groups" {
    value = aws_identitystore_group.groups
}

output "entitlements" {
    value = aws_ssoadmin_account_assignment.entitlements
}
