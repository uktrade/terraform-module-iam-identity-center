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

# Build organisation OU Account map

locals {
  # Map of all accounts directly in the OU. This only contains immediate child accounts, not all children from descendent OUs.
  child_account_map = {
    for ou in keys(local.org_ou_map) : "${ou}" => merge (
      { "active" = [
        for account in data.aws_organizations_organizational_unit_child_accounts.accounts[ou].accounts :
          account.name if account.status == "ACTIVE"
      ]},
      { "inactive" = [
        for account in data.aws_organizations_organizational_unit_child_accounts.accounts[ou].accounts :
          account.name if account.status != "ACTIVE"
      ]}
    )
  }
  # Map of all accounts in the OU. This contains all accounts from the OU and all descendant / child OUs.
  descendant_account_map = {
    for ou in keys(local.org_ou_map) : "${ou}" => merge (
      { "active" = [
        for account in data.aws_organizations_organizational_unit_descendant_accounts.accounts[ou].accounts :
          account.name if account.status == "ACTIVE"
      ]},
      { "inactive" = [
        for account in data.aws_organizations_organizational_unit_descendant_accounts.accounts[ou].accounts :
          account.name if account.status != "ACTIVE"
      ]}
    )
  }
  # Combined map of the two above.
  org_ou_account_map = merge(
    { "child_accounts" = local.child_account_map },
    { "descendant_accounts" = local.descendant_account_map },
  )
}
