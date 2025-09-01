import sys
import csv
from botocore.exceptions import ClientError
from utils import get_boto3_session, get_identity_store_id, find_group_id


def create_user(idstore_client, identity_store_id: str,
                user_name: str, given_name: str, family_name: str,
                display_name: str, email: str) -> str:
    """
    Create a new user in the Identity Store; may raise ConflictException if email exists.
    """
    resp = idstore_client.create_user(
        IdentityStoreId=identity_store_id,
        UserName=user_name,
        Name={'GivenName': given_name, 'FamilyName': family_name},
        DisplayName=display_name,
        Emails=[{'Value': email.strip(), 'Type': 'work'}]
    )
    return resp['UserId']


def create_group(idstore_client, identity_store_id: str,
                 display_name: str, description: str = None) -> str:
    """
    Create a group in the Identity Store and return its GroupId.
    """
    params = {'IdentityStoreId': identity_store_id,
              'DisplayName': display_name}
    if description:
        params['Description'] = description
    resp = idstore_client.create_group(**params)
    return resp['GroupId']


def find_or_create_group(idstore_client, identity_store_id: str, display_name: str) -> str:
    """
    Return the GroupId for display_name, creating the group if missing.
    """
    try:
        return find_group_id(idstore_client, identity_store_id, display_name)
    except ValueError:
        gid = create_group(idstore_client, identity_store_id, display_name)
        print(f"⚠️  Auto-created group '{display_name}' → {gid}")
        return gid


def add_user_to_group(idstore_client, identity_store_id: str,
                      group_id: str, user_id: str) -> None:
    """
    Add a user to a group; may raise ConflictException if already a member.
    """
    idstore_client.create_group_membership(
        IdentityStoreId=identity_store_id,
        GroupId=group_id,
        MemberId={'UserId': user_id}
    )
    print(f"   • Added user {user_id} to group '{group_id}'")


def import_users_from_csv(csv_path: str, profile_name: str = None, region_name: str = 'us-west-2'):
    session = get_boto3_session(profile_name, region_name)
    sso_admin = session.client('sso-admin')
    idstore = session.client('identitystore')
    store_id = get_identity_store_id(sso_admin)
    creation_errors = []
    skipped_groups = []

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # reader = csv.DictReader(f, delimiter='\t')
        reader.fieldnames = [name.strip() for name in reader.fieldnames]
        for row in reader:
            row = {k.strip(): v for k, v in row.items()}
            # username = row['Username'].strip()
            given_name = row['First'].strip()
            family_name = row['Last'].strip()
            display_name = row.get(
                'Display Name', f"{given_name} {family_name}").strip()
            email = row['Email'].strip()
            username = email
            # group_name = row.get('Group', '').strip()
            group_name = row.get('Project_Theme', '').strip()

            # Attempt to create user, catch and report errors
            try:
                user_id = create_user(
                    idstore, store_id,
                    user_name=username,
                    given_name=given_name,
                    family_name=family_name,
                    display_name=display_name,
                    email=email
                )
                print(f"✓ Created user {username} → {user_id}")
            except ClientError as e:
                err_msg = e.response.get('Error', {}).get('Message', str(e))
                print(f"❌ Error creating user '{email}': {err_msg}")
                creation_errors.append((email, err_msg))
                # Skip group membership for this user
                continue

            # Handle group membership, catch group conflicts
            if group_name:
                grp_id = find_or_create_group(idstore, store_id, group_name)
                try:
                    add_user_to_group(idstore, store_id, grp_id, user_id)
                except ClientError as e:
                    err_msg = e.response.get(
                        'Error', {}).get('Message', str(e))
                    print(
                        f"ℹ️  Could not add '{email}' to '{group_name}': {err_msg}")
                    skipped_groups.append((email, err_msg))

    # Summaries
    if creation_errors:
        print("\nSummary of user creation errors:")
        for email, msg in creation_errors:
            print(f" - {email}: {msg}")

    if skipped_groups:
        print("\nSummary of users not added to groups:")
        for email, msg in skipped_groups:
            print(f" - {email}: {msg}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python add_users.py <csv_path> [aws_profile] [region]")
        sys.exit(1)
    csv_path = sys.argv[1]
    profile = sys.argv[2] if len(sys.argv) > 2 else None
    region = sys.argv[3] if len(sys.argv) > 3 else 'us-west-2'
    import_users_from_csv(csv_path, profile, region)
