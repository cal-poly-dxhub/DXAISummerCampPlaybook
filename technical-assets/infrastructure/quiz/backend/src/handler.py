import json
import os
import re
from urllib.parse import unquote
import boto3
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])
ALLOWED_ORIGINS = set(os.environ.get("ALLOWED_ORIGINS", "").split(","))

MAX_NAME_LENGTH = 200
MAX_ANSWER_LENGTH = 5000
MAX_ANSWERS_COUNT = 100
VALID_UNI_VALUES = {"csu", "ccc"}

# Set per-request by lambda_handler
_cors_origin = ""


def lambda_handler(event, context):
    global _cors_origin
    headers = event.get("headers") or {}
    origin = headers.get("origin") or headers.get("Origin") or ""
    _cors_origin = origin if origin in ALLOWED_ORIGINS else ""

    method = event.get("httpMethod", "")
    path = event.get("path", "")

    if method == "GET" and path.startswith("/submission/"):
        return get_submission(event)
    elif method == "POST" and path == "/submission/quiz":
        return post_quiz(event)
    elif method == "POST" and path == "/submission/responses":
        return post_responses(event)
    else:
        return response(404, {"error": "Not found"})


def _get_jwt_email(event):
    """Extract verified email from Cognito authorizer claims (REST API v1 format)."""
    claims = (
        event.get("requestContext", {})
        .get("authorizer", {})
        .get("claims", {})
    )
    return claims.get("email", "").lower()


def _validate_email(email, uni=""):
    if not email:
        return False
    if uni == "ccc":
        return True
    return bool(re.search(r"\.edu$", email, re.IGNORECASE))


def get_submission(event):
    email = event.get("pathParameters", {}).get("email", "")
    if not email:
        return response(400, {"error": "Email is required"})

    email = unquote(email).lower().strip()

    jwt_email = _get_jwt_email(event)
    if jwt_email != email:
        return response(403, {"error": "Access denied"})

    result = table.get_item(Key={"email": email})
    item = result.get("Item")

    if not item:
        return response(404, {"found": False})

    submission = decimal_to_native(item)
    return response(200, {"found": True, "submission": submission})


def post_quiz(event):
    body = _parse_body(event)
    if body is None:
        return response(400, {"error": "Invalid JSON body"})

    jwt_email = _get_jwt_email(event)

    name = body.get("name", "").strip()
    email = body.get("email", "").strip().lower()
    uni = (body.get("uni") or "").strip().lower()
    submitted_at = body.get("submittedAt", "")
    raw_answers = body.get("mcqAnswers", [])
    correct_answers = body.get("correctAnswers", {})

    if not name or not email:
        return response(400, {"error": "Name and email are required"})
    if email != jwt_email:
        return response(403, {"error": "Email does not match authenticated user"})
    if uni not in VALID_UNI_VALUES:
        return response(400, {"error": "Invalid uni value"})
    if not _validate_email(email, uni):
        return response(400, {"error": "A valid .edu email is required"})
    if len(name) > MAX_NAME_LENGTH:
        return response(400, {"error": "Name too long"})
    if not isinstance(raw_answers, list) or len(raw_answers) > MAX_ANSWERS_COUNT:
        return response(400, {"error": "Invalid mcqAnswers"})
    if not isinstance(correct_answers, dict) or len(correct_answers) > MAX_ANSWERS_COUNT:
        return response(400, {"error": "Invalid correctAnswers"})
    if not isinstance(submitted_at, str) or len(submitted_at) > 50:
        return response(400, {"error": "Invalid submittedAt"})

    for ans in raw_answers:
        if not isinstance(ans, dict):
            return response(400, {"error": "Invalid answer entry"})
        if isinstance(ans.get("answer"), str) and len(ans["answer"]) > MAX_ANSWER_LENGTH:
            return response(400, {"error": "Answer text too long"})

    # Server-side grading
    mcq_score = 0
    mcq_total = 0

    for ans in raw_answers:
        if ans.get("type") == "mcq":
            mcq_total += 1
            correct = correct_answers.get(str(ans.get("id")), "")
            if ans.get("answer") == correct:
                mcq_score += 1

    current_mcq_score = mcq_score

    existing = table.get_item(Key={"email": email}).get("Item")
    existing_score = int(existing.get("mcqScore", 0)) if existing else 0
    best_score = max(existing_score, mcq_score)

    table.update_item(
        Key={"email": email},
        UpdateExpression=(
            "SET #n = :name, uni = :uni, submittedAt = :ts, "
            "quizTaken = :qt, mcqScore = :best, mcqTotal = :total"
            " ADD mcqAttempts :inc"
        ),
        ExpressionAttributeNames={"#n": "name"},
        ExpressionAttributeValues={
            ":name": name,
            ":uni": uni,
            ":ts": submitted_at,
            ":qt": True,
            ":best": best_score,
            ":total": mcq_total,
            ":inc": 1,
        },
    )

    result = table.get_item(Key={"email": email})
    item = result.get("Item", {})
    attempt_count = int(item.get("mcqAttempts", 1))

    return response(200, {
        "success": True,
        "mcqScore": current_mcq_score,
        "mcqTotal": mcq_total,
        "bestScore": best_score,
        "mcqAttempts": attempt_count,
    })


