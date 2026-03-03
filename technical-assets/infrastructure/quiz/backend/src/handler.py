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
    elif method == "POST" and path == "/submission":
        return post_submission(event)
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

    # Convert Decimal types for JSON serialization
    submission = decimal_to_native(item)
    return response(200, {"found": True, "submission": submission})


def post_submission(event):
    try:
        body = json.loads(event.get("body", "{}"))
    except (json.JSONDecodeError, TypeError):
        return response(400, {"error": "Invalid JSON body"})

    name = body.get("name", "").strip()
    email = body.get("email", "").strip().lower()
    submitted_at = body.get("submittedAt", "")
    raw_answers = body.get("answers", [])
    correct_answers = body.get("correctAnswers", {})

    if not name or not email:
        return response(400, {"error": "Name and email are required"})

    # Build clean answers with server-side grading
    clean_answers = []
    mcq_score = 0
    mcq_total = 0

    for ans in raw_answers:
        entry = {
            "id": ans.get("id"),
            "type": ans.get("type"),
            "question": ans.get("question"),
            "answer": ans.get("answer"),
        }

        if ans.get("type") == "mcq":
            mcq_total += 1
            correct = correct_answers.get(str(ans.get("id")), "")
            is_correct = ans.get("answer") == correct
            entry["isCorrect"] = is_correct
            if is_correct:
                mcq_score += 1

        clean_answers.append(entry)

    # Save the current attempt's MCQ score for the response
    current_mcq_score = mcq_score

    # Read existing record to decide how to merge
    existing = table.get_item(Key={"email": email}).get("Item")
    existing_score = int(existing.get("mcqScore", 0)) if existing else 0

    new_frq = [a for a in clean_answers if a.get("type") == "frq"]

    if not existing or mcq_score >= existing_score:
        # New score is best (or tied): use all new answers as-is
        merged_answers = clean_answers
        best_score = mcq_score
    else:
        # Worse MCQ score: keep stored MCQ answers, replace FRQ with latest
        stored_answers = existing.get("answers", [])
        merged_answers = [a for a in decimal_to_native(stored_answers) if a.get("type") != "frq"]
        merged_answers.extend(new_frq)
        best_score = existing_score

    # Single atomic write: always update everything
    table.update_item(
        Key={"email": email},
        UpdateExpression=(
            "SET #n = :name, submittedAt = :ts, answers = :ans, "
            "mcqScore = :score, mcqTotal = :total "
            "ADD attemptCount :inc"
        ),
        ExpressionAttributeNames={"#n": "name"},
        ExpressionAttributeValues={
            ":name": name,
            ":ts": submitted_at,
            ":ans": merged_answers,
            ":score": best_score,
            ":total": mcq_total,
            ":inc": 1,
        },
    )

    # Fetch attempt count after write
    result = table.get_item(Key={"email": email})
    item = result.get("Item", {})
    attempt_count = int(item.get("attemptCount", 1))

    return response(200, {
        "success": True,
        "mcqScore": current_mcq_score,
        "mcqTotal": mcq_total,
        "bestScore": best_score,
        "bestTotal": mcq_total,
        "attemptCount": attempt_count,
    })


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
