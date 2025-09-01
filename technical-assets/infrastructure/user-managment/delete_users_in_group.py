"""
Delete Users in Group Script

WARNING: THIS IS A DESTRUCTIVE SCRIPT THAT PERMANENTLY DELETES USERS

This script removes all users from specified groups AND permanently deletes those users from
the AWS IAM Identity Center (SSO). This is different from delete_group.py which removes users 
from a group but does not delete the users themselves.

Use with extreme caution as user deletion cannot be undone.
"""

import sys
from botocore.exceptions import ClientError
from utils import get_boto3_session, get_identity_store_id, find_group_id, list_group_memberships


def delete_user(idstore_client, identity_store_id: str, user_id: str):
    """
    Delete a user from the identity store.
    """
    try:
        idstore_client.delete_user(
            IdentityStoreId=identity_store_id,
            UserId=user_id
        )
        print(f"- Deleted user {user_id}")
    except ClientError as e:
        print(
            f"❌ Failed to delete user {user_id}: {e.response['Error']['Message']}")


def remove_and_delete_all_users(idstore_client, identity_store_id: str, group_id: str):
    """
    Remove every membership in the group and delete each user.
    """
    for membership_id, user_id in list_group_memberships(idstore_client, identity_store_id, group_id):
        # remove membership
        try:
            idstore_client.delete_group_membership(
                IdentityStoreId=identity_store_id,
                MembershipId=membership_id
            )
            print(f"- Removed membership {membership_id} for user {user_id}")
        except ClientError as e:
            print(
                f"❌ Failed to remove membership {membership_id}: {e.response['Error']['Message']}")
        # delete the user
        delete_user(idstore_client, identity_store_id, user_id)


def delete_group(idstore_client, identity_store_id: str, group_id: str):
    """
    Delete the specified group.
    """
    try:
        idstore_client.delete_group(
            IdentityStoreId=identity_store_id,
            GroupId=group_id
        )
        print(f"- Deleted group {group_id}")
    except ClientError as e:
        print(
            f"❌ Failed to delete group {group_id}: {e.response['Error']['Message']}")


def main():
    """
    Main function that processes a single group - removes all members and permanently deletes them.
    CAUTION: This is a destructive operation that deletes users completely.
    """
    if len(sys.argv) < 2:
        print("⚠️  WARNING: THIS SCRIPT PERMANENTLY DELETES USERS ⚠️")
        print(
            "Usage: python delete_users_in_group.py <group_name> [aws_profile] [region]")
        sys.exit(1)

    group_name = sys.argv[1]
    profile = sys.argv[2] if len(sys.argv) > 2 else None
    region = sys.argv[3] if len(sys.argv) > 3 else 'us-west-2'

    session = get_boto3_session(profile, region)
    sso_admin = session.client('sso-admin')
    idstore = session.client('identitystore')
    store_id = get_identity_store_id(sso_admin)

    try:
        group_id = find_group_id(idstore, store_id, group_name)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)

    remove_and_delete_all_users(idstore, store_id, group_id)
    # delete_group(idstore, store_id, group_id)

def process_multiple_groups(group_names, profile="master", region="us-west-2"):
    """
    Loops through multiple group names, removes all members and PERMANENTLY DELETES those users.
    
    WARNING: This is a destructive operation that cannot be undone.
    - All users in the specified groups will be completely deleted from IAM Identity Center
    - The groups themselves will not be deleted (uncomment the delete_group call if needed)
    
    Args:
        group_names: List of group names to process
        profile: AWS profile to use
        region: AWS region to use (defaults to us-west-2)
    """
    session = get_boto3_session(profile, region)
    sso_admin = session.client('sso-admin')
    idstore = session.client('identitystore')
    store_id = get_identity_store_id(sso_admin)

    for group_name in group_names:
        print(f"\n🔍 Processing group: {group_name}")
        try:
            group_id = find_group_id(idstore, store_id, group_name)
            remove_and_delete_all_users(idstore, store_id, group_id)
            # delete_group(idstore, store_id, group_id)  # Uncomment if you want to delete the group itself
        except ValueError as e:
            print(f"❌ {e}")

if __name__ == '__main__':
    group_list = [
    "Hackathon1",
    "Hackathon2"
    ]

    process_multiple_groups(group_list)
