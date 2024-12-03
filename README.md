# AWS Identity Center Terraform Modules

## Concept

This repo contains modules to deploy the following Identity Centre resources for AWS Account permissions:
- Groups
- Permission Sets
- "**Entitlements**" (which are the relationship of a Group to an Account with a Permission Set)

Also, the following Identity Centre resources for Applications:
- SSO Applications
- "Application **Entitlements**" (which are the relationship of a Group to an Application)

The **Entitlement** principle and the role of these Terraform modules are shown here:  
![IDC Terraform](<docs/IDC Terraform.svg>)

This shows how the code performs the following functions:
- Groups:
  - Creates groups in Identity Centre.
- Then for Permission Sets:
  - Creates permission-sets in Identity Centre.
    - Also creates in-line policies in a permission-set.
    - And can also add AWS-managed or existing customer-managed IAM policies to a permission-set.
  - Creates an "**Entitlement**" which essentially states: "**This Group** can access **this AWS Account** with **this Permission Set**"
- And for Applications:
  - Creates applications in Identity Centre (AWS API functionality here is quite basic - [see this note](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ssoadmin_application) and the [Applications](#applications) section below).
  - Creates an "**Application Entitlement**" which states: "**This Group** can access **this Application**"

The diagram also shows where the IDP fits in (in this case handling user / group membership via SCIM rather than these Terraform modules).


## Usage

### Permission Sets

**Permission Sets should, as far as possible, describe the collection of permissions.**  
It's often best to avoid using group names, AWS account details or role specific details here - since that makes the permission-set tricker to reuse (between Accounts and Groups). Also, it's good to avoid specific service-names such as "ec2_read_only" - since that makes the permission-set more difficult to extend without compromising the naming.  
The permission-set is what the AWS user will see in the logon console (and their `.aws` config file) - so it has to be meaningful from that perspective.

An example of permission-set object structure is:
```YAML
---
name: <PERMISSION-SET-NAME>
description: <PERMISSION-SET-DESC>
aws_managed_policies:
  - name: <AWS-POLICY-1>
  - name: <AWS-POLICY-2>
  ***.etc.***
external_customer_managed_policies:
  - name: <CUSTOMER-POLICY-1>
  - name: <CUSTOMER-POLICY-2>
  ***.etc.***
inline_policy:
  Version: "2012-10-17"
  Statement:
    - Sid: <SID-1>
      Action:
        - <SERVICE-1>:<PERMISSION-1>
        - <SERVICE-1>:<PERMISSION-2>
        - <SERVICE-2>:<PERMISSION-1>
      Effect: <EFFECT>
      Resource: <RESOURCE>
      Condition: <CONDITION>
    - Sid: <SID-2>
      ***.etc.***
    ***.etc.***
...
```

### Groups
**Groups should, as far as possible, describe the collection of users.**  
Try to avoid names that describe the permissions or AWS accounts - since that makes it difficult to alter the permissions or add further "entitlements" without compromising the group name.  
Group names are made up of 2 elements: the `team.name` and the `role.name`(s) (see YAML below). A 'team' can have multiple 'roles', each with its own set of permissions (note that 'roles' here are not IAM Roles - this refers to the second element of the resulting group names: "`team1`\_`role1`", "`team1`\_`role2`", etc.).  

**This is where "Entitlements" are defined.** A combination of **team_role**(s) (i.e. a Group Name) with **permission-sets** with **accounts** (or OUs or account-sets i.e. custom lists of accounts - see below) create **"Entitlements"**. Each entitlement is unique - and if groups have multiple permission-sets or the permission has a defined OU or account-set (see below) with multiple accounts - each of these is one entitlement. I.e. **each entitlement** is **one group** with **one permission-set** with **one account**.  
Note that **`account-sets`** are a made-up concept here - and are just a custom list / collection of accounts. Account-sets don't exist in AWS (though Org OUs are similar).  

Group object structure is:
```YAML
---
team:
  name: <TEAM-NAME>
roles:
  - name: <ROLE-1-NAME>
    description: <ROLE-1-DESC>
    permission_sets:
      - name: <PERMISSION-SET-1-NAME>
        account_sets:
          - <ACCOUNT-SET-NAME>
        ous:
          - <OU-1-NAME>
          - <OU-2-NAME>
          ***.etc.***
      - name: <PERMISSION-SET-2-NAME>
        ***.etc.***
    applications:
      - <APP-NAME-1>
      - <APP-NAME-2>
  - name: <ROLE-2-NAME>
    ***.etc.***
  account_sets:
  - name: <ACCOUNT-SET-1-NAME>
    accounts:
      - <AWS-ACCOUNT-1>
      - <AWS-ACCOUNT-2>
      ***.etc.***
  - name: <ACCOUNT-SET-2-NAME>
    accounts:
      - <AWS-ACCOUNT-3>
      - <AWS-ACCOUNT-4>
      ***.etc.***
...
```

### Applications
This module creates applications that are accessed via AWS SSO. For further application provider information, refer to the [AWS documentation](https://docs.aws.amazon.com/singlesignon/latest/userguide/manage-your-applications.html) for more details. The [aws sso-admin create-application](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/sso-admin/create-application.html) command documentation is also quite useful.  
Note also that the [aws_ssoadmin_application](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ssoadmin_application) Terraform registry docs state _"The CreateApplication API only supports custom OAuth 2.0 applications."_, so for other application types, create them in the console and [import into Terraform](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/ssoadmin_application#import) to use with Groups.

An custom SAML application config structure is:
```YAML
---
name: <APP-NAME>
application_provider_arn: arn:aws:sso::aws:applicationProvider/<PROVIDER>
description: <APP-DESCRIPTION>
status: ENABLED
portal_options:
  - sign_in_options:
      - application_url: <APP-URL>
        origin: APPLICATION
    visibility: ENABLED
...
```

### Organisations
The Organisation module provides organisation / OU data. Further detail and an example is provided in the module [README](org/README.md).

For example, calling the 'org' module...
```HCL
module "org" {
  source = "github.com/uktrade/terraform-module-iam-identity-center//org"
}
```
...allows the `module.org.org_ou_account_map` output to then be used in the Group module, so OU names can be used in group definitions.
```HCL
module "group" {
  source             = "github.com/uktrade/terraform-module-iam-identity-center//group"
  identity_store     = data.aws_ssoadmin_instances.sso
  permission_sets    = module.permission_sets
  applications       = module.applications
  org_ou_account_map = module.org.org_ou_account_map
}
```
**Note**: This module does not create OUs.

### Scripts
#### idc_helper.py ####
This script provides some information that's difficult to get from the IDC UI (without a lot of clicking). Each command also writes the results to a CSV for further analysis.

The functions are:
- `list-entitlements` - This option fully expands all 'Entitlements' (accounts, permission-sets, users / groups).
- `list-group-members` - This provides a list of all groups and the group members.
- `get-groups-for-account [ACCOUNT]` - Lists all groups that can access the account (and the permission-sets).
- `get-accounts-for-group [GROUP]` - Lists all accounts that can be accessed by members of the group (and the permission-sets).
- `get-permissions-for-user [USER]` - Lists all accounts a user can access (with permission-set) and whether direct or via a group.
- `get-users-for-accounts [ACCOUNT1,ACCOUNT2,ACCOUNTn]` - Shows all users who can access the accounts, and via group or direct access. Can provide a comma-separated list of accounts to examine.

## References
- Identity Centre quotas in AWS are quite low and cannot be increased much. Please refer to [this AWS documentation](https://docs.aws.amazon.com/singlesignon/latest/userguide/limits.html) for current limits.
- AWS documentation referencing [AWS SSO Applications](https://docs.aws.amazon.com/singlesignon/latest/userguide/manage-your-applications.html)
