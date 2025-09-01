# S3 Document Uploader

This tool uploads team documents to their corresponding S3 buckets across multiple AWS accounts using named profiles.

## Overview

The script is designed to handle document uploading for multiple teams participating in the Summer Camp 2025. Each team has its own AWS account with a dedicated S3 bucket, and the script automates the process of creating buckets (if they don't exist) and uploading documents to them. This example handles 5 teams, but the approach can be easily expanded for more teams.

## Configuration Variables

Before running the script, you should review and modify these important variables at the top of the script:

| Variable        | Description                                       | Default Value                    | Recommended Action                                              |
| --------------- | ------------------------------------------------- | -------------------------------- | --------------------------------------------------------------- |
| `DATA_DIR`      | Local directory where all team folders are stored | `./Data`                         | Update to the actual path of your data directory                |
| `REGION`        | AWS region where S3 buckets will be created       | `us-west-2`                      | Change to your preferred region (e.g., `us-east-1`)             |
| `LOG_FILE`      | Path for the log file                             | `upload_results_[timestamp].log` | Leave as is or specify a fixed filename                         |
| `TOTAL_TEAMS`   | Number of teams to process                        | `5`                              | Update to match the number of teams in the `TEAM_FOLDERS` array |
| `BUCKET_PREFIX` | Prefix for all S3 bucket names                    | `ccc-summer-camp-2025`           | Change to a unique prefix for your project                      |

The S3 bucket names are automatically generated with the format:

```
[BUCKET_PREFIX]-[team-name-in-lowercase-with-hyphens]
```

For example, "Team A - Math Placement Tool" becomes `ccc-summer-camp-2025-team-a-math-placement-tool`

## Prerequisites

1. AWS CLI installed and configured with multiple profiles
2. Proper AWS credentials for each profile with S3 permissions
3. Team folders organized in a local directory structure

## AWS Profile Setup

The script requires AWS CLI profiles to be configured. Each team is mapped to a profile (profile1, profile2, etc.) in the `~/.aws/credentials` file:

```
[profile1]
aws_access_key_id = AKIAXXXXXXXXXXXXXXXX
aws_secret_access_key = XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
region = us-west-2

[profile2]
aws_access_key_id = AKIAXXXXXXXXXXXXXXXX
aws_secret_access_key = XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
region = us-west-2

[profile3]
aws_access_key_id = AKIAXXXXXXXXXXXXXXXX
aws_secret_access_key = XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
region = us-west-2

# ... and so on for profiles 4 and 5
```

## Directory Structure

The script expects a specific directory structure:

```
./Data/
  ├── Team A - Math Placement Tool/
  │   ├── file1.pdf
  │   └── file2.xlsx
  ├── Team B - Documentation Assistant/
  │   ├── report.docx
  │   └── data.csv
  ├── Team C - Training Module/
  │   └── ...
  └── ...
```

## Usage

1. Ensure AWS profiles are configured for all teams
2. Organize team documents in the appropriate folder structure
3. Update the script variables as needed:
   - Set `DATA_DIR` to your data directory path
   - Set `REGION` to your desired AWS region
   - Adjust `TEAM_FOLDERS` array to match your team names
   - Update the `get_profile()` function to map each team to the correct AWS profile
   - Ensure `TOTAL_TEAMS` matches the number of teams
4. Make the script executable and run it:

```bash
chmod +x upload_docs.sh
./upload_docs.sh
```

## Customization

### Adding More Teams

To add more teams, update these sections:

1. Add team names to the `get_profile()` function:

```bash
get_profile() {
    case "$1" in
        "Team A - Math Placement Tool") echo "profile1" ;;
        # Add more teams here...
        "Team F - New Project") echo "profile6" ;;
        *) echo "" ;;
    esac
}
```

2. Add team names to the `TEAM_FOLDERS` array:

```bash
TEAM_FOLDERS=(
  "Team A - Math Placement Tool"
  # Existing teams...
  "Team F - New Project"
)
```

3. Update the `TOTAL_TEAMS` variable to match the new total

### Changing Bucket Names

Modify the bucket naming format by editing this line in the script:

```bash
BUCKET_NAME="ccc-summer-camp-2025-$(echo "$TEAM_FOLDER" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-')"
```

## Features

- Automatically creates S3 buckets if they don't exist
- Maps team folders to their respective AWS accounts via profiles
- Comprehensive logging with timestamps
- Error handling for missing directories and upload failures
- Upload statistics summary

## Bucket Naming Convention

Buckets are named using the format: `[BUCKET_PREFIX]-[team-name-in-lowercase-with-hyphens]`

The default bucket prefix is `ccc-summer-camp-2025`, which makes bucket names like:

- `ccc-summer-camp-2025-team-a-math-placement-tool`
- `ccc-summer-camp-2025-team-b-documentation-assistant`

## Log Files

The script generates a timestamped log file (e.g., `upload_results_20250901_120000.log`) containing all output, including errors and upload statistics.

## Common Issues and Troubleshooting

### AWS Profile Issues

- **Error:** `No profile defined for [team name]`

  - **Solution:** Add the team name to the `get_profile()` function with the correct profile name

- **Error:** `The config profile [profile] could not be found`
  - **Solution:** Ensure the profile exists in your AWS configuration files

### Data Directory Issues

- **Error:** `Folder not found at [path]`
  - **Solution:** Verify that the `DATA_DIR` path is correct and the team folder exists

### Bucket Creation Issues

- **Error:** `Failed to create [bucket name]`
  - **Solution:** Check permissions for the AWS profile, or try a different bucket name
  - **Note:** S3 bucket names must be globally unique across all AWS accounts

### Permissions

- Make sure each AWS profile has permissions to:
  - Create S3 buckets
  - Put objects in S3 buckets
