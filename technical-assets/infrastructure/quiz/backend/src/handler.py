import json
import os
import boto3
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


def lambda_handler(event, context):
    method = event.get("requestContext", {}).get("http", {}).get("method", "")
    path = event.get("rawPath", "")

    if method == "GET" and path.startswith("/submission/"):
        return get_submission(event)
    elif method == "POST" and path == "/submission/quiz":
        return post_quiz(event)
    elif method == "POST" and path == "/submission/responses":
        return post_responses(event)
    else:
        return response(404, {"error": "Not found"})


def get_submission(event):
    email = event.get("pathParameters", {}).get("email", "")
    if not email:
        return response(400, {"error": "Email is required"})

    email = email.lower().strip()

    result = table.get_item(Key={"email": email})
    item = result.get("Item")

    if not item:
        return response(404, {"found": False})

    submission = decimal_to_native(item)
    return response(200, {"found": True, "submission": submission})


def post_quiz(event):
    try:
        body = json.loads(event.get("body", "{}"))
    except (json.JSONDecodeError, TypeError):
        return response(400, {"error": "Invalid JSON body"})

    name = body.get("name", "").strip()
    email = body.get("email", "").strip().lower()
    submitted_at = body.get("submittedAt", "")
    raw_answers = body.get("mcqAnswers", [])
    correct_answers = body.get("correctAnswers", {})

    if not name or not email:
        return response(400, {"error": "Name and email are required"})

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

    # Read existing record to determine best score
    existing = table.get_item(Key={"email": email}).get("Item")
    existing_score = int(existing.get("mcqScore", 0)) if existing else 0
    best_score = max(existing_score, mcq_score)

    # Write quiz results
    table.update_item(
        Key={"email": email},
        UpdateExpression=(
            "SET #n = :name, submittedAt = :ts, "
            "quizTaken = :qt, mcqScore = :best, mcqTotal = :total"
            " ADD mcqAttempts :inc"
        ),
        ExpressionAttributeNames={"#n": "name"},
        ExpressionAttributeValues={
            ":name": name,
            ":ts": submitted_at,
            ":qt": True,
            ":best": best_score,
            ":total": mcq_total,
            ":inc": 1,
        },
    )

    # Fetch attempt count after write
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
    try:
        body = json.loads(event.get("body", "{}"))
    except (json.JSONDecodeError, TypeError):
        return response(400, {"error": "Invalid JSON body"})

    name = body.get("name", "").strip()
    email = body.get("email", "").strip().lower()
    submitted_at = body.get("submittedAt", "")
    section2_answers = body.get("section2Answers", [])

    if not name or not email:
        return response(400, {"error": "Name and email are required"})

    table.update_item(
        Key={"email": email},
        UpdateExpression=(
            "SET #n = :name, section2Answers = :s2, submittedAt = :ts"
        ),
        ExpressionAttributeNames={"#n": "name"},
        ExpressionAttributeValues={
            ":name": name,
            ":s2": section2_answers,
            ":ts": submitted_at,
        },
    )

    return response(200, {"success": True})


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
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
