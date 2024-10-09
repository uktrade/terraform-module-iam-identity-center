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
