import boto3
from functools import lru_cache


def get_boto3_session(profile_name: str = None, region_name: str = 'us-west-2') -> boto3.Session:
    """
    Return a boto3 Session, using the named profile if provided.
    """
    if profile_name:
        return boto3.Session(profile_name=profile_name, region_name=region_name)
    return boto3.Session(region_name=region_name)


def get_identity_store_id(sso_admin_client) -> str:
    """
    Fetch the Identity Store ID for your IAM Identity Center instance.
    """
    resp = sso_admin_client.list_instances()
    instances = resp.get('Instances', [])
    if not instances:
        raise RuntimeError("No IAM Identity Center instances found.")
    return instances[0]['IdentityStoreId']


@lru_cache(maxsize=None)
def find_group_id(idstore_client, identity_store_id: str, display_name: str) -> str:
    """
    Find a group's ID by display name.
    """
    paginator = idstore_client.get_paginator('list_groups')
    for page in paginator.paginate(IdentityStoreId=identity_store_id):
        for g in page.get('Groups', []):
            if g['DisplayName'] == display_name:
                return g['GroupId']
    raise ValueError(f"Group '{display_name}' not found.")


def list_group_memberships(idstore_client, identity_store_id: str, group_id: str):
    """
    Generator yielding (membership_id, user_id) for a given group.
    """
    paginator = idstore_client.get_paginator('list_group_memberships')
    for page in paginator.paginate(IdentityStoreId=identity_store_id, GroupId=group_id):
        for m in page.get('GroupMemberships', []):
            yield m['MembershipId'], m['MemberId']['UserId']
