#!/usr/bin/env python3
"""Export quiz submissions from DynamoDB to CSV."""

import boto3
import csv
import sys
import os
from decimal import Decimal

TABLE_NAME = "quiz-submissions"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "quiz_results.csv")


def decimal_to_native(obj):
    if isinstance(obj, list):
        return [decimal_to_native(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: decimal_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj == int(obj) else float(obj)
    return obj


def main():
    dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
    table = dynamodb.Table(TABLE_NAME)

    print(f"Scanning {TABLE_NAME}...")
    items = []
    response = table.scan()
    items.extend(response["Items"])
    while "LastEvaluatedKey" in response:
        response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
        items.extend(response["Items"])

    if not items:
        print("No submissions found.")
        return

    items = [decimal_to_native(item) for item in items]
    items.sort(key=lambda x: x.get("email", ""))

    # Collect all section 2 questions for column headers
    s2_questions = []
    for item in items:
        for ans in item.get("section2Answers", []):
            if not isinstance(ans, dict):
                continue
            q = ans.get("question")
            if not isinstance(q, str) or not q:
                continue
            if q not in s2_questions:
                s2_questions.append(q)

    # Build CSV
    headers = ["email", "name", "uni", "quizTaken", "mcqAttempts", "mcqScore", "mcqTotal", "submittedAt"]
    for q in s2_questions:
        headers.append(f"Response: {q}")

    output = OUTPUT_FILE if len(sys.argv) < 2 else sys.argv[1]

    with open(output, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        for item in items:
            email = item.get("email", "")
            row = [
                email,
                item.get("name", ""),
                item.get("uni", ""),
                item.get("quizTaken", False),
                item.get("mcqAttempts", 0),
                item.get("mcqScore", 0),
                item.get("mcqTotal", 0),
                item.get("submittedAt", ""),
            ]

            answers = {}
            for a in item.get("section2Answers", []):
                if not isinstance(a, dict):
                    print(f"  WARNING: [{email}] malformed answer entry (not a dict): {a!r}")
                    continue
                q = a.get("question")
                if not isinstance(q, str) or not q:
                    print(f"  WARNING: [{email}] malformed answer entry (bad/missing question): {a!r}")
                    continue
                val = a.get("answer", "")
                if not isinstance(val, str):
                    print(f"  WARNING: [{email}] non-string answer for \"{q}\": {val!r}")
                    val = str(val)
                answers[q] = val
            for q in s2_questions:
                row.append(answers.get(q, ""))

            writer.writerow(row)

    print(f"Exported {len(items)} submissions to {output}")


if __name__ == "__main__":
    main()
