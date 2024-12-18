# Groups

locals {
    # Build a list of entitlements.
    group_role_list = flatten([
        for role in var.args.roles : {
            team = var.args.team.name
            role = role.name
            description = try( role.description, null )
        }  
    ])
    # Create a map of groups and desriptions, keyed by group name (i.e. team_role).
    group_role_map = {
        for group in local.group_role_list : "${group.team}_${group.role}" => {
            name = "${group.team}_${group.role}"
            description = group.description
        }
    } 
}

resource "aws_identitystore_group" "groups" {
    for_each = local.group_role_map
    display_name = each.value.name
    description = each.value.description
    identity_store_id = var.identity_store.identity_store_ids[0]
}

# Entitlements

## Permission-set Entitlements (aka Group-PermissionSet-Account mapping)

locals {
    # Change this map from being keyed by filename to keyed by permission_set.name, which is more useful here.
    permission_set_map_by_name = {
        for permission_set in var.permission_sets :
            permission_set.permission_set.name => permission_set
    }

    # A map of account_sets, keyed by name.
    account_set_map = {
        for account_set in try( var.args.account_sets, [] ) :
            account_set.name => toset(account_set.accounts)
    }

    # Build a list of entitlements.
    entitlement_list = flatten([
        for role in var.args.roles : [
            for permission_set in try( role.permission_sets, [] ) : concat([
                for account_set in try( permission_set.account_sets, [] ) : [
                    for account_set_accounts in local.account_set_map[account_set] : {
                        team = var.args.team.name
                        role = role.name
                        account = account_set_accounts
                        permission_set = permission_set.name
                    }
                ]
            ],[
                for ou in try( permission_set.ous, [] ) : [
                    for ou_account in var.org_ou_account_map.descendant_accounts[ou].active : {
                        team = var.args.team.name
                        role = role.name
                        account = ou_account
                        permission_set = permission_set.name
                    }
                ]
            ])
        ]
    ])
    # Create a map of entitlements from the list, keyed by "team_role_account" to be unique.
    entitlement_map = {
        for entitlement in local.entitlement_list : "${entitlement.team}_${entitlement.role}_${entitlement.permission_set}_${entitlement.account}" => {
            group = "${entitlement.team}_${entitlement.role}"
            account = entitlement.account
            permission_set = entitlement.permission_set
        }
    }

}

resource "aws_ssoadmin_account_assignment" "entitlements" {
    for_each = local.entitlement_map
    instance_arn = var.identity_store.arns[0]
    permission_set_arn = local.permission_set_map_by_name[each.value.permission_set].permission_set.arn
    principal_id = aws_identitystore_group.groups[each.value.group].group_id # ID of the group created in this module and required for this entitlement.
    principal_type = "GROUP"
    target_id = var.aws_account_map[each.value.account] # The ID of the AWS account. Lookup the account id from the name in var.aws_account_map
    target_type = "AWS_ACCOUNT"
}

## Application Entitlements (aka Group-Application mapping)

locals {
    # A map of applications, keyed by name.
    application_map_by_name = {
        for application in var.applications : "${application.sso_application.name}" => application.sso_application
    }
    # Build a list of applications.
    application_list = flatten([
        for role in var.args.roles : [
            for application in try( role.applications, [] ) : {
                team = var.args.team.name
                role = role.name
                application_name = application
            }
        ]
    ])
    # Create a map of applications from the list, keyed by "team_role_application" to be unique.
    application_map = {
        for application in local.application_list : "${application.team}_${application.role}_${application.application_name}" => {
            group = "${application.team}_${application.role}"
            application_name = application.application_name
            application_arn = local.application_map_by_name[application.application_name].application_arn
        }
    }
}

resource "aws_ssoadmin_application_assignment" "application_assignments" {
  for_each = local.application_map
  principal_id = aws_identitystore_group.groups[each.value.group].group_id
  principal_type  = "GROUP"
  application_arn = each.value.application_arn
}
