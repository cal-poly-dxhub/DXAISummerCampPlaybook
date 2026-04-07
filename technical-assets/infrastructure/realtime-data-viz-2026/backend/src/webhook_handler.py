"""
Webhook handler for CognitoForms submissions.
Receives POST at /webhook/{org}, validates, classifies, and stores in DynamoDB.
"""

import json
import logging
import os
from datetime import datetime, timezone

import boto3

from classification import classify_institution, classify_major

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["APPLICATIONS_TABLE"])

WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")
ALLOWED_ORIGINS = {o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()}

_request_origin = ""

# CognitoForms field name mappings per org.
# Verified from actual webhook payloads captured 2026-03-31.
FIELD_MAPS = {
    "csu": {
        "email": "YourUniversityEmailAddressEDUEMAILSONLYNoneduEmailsWillBeDisqualified",
        "name_obj": "Name",
        "major": "WhatAcademicMajorAreYouStudyingincludingAdditionalAcademicProgramsAsApplicable",
        "years": "HowManyYearsOfInstructionHaveYouCompletedmayIncludeTransferCredit",
        "of_age": "WillYouBeAge18OrOlderOnJuly12th2026",
        "phone": "Phone",
        "institution_field": None,  # CSU uses email domain
        "technical_experience": "TechnicalExperience",
        "coding_env": "DoYouCurrentlyHaveAWorkingCodingEnvironmentegVSCodeWorkingOnYourLaptop",
        "resume": "PleaseUploadACopyOfYourResumeAsAPDFFile",
    },
    "ccc": {
        "email": "YourEmailAddress",
        "name_obj": "Name",
        "major": "WhatAcademicMajorAreYouStudyingincludingAdditionalAcademicProgramsAsApplicable",
        "years": "NumberOfSemestersOrQuartersAttendedAtACommunityCollege",
        "of_age": "WillYouBeAge18OrOlderOnJuly12th2026",
        "phone": "Phone",
        "institution_field": None,  # CCC uses email domain; no explicit institution field on form
        "technical_experience": "TechnicalExperience",
        "coding_env": "DoYouCurrentlyHaveAWorkingCodingEnvironmentegVSCodeWorkingOnYourLaptop",
        "resume": "PleaseUploadACopyOfYourResumeAsAPDFFile",
        "goals": "Goals",
    },
}


