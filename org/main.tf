# Organisation data

data "aws_organizations_organization" "org" {}

data "aws_organizations_organizational_unit_descendant_organizational_units" "ous" {
  parent_id = data.aws_organizations_organization.org.roots[0].id
}

data "aws_organizations_organizational_unit_child_accounts" "accounts" {
  for_each = local.org_ou_map
  parent_id = each.value
}

data "aws_organizations_organizational_unit_descendant_accounts" "accounts" {
  for_each = local.org_ou_map
  parent_id = each.value
}

locals {
  # Map of organisation OUs keyed by name.
  org_ou_map = merge(
    { "${data.aws_organizations_organization.org.roots[0].name}" = data.aws_organizations_organization.org.roots[0].id },
    { for ou in data.aws_organizations_organizational_unit_descendant_organizational_units.ous.children : "${ou.name}" => ou.id }
  )
}
