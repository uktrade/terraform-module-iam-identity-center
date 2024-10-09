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

