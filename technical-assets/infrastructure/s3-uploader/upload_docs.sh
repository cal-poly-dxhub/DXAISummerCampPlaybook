#!/bin/bash

# S3 Document Uploader for Summer Camp 2025
# This script uploads team documents to their corresponding S3 buckets
# across multiple AWS accounts using named profiles

# Configuration variables
DATA_DIR="./Data"                              # Path to folder containing team data
REGION="us-west-2"                            # AWS region for bucket creation
BUCKET_PREFIX="ccc-summer-camp-2025"          # Prefix for all bucket names
LOG_FILE="upload_results_$(date +%Y%m%d_%H%M%S).log"  # Log file path

# Statistics
TOTAL_TEAMS=5                                 # Must match the number of teams in TEAM_FOLDERS
PROCESSED=0
SUCCESSFUL=0
FAILED=0


# Enable logging
exec > >(tee -a "$LOG_FILE") 2>&1
echo "Starting document upload at $(date)"
echo "----------------------------------------"

# Map folder name → AWS CLI profile
get_profile() {
    case "$1" in
        "Team A - Math Placement Tool") echo "profile1" ;;
        "Team B - Documentation Assistant") echo "profile2" ;;
        "Team C - Training Module") echo "profile3" ;;
        "Team D - Financial Analysis") echo "profile4" ;;
        "Team E - Data Insights") echo "profile5" ;;
        # Additional teams would be mapped here in a real deployment
        *) echo "" ;;
    esac
}



TEAM_FOLDERS=(
  "Team A - Math Placement Tool"
  "Team B - Documentation Assistant"
  "Team C - Training Module"
  "Team D - Financial Analysis"
  "Team E - Data Insights"
)

for TEAM_FOLDER in "${TEAM_FOLDERS[@]}"; do
  echo "Processing: $TEAM_FOLDER"
  PROCESSED=$((PROCESSED + 1))
  
  PROFILE=$(get_profile "$TEAM_FOLDER")
  if [ -z "$PROFILE" ]; then
    echo "  ERROR: No profile defined for '$TEAM_FOLDER'"
    FAILED=$((FAILED + 1))
    continue
  fi

  LOCAL_PATH="$DATA_DIR/$TEAM_FOLDER"
  if [ ! -d "$LOCAL_PATH" ]; then
    echo "  ERROR: Folder not found at '$LOCAL_PATH'"
    FAILED=$((FAILED + 1))
    continue
  fi
  
  # Get file count for reporting
  FILE_COUNT=$(find "$LOCAL_PATH" -type f | wc -l | xargs)
  echo "  Found $FILE_COUNT files to upload"
  
  BUCKET_NAME="$BUCKET_PREFIX-$(echo "$TEAM_FOLDER" | tr '[:upper:]' '[:lower:]' | tr ' ' '-' | tr -cd 'a-z0-9-')"
  echo "  Target bucket: $BUCKET_NAME"
  
  # Create bucket if needed
  aws s3api head-bucket --bucket "$BUCKET_NAME" --profile "$PROFILE" 2>/dev/null
  if [ $? -ne 0 ]; then
    if [ "$REGION" = "us-east-1" ]; then
      aws s3api create-bucket --bucket "$BUCKET_NAME" --profile "$PROFILE"
    else
      aws s3api create-bucket \
        --bucket "$BUCKET_NAME" \
        --region "$REGION" \
        --create-bucket-configuration LocationConstraint="$REGION" \
        --profile "$PROFILE"
    fi
    sleep 2
    aws s3api head-bucket --bucket "$BUCKET_NAME" --profile "$PROFILE" 2>/dev/null || {
      echo "Failed to create $BUCKET_NAME"
      continue
    }
  fi

  # Upload
  echo "  Uploading files to S3..."
  if aws s3 cp "$LOCAL_PATH" "s3://$BUCKET_NAME/" --recursive --profile "$PROFILE"; then
    echo "  SUCCESS: Uploaded $FILE_COUNT files to s3://$BUCKET_NAME/"
    SUCCESSFUL=$((SUCCESSFUL + 1))
  else
    echo "  ERROR: Upload failed for '$TEAM_FOLDER'"
    FAILED=$((FAILED + 1))
  fi
  
  echo "----------------------------------------"
done

# Print summary
echo "UPLOAD SUMMARY:"
echo "  Total teams: $TOTAL_TEAMS"
echo "  Successfully processed: $SUCCESSFUL"
echo "  Failed: $FAILED"
echo "  Log file: $LOG_FILE"
echo "----------------------------------------"
echo "Upload process completed at $(date)"