def post_responses(event):
    body = _parse_body(event)
    if body is None:
        return response(400, {"error": "Invalid JSON body"})

    jwt_email = _get_jwt_email(event)

    name = body.get("name", "").strip()
    email = body.get("email", "").strip().lower()
    uni = (body.get("uni") or "").strip().lower()
    submitted_at = body.get("submittedAt", "")
    section2_answers = body.get("section2Answers", [])

    if not name or not email:
        return response(400, {"error": "Name and email are required"})
    if email != jwt_email:
        return response(403, {"error": "Email does not match authenticated user"})
    if uni not in VALID_UNI_VALUES:
        return response(400, {"error": "Invalid uni value"})
    if not _validate_email(email, uni):
        return response(400, {"error": "A valid .edu email is required"})
    if len(name) > MAX_NAME_LENGTH:
        return response(400, {"error": "Name too long"})
    if not isinstance(section2_answers, list) or len(section2_answers) > MAX_ANSWERS_COUNT:
        return response(400, {"error": "Invalid section2Answers"})
    if not isinstance(submitted_at, str) or len(submitted_at) > 50:
        return response(400, {"error": "Invalid submittedAt"})

    for ans in section2_answers:
        if not isinstance(ans, dict):
            return response(400, {"error": "Invalid answer entry"})
        if isinstance(ans.get("answer"), str) and len(ans["answer"]) > MAX_ANSWER_LENGTH:
            return response(400, {"error": "Answer text too long"})

    table.update_item(
        Key={"email": email},
        UpdateExpression=(
            "SET #n = :name, uni = :uni, section2Answers = :s2, submittedAt = :ts"
        ),
        ExpressionAttributeNames={"#n": "name"},
        ExpressionAttributeValues={
            ":name": name,
            ":uni": uni,
            ":s2": section2_answers,
            ":ts": submitted_at,
        },
    )

    return response(200, {"success": True})


def _parse_body(event):
    try:
        return json.loads(event.get("body", "{}"))
    except (json.JSONDecodeError, TypeError):
        return None


def response(status_code, body):
    headers = {"Content-Type": "application/json"}
    if _cors_origin:
        headers["Access-Control-Allow-Origin"] = _cors_origin
        headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization,x-aws-waf-token"
        headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return {
        "statusCode": status_code,
        "headers": headers,
        "body": json.dumps(body),
    }


def decimal_to_native(obj):
    """Recursively convert DynamoDB Decimal types to int/float."""
    if isinstance(obj, list):
        return [decimal_to_native(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj == int(obj) else float(obj)
    return obj
