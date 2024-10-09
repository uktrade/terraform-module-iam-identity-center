import boto3
import sys
import os
import logging

# Logging
logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
logger.setLevel(logging.INFO)
log = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(message)s')
log.setFormatter(formatter)
logger.addHandler(log)

# Boto3 initialisation
## Session
boto3_session = boto3.Session(profile_name=os.environ['AWS_PROFILE'])
## Identity Centre Client
idc_client = boto3_session.client('identitystore')
## SSO Client
sso_client = boto3_session.client('sso-admin')
client_sso_instance = sso_client.list_instances()["Instances"][0]
logger.debug(f"client_sso_instance: {client_sso_instance}")
## AWS ORganisation Client
org_client = boto3_session.client('organizations')


def get_permission_sets():
    permission_sets = []
    next_token = ""
    while True:
        client_permission_sets = sso_client.list_permission_sets(
            InstanceArn = client_sso_instance["InstanceArn"],
            MaxResults=100,
            NextToken=next_token
        )
        logger.debug(f"client_permission_sets: {client_permission_sets}")
        permission_sets.extend(client_permission_sets["PermissionSets"])
        if "NextToken" in client_permission_sets:
            next_token=client_permission_sets["NextToken"]
            logger.debug(f"next_token: {next_token}")
        else:
            logger.debug(f"permission_sets: {permission_sets}")
            break
    return permission_sets

def get_provisioned_permission_sets(account_id):
    provisioned_permission_sets = []
    next_token = ""
    while True:
        client_provisioned_permission_sets = sso_client.list_permission_sets_provisioned_to_account(
            AccountId=account_id,
            InstanceArn=client_sso_instance["InstanceArn"],
            MaxResults=100,
            NextToken=next_token
            # ProvisioningStatus='LATEST_PERMISSION_SET_PROVISIONED'|'LATEST_PERMISSION_SET_NOT_PROVISIONED'
        )
        logger.debug(f"client_provisioned_permission_sets: {client_provisioned_permission_sets}")
        provisioned_permission_sets.extend(client_provisioned_permission_sets["PermissionSets"])
        if "NextToken" in client_provisioned_permission_sets:
            next_token=client_provisioned_permission_sets["NextToken"]
            logger.debug(f"next_token: {next_token}")
        else:
            logger.debug(f"provisioned_permission_sets: {provisioned_permission_sets}")
            break
    return provisioned_permission_sets

def get_permission_set_property(PermissionSetArn,property):
    permission_set = sso_client.describe_permission_set(
        InstanceArn = client_sso_instance["InstanceArn"],
        PermissionSetArn=PermissionSetArn
    )
    logger.debug(f"permission_set: {permission_set}")
    return permission_set['PermissionSet'][property]


def get_accounts():
    account_dict = {}
    accounts = org_client.list_accounts(MaxResults=20)
    while True:
        for account in accounts['Accounts']:
            account_dict[account['Id']]=account['Name']
        if "NextToken" in accounts:
            accounts = org_client.list_accounts(MaxResults=20,NextToken=accounts["NextToken"])
        else:
            break
    return account_dict

def get_account_property(AccountId,property):
    account = org_client.describe_account(
        AccountId=AccountId
    )
    logger.debug(f"account: {account}")
    return account['Account'][property]

def get_account_assignments(permission_set, account_id):
    account_assignments = []
    next_token = ""
    while True:
        client_account_assignments = sso_client.list_account_assignments(
            AccountId = account_id,
            InstanceArn = client_sso_instance["InstanceArn"],
            MaxResults=100,
            NextToken=next_token,
            PermissionSetArn = permission_set
        )
        logger.debug(f"client_account_assignments: {client_account_assignments}")
        account_assignments.extend(client_account_assignments["AccountAssignments"])
        if "NextToken" in client_account_assignments:
            next_token=client_account_assignments["NextToken"]
            logger.debug(f"next_token: {next_token}")
        else:
            logger.debug(f"account_assignments: {account_assignments}")
            break
    return account_assignments

def get_account_assignments_for_principal(principal_id, principal_type):
    account_assignments = []
    client_account_assignments_for_principal = sso_client.list_account_assignments_for_principal(
        InstanceArn = client_sso_instance["InstanceArn"],
        MaxResults=100,
        PrincipalId=principal_id,
        PrincipalType=principal_type
    )
    logger.debug(f"client_account_assignments_for_principal: {client_account_assignments_for_principal}")
    while True:
        account_assignments.extend(client_account_assignments_for_principal["AccountAssignments"])
        if "NextToken" in client_account_assignments_for_principal:
            client_account_assignments_for_principal = sso_client.list_account_assignments_for_principal(
                InstanceArn = client_sso_instance["InstanceArn"],
                MaxResults=100,
                NextToken=client_account_assignments_for_principal["NextToken"],
                PrincipalId=principal_id,
                PrincipalType=principal_type
            )
            logger.debug(f"client_account_assignments_for_principal: {client_account_assignments_for_principal}")
        else:
            logger.debug(f"account_assignments: {account_assignments}")
            break
    return account_assignments