def cors_headers():
    origin = _request_origin if _request_origin in ALLOWED_ORIGINS else ""
    return {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Webhook-Secret",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    }


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {**cors_headers(), "Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def safe_get(payload, key, default=""):
    """Safely get a field from the payload, trying the key directly."""
    if not key:
        return default
    val = payload.get(key, default)
    return val if val is not None else default


def extract_fields(payload, org):
    """Extract structured fields from CognitoForms JSON payload."""
    field_map = FIELD_MAPS.get(org, FIELD_MAPS["csu"])

    # Extract name
    name_obj = safe_get(payload, field_map["name_obj"], {})
    if isinstance(name_obj, dict):
        first_name = name_obj.get("First", "")
        last_name = name_obj.get("Last", "")
    else:
        first_name = str(name_obj)
        last_name = ""

    # Extract email
    email = str(safe_get(payload, field_map["email"], "")).strip().lower()

    # Extract major and classify
    raw_major = str(safe_get(payload, field_map["major"], ""))
    major_category, is_cs = classify_major(raw_major)

    # Extract years of instruction
    years = str(safe_get(payload, field_map["years"], ""))

    # Extract age verification
    of_age_raw = safe_get(payload, field_map["of_age"], "")
    if isinstance(of_age_raw, bool):
        is_of_age = of_age_raw
    else:
        is_of_age = str(of_age_raw).lower() in ("yes", "true", "1")

    # Institution classification
    form_institution = str(safe_get(payload, field_map.get("institution_field"), ""))
    institution = classify_institution(email, org, form_institution)

    # Extract email domain
    email_domain = email.split("@")[-1] if "@" in email else ""

    # Timestamp from CognitoForms or fallback to now
    entry_info = payload.get("Entry", {})
    submitted_at = ""
    if isinstance(entry_info, dict):
        submitted_at = entry_info.get("Timestamp", "")
    if not submitted_at:
        submitted_at = payload.get("DateCreated", "")
    if not submitted_at:
        submitted_at = datetime.now(timezone.utc).isoformat()

    # Technical experience ratings (nested object with 1-5 ratings)
    tech_exp = safe_get(payload, field_map.get("technical_experience"), {})
    if not isinstance(tech_exp, dict):
        tech_exp = {}
    ai_experience = tech_exp.get("HowMuchExperienceDoYouHaveWithAI_Rating", 0)
    cloud_experience = tech_exp.get("HoMuchExperienceDoYouHaveUsingCloudServices_Rating", 0)
    ai_assistant_experience = tech_exp.get("HowMuchExperienceDoYouHaveUsingAnAICodingAssistant_Rating", 0)

    # Coding environment
    has_coding_env = safe_get(payload, field_map.get("coding_env"), False)
    if not isinstance(has_coding_env, bool):
        has_coding_env = str(has_coding_env).lower() in ("yes", "true", "1")

    # Resume info (just store name + link, not the file itself)
    resume_files = safe_get(payload, field_map.get("resume"), [])
    resume_info = []
    if isinstance(resume_files, list):
        for f in resume_files:
            if isinstance(f, dict):
                resume_info.append({"name": f.get("Name", ""), "id": f.get("Id", "")})

    # Goals (CCC only)
    goals = str(safe_get(payload, field_map.get("goals"), ""))

    return {
        "pk": f"{org}#{email}",
        "sk": "APPLICATION",
        "org": org,
        "email": email,
        "firstName": first_name,
        "lastName": last_name,
        "phone": str(safe_get(payload, field_map.get("phone"), "")),
        "major": raw_major,
        "majorCategory": major_category,
        "csBackground": is_cs,
        "yearsOfInstruction": years,
        "isOfAge": is_of_age,
        "institution": institution,
        "emailDomain": email_domain,
        "submittedAt": submitted_at,
        "aiExperience": ai_experience,
        "cloudExperience": cloud_experience,
        "aiAssistantExperience": ai_assistant_experience,
        "hasCodingEnv": has_coding_env,
        "resumeInfo": resume_info,
        "goals": goals,
        "rawPayload": payload,
    }


def lambda_handler(event, context):
    """Handle incoming CognitoForms webhook POST."""
    global _request_origin
    _request_origin = (event.get("headers") or {}).get("origin") or (event.get("headers") or {}).get("Origin") or ""

    # Handle OPTIONS preflight
    if event.get("httpMethod") == "OPTIONS":
        return response(200, {"message": "ok"})

    # Validate webhook secret (check header first, fall back to query param)
    headers = event.get("headers") or {}
    secret = headers.get("X-Webhook-Secret") or headers.get("x-webhook-secret") or ""
    if not secret:
        params = event.get("queryStringParameters") or {}
        secret = params.get("secret", "")
    if secret != WEBHOOK_SECRET:
        logger.warning("Invalid webhook secret")
        return response(401, {"error": "Unauthorized"})

    # Extract org from path
    path_params = event.get("pathParameters") or {}
    org = path_params.get("org", "").lower()
    if org not in ("csu", "ccc"):
        return response(400, {"error": f"Invalid org: {org}. Must be 'csu' or 'ccc'."})

    # Parse body
    try:
        body = event.get("body", "")
        if isinstance(body, str):
            payload = json.loads(body)
        else:
            payload = body or {}
    except (json.JSONDecodeError, TypeError) as e:
        logger.error(f"Failed to parse body: {e}")
        return response(400, {"error": "Invalid JSON body"})

    if not payload:
        return response(400, {"error": "Empty payload"})

    # Extract and classify fields
    try:
        item = extract_fields(payload, org)
    except Exception as e:
        logger.error(f"Field extraction failed: {e}")
        return response(400, {"error": f"Failed to extract fields: {str(e)}"})

    if not item["email"]:
        return response(400, {"error": "Missing email in submission"})

    # Store in DynamoDB
    try:
        table.put_item(Item=json.loads(json.dumps(item), parse_float=str))
        logger.info(f"Stored application: org={org}, email={item['email']}, institution={item['institution']}")
    except Exception as e:
        logger.error(f"DynamoDB put failed: {e}")
        return response(500, {"error": "Failed to store application"})

    return response(200, {"message": "received"})
