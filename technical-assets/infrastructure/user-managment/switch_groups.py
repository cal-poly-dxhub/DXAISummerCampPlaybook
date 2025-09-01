import csv
import argparse
from utils import (
    get_boto3_session,
    get_identity_store_id,
    find_group_id,
    list_group_memberships,
)
import boto3


def parse_args():
    parser = argparse.ArgumentParser(description="Switch users between Identity Center groups.")
    parser.add_argument("csv_file", help="CSV with user email, From Group (optional), To Group")
    parser.add_argument("--profile", help="AWS profile name", default=None)
    parser.add_argument("--region", help="AWS region", default="us-west-2")
    return parser.parse_args()


def get_user_id(idstore_client, identity_store_id, email):
    response = idstore_client.get_user_id(
        IdentityStoreId=identity_store_id,
        AlternateIdentifier={
            "UniqueAttribute": {
                "AttributePath": "emails.value",
                "AttributeValue": email
            }
        }
    )
    return response["UserId"]


def remove_user_from_group(idstore_client, identity_store_id, user_id, group_id):
    for membership_id, member_user_id in list_group_memberships(idstore_client, identity_store_id, group_id):
        if member_user_id == user_id:
            idstore_client.delete_group_membership(
                IdentityStoreId=identity_store_id,
                MembershipId=membership_id
            )
            print(f"✅ Removed user {user_id} from group {group_id}")
            return
    print(f"⚠️ User {user_id} not found in group {group_id}")


def add_user_to_group(idstore_client, identity_store_id, user_id, group_id):
    idstore_client.create_group_membership(
        IdentityStoreId=identity_store_id,
        GroupId=group_id,
        MemberId={"UserId": user_id}
    )
    print(f"✅ Added user {user_id} to group {group_id}")


def get_user_account_assignments(sso_admin_client, instance_arn, user_id):
    """
    Get all (account_id, permission_set_arn) pairs assigned directly to the user.
    """
    assignments = []
    paginator = sso_admin_client.get_paginator("list_account_assignments_for_principal")
    for page in paginator.paginate(
        InstanceArn=instance_arn,
        PrincipalId=user_id,
        PrincipalType="USER"
    ):
        for a in page.get("AccountAssignments", []):
            assignments.append((a["AccountId"], a["PermissionSetArn"]))
    return assignments

def assign_user_to_group_accounts(sso_admin_client, instance_arn, user_id, group_id):
    """
    Assign user to all account/permission sets that the group currently has.
    """
    paginator = sso_admin_client.get_paginator("list_account_assignments_for_principal")
    for page in paginator.paginate(
        InstanceArn=instance_arn,
        PrincipalId=group_id,
        PrincipalType="GROUP"
    ):
        for assignment in page.get("AccountAssignments", []):
            try:
                sso_admin_client.create_account_assignment(
                    InstanceArn=instance_arn,
                    TargetId=assignment["AccountId"],
                    TargetType="AWS_ACCOUNT",
                    PermissionSetArn=assignment["PermissionSetArn"],
                    PrincipalType="USER",
                    PrincipalId=user_id
                )
                print(f"✅ Assigned user {user_id} access to account {assignment['AccountId']} with permission set {assignment['PermissionSetArn']}")
            except sso_admin_client.exceptions.ConflictException:
                print(f"⚠️ Assignment already exists for user {user_id} in account {assignment['AccountId']}")



def delete_user_account_assignments(sso_admin_client, instance_arn, user_id):
    assignments = get_user_account_assignments(sso_admin_client, instance_arn, user_id)
    for account_id, perm_set_arn in assignments:
        try:
            sso_admin_client.delete_account_assignment(
                InstanceArn=instance_arn,
                TargetId=account_id,
                TargetType="AWS_ACCOUNT",
                PermissionSetArn=perm_set_arn,
                PrincipalType="USER",
                PrincipalId=user_id
            )
            print(f"🧹 Revoked user {user_id} access to account {account_id} with permission set {perm_set_arn}")
        except sso_admin_client.exceptions.ResourceNotFoundException:
            pass  # Nothing to delete


def main():
    args = parse_args()
    session = get_boto3_session(args.profile, args.region)
    idstore_client = session.client("identitystore")
    sso_admin_client = session.client("sso-admin")

    identity_store_id = get_identity_store_id(sso_admin_client)
    instance_arn = sso_admin_client.list_instances()["Instances"][0]["InstanceArn"]

    with open(args.csv_file, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            email = row["Email"].strip()
            from_group = row["From Group"].strip() if row["From Group"] else None
            to_group = row["To Group"].strip()

            print(f"\n🔄 Processing user: {email}")
            try:
                user_id = get_user_id(idstore_client, identity_store_id, email)
            except Exception as e:
                print(f"❌ Failed to get user ID for {email}: {e}")
                continue

            try:
                to_group_id = find_group_id(idstore_client, identity_store_id, to_group)
            except Exception as e:
                print(f"❌ Failed to find To Group '{to_group}': {e}")
                continue

            if from_group:
                try:
                    from_group_id = find_group_id(idstore_client, identity_store_id, from_group)
                    delete_user_account_assignments(sso_admin_client, instance_arn, user_id)
                    remove_user_from_group(idstore_client, identity_store_id, user_id, from_group_id)
                except Exception as e:
                    print(f"⚠️ Skipping cleanup for from_group '{from_group}': {e}")

            try:
                add_user_to_group(idstore_client, identity_store_id, user_id, to_group_id)
                # Assign user to all accounts/permission sets of the target group
                assign_user_to_group_accounts(sso_admin_client, instance_arn, user_id, to_group_id)
            except Exception as e:
                print(f"❌ Failed to add user to group {to_group}: {e}")
                continue

            
if __name__ == "__main__":
    main()
