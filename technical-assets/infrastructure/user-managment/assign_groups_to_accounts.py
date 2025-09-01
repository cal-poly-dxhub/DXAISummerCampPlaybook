import csv
import argparse
from utils import get_boto3_session, get_identity_store_id, find_group_id
import boto3


def parse_args():
    parser = argparse.ArgumentParser(description="Assign groups to accounts using names and permission sets.")
    parser.add_argument("csv_file", help="CSV with GroupName,AccountName,PermissionSetName")
    parser.add_argument("--profile", help="AWS profile name", default=None)
    parser.add_argument("--region", help="AWS region", default="us-west-2")
    return parser.parse_args()


def get_permission_set_arn(sso_admin_client, instance_arn, name):
    paginator = sso_admin_client.get_paginator("list_permission_sets")
    for page in paginator.paginate(InstanceArn=instance_arn):
        for ps_arn in page["PermissionSets"]:
            desc = sso_admin_client.describe_permission_set(
                InstanceArn=instance_arn,
                PermissionSetArn=ps_arn
            )
            if desc["PermissionSet"]["Name"] == name:
                return ps_arn
    raise ValueError(f"Permission set '{name}' not found.")


def get_account_name_to_id_map(org_client):
    """
    Build a map of account names to account IDs from AWS Organizations.
    """
    account_map = {}
    paginator = org_client.get_paginator("list_accounts")
    for page in paginator.paginate():
        for acct in page["Accounts"]:
            account_map[acct["Name"]] = acct["Id"]
    return account_map


def assign_group_to_account(sso_admin_client, instance_arn, account_id, permission_set_arn, group_id):
    try:
        sso_admin_client.create_account_assignment(
            InstanceArn=instance_arn,
            TargetId=account_id,
            TargetType="AWS_ACCOUNT",
            PermissionSetArn=permission_set_arn,
            PrincipalType="GROUP",
            PrincipalId=group_id
        )
        print(f"✅ Assigned group {group_id} to account {account_id} with permission set {permission_set_arn}")
    except sso_admin_client.exceptions.ConflictException:
        print(f"⚠️ Assignment already exists for group {group_id} in account {account_id}")


def main():
    args = parse_args()
    session = get_boto3_session(args.profile, args.region)
    idstore_client = session.client("identitystore")
    sso_admin_client = session.client("sso-admin")
    org_client = session.client("organizations")

    identity_store_id = get_identity_store_id(sso_admin_client)
    instance_arn = sso_admin_client.list_instances()["Instances"][0]["InstanceArn"]
    account_name_to_id = get_account_name_to_id_map(org_client)

    with open(args.csv_file, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            group_name = row["GroupName"].strip()
            account_name = row["AccountName"].strip()
            permission_set_name = row["PermissionSetName"].strip()

            try:
                group_id = find_group_id(idstore_client, identity_store_id, group_name)

                account_id = account_name_to_id.get(account_name)
                if not account_id:
                    print(f"❌ Account '{account_name}' not found in your AWS Organization.")
                    continue

                permission_set_arn = get_permission_set_arn(sso_admin_client, instance_arn, permission_set_name)
                assign_group_to_account(sso_admin_client, instance_arn, account_id, permission_set_arn, group_id)
            except Exception as e:
                print(f"❌ Failed to assign group {group_name} to account '{account_name}': {e}")


if __name__ == "__main__":
    main()
