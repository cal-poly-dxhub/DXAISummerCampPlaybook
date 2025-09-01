"""
Delete Group Script

This script removes all users from a specified group and then deletes the group itself.
IMPORTANT: This script does NOT delete the users themselves, only their membership in the group.

If you need to delete the users as well, use delete_users_in_group.py instead.
"""

import sys
from botocore.exceptions import ClientError
from utils import get_boto3_session, get_identity_store_id, find_group_id, list_group_memberships


def remove_all_users_from_group(idstore_client, identity_store_id: str, group_id: str):
    """
    Delete every membership in the specified group.
    """
    for membership_id, user_id in list_group_memberships(idstore_client, identity_store_id, group_id):
        try:
            idstore_client.delete_group_membership(
                IdentityStoreId=identity_store_id,
                MembershipId=membership_id
            )
            print(
                f"- Removed user {user_id} (membership {membership_id}) from group {group_id}")
        except ClientError as e:
            print(
                f"❌ Failed to remove membership {membership_id}: {e.response['Error']['Message']}")


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
    if len(sys.argv) < 2:
        print(
            "Usage: python delete_group.py <group_name> [aws_profile] [region]")
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

    remove_all_users_from_group(idstore, store_id, group_id)
    # Uncomment to delete the group itself
    delete_group(idstore, store_id, group_id)


if __name__ == '__main__':
    main()