def get_permission_set_accounts(permission_set):
    logger.debug(f"permission_set: {permission_set}")
    accounts = []
    next_token = ""
    while True:
        permission_set_accounts = sso_client.list_accounts_for_provisioned_permission_set(
            InstanceArn=client_sso_instance["InstanceArn"],
            MaxResults=100,
            NextToken=next_token,
            PermissionSetArn=permission_set
            # ProvisioningStatus='LATEST_PERMISSION_SET_PROVISIONED'|'LATEST_PERMISSION_SET_NOT_PROVISIONED'
        )
        accounts.extend(permission_set_accounts["AccountIds"])
        if "NextToken" in permission_set_accounts:
            next_token=permission_set_accounts["NextToken"]
        else:
            return accounts


def get_principal(PrincipalId, PrincipalType):
    logger.debug(f"PrincipalId, PrincipalType: {PrincipalId},{PrincipalType}")
    principal={}
    if PrincipalType == "GROUP":
        principal_group = idc_client.describe_group(
            IdentityStoreId=client_sso_instance["IdentityStoreId"],
            GroupId=PrincipalId
        )
        logger.debug(f"principal_group: {principal_group}")
        if "Description" not in principal_group:
            principal_group["Description"]=""
        principal["PrincipalId"]=principal_group["GroupId"]
        principal["DisplayName"]=principal_group["DisplayName"]
        principal["Description"]=principal_group["Description"]
    elif PrincipalType == "USER":
        try:
            principal_user = idc_client.describe_user(
                IdentityStoreId=client_sso_instance["IdentityStoreId"],
                UserId=PrincipalId
            )
            logger.debug(f"principal_user: {principal_user}")
            principal["PrincipalId"]=principal_user["UserId"]
            principal["DisplayName"]=principal_user["DisplayName"]
            principal["Description"]=principal_user["UserName"]
        except idc_client.exceptions.ResourceNotFoundException:
            principal["PrincipalId"]=PrincipalId
            principal["DisplayName"]=PrincipalType
            principal["Description"]="NOT FOUND"
    logger.debug(f"principal: {principal}")
    return principal

def get_groups():
    group_list = []
    groups = idc_client.list_groups(
        IdentityStoreId=client_sso_instance["IdentityStoreId"],
        MaxResults=100
    )
    logger.debug(f"groups: {groups}")
    while True:
        group_list.extend(groups["Groups"])
        if "NextToken" in groups:
            groups = idc_client.list_groups(
                IdentityStoreId=client_sso_instance["IdentityStoreId"],
                MaxResults=100,
                NextToken=groups["NextToken"]
            )
        else:
            return group_list

def get_group_property(GroupId,property):
    group = idc_client.describe_group(
        IdentityStoreId=client_sso_instance["IdentityStoreId"],
        GroupId=GroupId
    )
    logger.debug(f"group: {group}")
    return group[property]

def get_user_groups(user_id):
    group_list = []
    groups = idc_client.list_group_memberships_for_member(
        IdentityStoreId=client_sso_instance["IdentityStoreId"],
        MemberId={'UserId':user_id},
        MaxResults=100
    )
    logger.debug(f"groups: {groups}")
    logger.debug(f"GroupMemberships: {groups['GroupMemberships']}")
    while True:
        group_list.extend(groups["GroupMemberships"])
        if "NextToken" in groups:
            groups = idc_client.list_group_memberships_for_member(
                IdentityStoreId=client_sso_instance["IdentityStoreId"],
                MemberId={'UserId':user_id},
                MaxResults=100,
                NextToken=groups["NextToken"]
            )
        else:
            return group_list

def get_group_members(groupid):
    logger.debug(f"groupid: {groupid}")
    members = []
    group_memberships = idc_client.list_group_memberships(
        IdentityStoreId=client_sso_instance["IdentityStoreId"],
        GroupId=groupid,
        MaxResults=100
    )
    logger.debug(f"group_memberships: {group_memberships}")
    while True:
        members.extend(group_memberships["GroupMemberships"])
        if "NextToken" in group_memberships:
            group_memberships = idc_client.list_group_memberships(
                IdentityStoreId=client_sso_instance["IdentityStoreId"],
                GroupId=groupid,
                MaxResults=100,
                NextToken=group_memberships["NextToken"]
            )
            logger.debug(f"group_memberships: {group_memberships}")
        else:
            break
    return members

def get_user_property(userid,property):
    logger.debug(f"userid, property: {userid},{property}")
    user = idc_client.describe_user(
        IdentityStoreId=client_sso_instance["IdentityStoreId"],
        UserId=userid
    )
    logger.debug(f"user: {user}")
    return user[property]

def get_user_id(AttributePath,AttributeValue):
    logger.debug(f"AttributePath: {AttributePath}")
    logger.debug(f"AttributeValue: {AttributeValue}")
    user = idc_client.list_users(
        IdentityStoreId=client_sso_instance["IdentityStoreId"],
        Filters=[{
            'AttributePath': AttributePath,
            'AttributeValue': AttributeValue
        }]
    )
    logger.debug(f"user: {user}")
    if len(user["Users"])==0:
        raise Exception("User or UserId not found.")
    return user["Users"][0]["UserId"]


