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
