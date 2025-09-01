# AWS IAM Identity Center User Management

This directory contains Python scripts for managing users and groups in AWS IAM Identity Center (formerly AWS SSO). These utilities help with bulk user management operations, such as adding users, assigning groups to AWS accounts, moving users between groups, and removing users or groups.

## Prerequisites

- Python 3.6+
- AWS CLI configured with appropriate permissions
- Required Python packages:
  - boto3
  - botocore

## Script Files Overview

### 1. add_users.py

Creates new users in IAM Identity Center from a CSV file and optionally assigns them to groups.

**Usage:**
```bash
python add_users.py <csv_path> [aws_profile] [region]
```

**CSV Format Example:**
See [Add_Users_Ex.csv](./Add_Users_Ex.csv) for the format, which includes:
- First name
- Last name
- Email
- Display Name
- Group (optional)

### 2. assign_groups_to_accounts.py

Assigns IAM Identity Center groups to AWS accounts with specific permission sets.

**Usage:**
```bash
python assign_groups_to_accounts.py <csv_file> [--profile PROFILE] [--region REGION]
```

**CSV Format Example:**
See [Assign_Group_Ex.csv](./Assign_Group_Ex.csv) for the format, which includes:
- GroupName
- AccountName
- PermissionSetName

### 3. switch_groups.py

Moves users from one group to another, or adds users to a new group without removing them from existing groups. Also handles the necessary permission updates.

**Key Features:**
- If "From Group" is specified, the user is removed from that group and added to the "To Group"
- If "From Group" is left empty, the user is simply added to the "To Group" without being removed from any existing groups
- Automatically assigns the appropriate AWS account permissions

**Usage:**
```bash
python switch_groups.py <csv_file> [--profile PROFILE] [--region REGION]
```

**CSV Format Example:**
See [Switch_Group_Ex.csv](./Switch_Group_Ex.csv) for the format, which includes:
- Email
- From Group (optional) - Leave blank to add to a new group without removing from existing groups
- To Group

### 4. delete_group.py

Removes all users from a group and deletes the group itself. This script does NOT delete the users themselves, only their membership in the group.

**Usage:**
```bash
python delete_group.py <group_name> [aws_profile] [region]
```

### 5. delete_users_in_group.py

⚠️ **WARNING: DESTRUCTIVE OPERATION** ⚠️

This script removes users from specified groups AND PERMANENTLY DELETES those users from the IAM Identity Center. This is a destructive operation that cannot be undone.

Key differences from delete_group.py:
- delete_group.py: Removes users from a group but preserves the users
- delete_users_in_group.py: Removes AND permanently deletes the users

**Usage:**
```bash
python delete_users_in_group.py <group_name> [aws_profile] [region]
```

This script also includes a `process_multiple_groups` function that can handle bulk operations across multiple groups.

## CSV File Examples

The repository includes example CSV files for the different operations:

- **Add_Users_Ex.csv** - Template for adding users
- **Assign_Group_Ex.csv** - Template for assigning groups to accounts
- **Switch_Group_Ex.csv** - Template for moving users between groups

## Important Notes

1. All scripts utilize a common `utils.py` file that contains shared AWS IAM Identity Center utility functions. This file seems to be missing from the repository, but is required for the scripts to function.

2. Make sure you have the necessary AWS permissions to perform these operations.

3. Always test in a non-production environment first, especially when using the deletion scripts.

4. The region defaults to 'us-west-2' if not specified.

## Common Functions

The scripts share several utility functions for:

- Getting AWS boto3 sessions
- Getting Identity Store IDs
- Finding group IDs
- Listing group memberships
- Creating and managing users and groups

## Best Practices

- Always back up your IAM Identity Center configuration before bulk operations
- Review the CSV files carefully before running the scripts
- Consider running with limited scope first to verify behavior