# Constants
AWS_ACCOUNTS=get_accounts() # Used to cache account IDs to Names and avoid repeated API calls since we reference this a lot.


if __name__ == "__main__":

    args=sys.argv
    logger.debug(f"args: {args}")
    if len(args)<2:
        print_help()

    f = open("idc_helper.csv", "w")

    if args[1].lower()=="get-group-members":
        f.write('group_name,user_name\n')
        groups=get_groups()
        logger.debug(f"groups: {groups}")
        for group in groups:
            logger.debug(f"group: {group}")
            group_members=get_group_members(group["GroupId"])
            logger.debug(f"group_members: {group_members}")
            for group_member in group_members:
                logger.debug(f"group_member: {group_member}")
                user=get_user_property(group_member["MemberId"]["UserId"],"UserName")
                output=f"{group['DisplayName']},{user}"
                logger.info(output)
                f.write(output+"\n")

    elif args[1].lower()=="get-entitlements":
        f.write('account_id,account_name,permission_set_name,principal_type,principal_name,principal_description\n')
        permission_sets=get_permission_sets()
        logger.debug(f"permission_sets: {permission_sets}")
        for permission_set in permission_sets:
            logger.info(f"permission_set: {permission_set}")
            permission_set_name=get_permission_set_property(permission_set,'Name')
            logger.debug(f"permission_set_name: {permission_set_name}")
            permission_set_accounts=get_permission_set_accounts(permission_set)
            logger.debug(f"permission_set_accounts: {permission_set_accounts}")
            logger.info(f"Permission set in {len(permission_set_accounts)} accounts.")
            for permission_set_account in permission_set_accounts:
                logger.debug(f"permission_set, permission_set_account: {permission_set},{permission_set_account}")
                account_name=AWS_ACCOUNTS[permission_set_account]
                account_assignments=get_account_assignments(permission_set,permission_set_account)
                logger.debug(f"account_assignments: {account_assignments}")
                for account_assignment in account_assignments:
                    logger.debug(f"account_assignment: {account_assignment}")
                    principal = get_principal(
                        account_assignment["PrincipalId"],
                        account_assignment["PrincipalType"],
                    )
                    logger.debug(f"principal: {principal}")
                    if "Description" not in principal:
                        principal["Description"]=""
                    output=f"{permission_set_account},{account_name},{permission_set_name},{account_assignment['PrincipalType']},{principal['DisplayName']},{principal['Description']}"
                    logger.info(output)
                    f.write(output+'\n')

    elif args[1].lower()=="get-users-for-accounts":
        f.write('account_id,account_name,permission_set_name,principal_type,group_name,user_name,user_display_name\n')
        account_names=args[2].split(",")
        logger.debug(f"account_names: {account_names}")
        for account_name in account_names:
            logger.info(f"account_name: {account_name}")
            account_id=list(AWS_ACCOUNTS.keys())[list(AWS_ACCOUNTS.values()).index(account_name)] # Look up the Accounta dictionary in reverse to get the ID from the name.
            logger.info(f"account_id: {account_id}")
            provisioned_permission_sets=get_provisioned_permission_sets(account_id)
            logger.debug(f"provisioned_permission_sets: {provisioned_permission_sets}")
            for provisioned_permission_set in provisioned_permission_sets:
                assignments=get_account_assignments(provisioned_permission_set,account_id)
                logger.debug(f"assignments: {assignments}")
                for assignment in assignments:
                    logger.debug(f"PrincipalId: {assignment['PrincipalId']}")
                    logger.info(f"PrincipalType: {assignment['PrincipalType']}")
                    principal=get_principal(assignment['PrincipalId'], assignment['PrincipalType'])
                    logger.info(f"principal: {principal['DisplayName']}")
                    permission_set_name=get_permission_set_property(provisioned_permission_set,'Name')
                    logger.info(f"permission_set_name: {permission_set_name}")
                    if assignment['PrincipalType']=="GROUP":
                        group_members=get_group_members(assignment['PrincipalId'])
                        logger.debug(f"group_members: {group_members}")
                        for group_member in group_members:
                            logger.debug(f"group_member: {group_member}")
                            logger.debug(f"UserId: {group_member['MemberId']['UserId']}")
                            group_member_details=get_principal(group_member['MemberId']['UserId'], "USER")
                            logger.debug(f"group_member_details: {group_member_details}")
                            output=f"{account_id},{account_name},{permission_set_name},{assignment['PrincipalType']},{principal['DisplayName']},{group_member_details['Description']},{group_member_details['DisplayName']}"
                            logger.info(output)
                            f.write(output+'\n')
                    elif assignment['PrincipalType']== "USER":
                        user_details=get_principal(assignment['PrincipalId'], "USER")
                        logger.debug(f"user_details: {user_details}")
                        output=f"{account_id},{account_name},{permission_set_name},{assignment['PrincipalType']},N/A,{user_details['Description']},{user_details['DisplayName']}"
                        logger.info(output)
                        f.write(output+'\n')

    f.close()
