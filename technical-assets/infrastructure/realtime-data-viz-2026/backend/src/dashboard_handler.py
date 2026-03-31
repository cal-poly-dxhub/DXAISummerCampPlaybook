"""
Dashboard API handler. Serves aggregated stats from both the applications
table and the quiz-submissions table. All endpoints require a shared password
via the Authorization header.
"""

import hashlib
import hmac
import json
import logging
import os
from collections import defaultdict
from decimal import Decimal

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
applications_table = dynamodb.Table(os.environ["APPLICATIONS_TABLE"])
quiz_table = dynamodb.Table(os.environ["QUIZ_TABLE"])

ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*")
DASHBOARD_PASSWORD = os.environ.get("DASHBOARD_PASSWORD", "")


class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return int(o) if o == int(o) else float(o)
        return super().default(o)


def cors_headers():
    return {
        "Access-Control-Allow-Origin": ALLOWED_ORIGINS,
        "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Webhook-Secret",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    }


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {**cors_headers(), "Content-Type": "application/json"},
        "body": json.dumps(body, cls=DecimalEncoder),
    }


def scan_all(table_resource, **kwargs):
    """Paginated scan that returns all items."""
    items = []
    resp = table_resource.scan(**kwargs)
    items.extend(resp.get("Items", []))
    while "LastEvaluatedKey" in resp:
        resp = table_resource.scan(ExclusiveStartKey=resp["LastEvaluatedKey"], **kwargs)
        items.extend(resp.get("Items", []))
    return items


def get_applications(org_filter="all"):
    """Get applications, optionally filtered by org."""
    if org_filter in ("csu", "ccc"):
        items = scan_all(
            applications_table,
            IndexName="OrgIndex",
            FilterExpression=boto3.dynamodb.conditions.Attr("org").eq(org_filter),
        )
    else:
        items = scan_all(applications_table)
    return items


def get_quiz_data(org_filter="all"):
    """Get quiz submissions, optionally filtered by org (uni field)."""
    items = scan_all(quiz_table)
    if org_filter in ("csu", "ccc"):
        items = [i for i in items if i.get("uni") == org_filter]
    return items


def build_stats(applications, quiz_items):
    """Build aggregated statistics from applications and quiz data."""
    # Application stats
    total = len(applications)
    qualified = sum(1 for a in applications if a.get("isOfAge") is True)

    by_org = defaultdict(int)
    by_institution = defaultdict(int)
    by_major = defaultdict(int)
    by_cs = defaultdict(int)
    by_years = defaultdict(int)
    by_years_csu = defaultdict(int)
    by_years_ccc = defaultdict(int)
    by_date = defaultdict(int)

    # Technical experience from application forms (1-5 ratings)
    app_ai_exp = defaultdict(int)       # distribution of 1-5
    app_cloud_exp = defaultdict(int)
    app_assistant_exp = defaultdict(int)
    ai_exp_values = []
    cloud_exp_values = []
    assistant_exp_values = []

    # Per-institution technical experience for averages
    inst_tech_totals = defaultdict(lambda: {"sum": 0, "count": 0})

    for app in applications:
        org = app.get("org", "unknown")
        by_org[org] += 1
        institution = app.get("institution", "Unknown")
        by_institution[institution] += 1
        raw_cat = app.get("majorCategory", "Other")
        cs = app.get("csBackground", False)
        by_cs["Yes" if cs else "No"] += 1
        if raw_cat.startswith("STEM"):
            by_major["STEM"] += 1
        else:
            by_major[raw_cat] += 1
        years_val = app.get("yearsOfInstruction", "Unknown")
        by_years[years_val] += 1
        if org == "csu":
            by_years_csu[years_val] += 1
        elif org == "ccc":
            by_years_ccc[years_val] += 1

        submitted = app.get("submittedAt", "")
        if submitted:
            date_str = submitted[:10]  # YYYY-MM-DD
            by_date[date_str] += 1

        # Technical experience ratings
        ai_val = app.get("aiExperience", 0)
        cloud_val = app.get("cloudExperience", 0)
        assistant_val = app.get("aiAssistantExperience", 0)

        if ai_val:
            rating = int(float(ai_val))
            app_ai_exp[str(rating)] += 1
            ai_exp_values.append(rating)
        if cloud_val:
            rating = int(float(cloud_val))
            app_cloud_exp[str(rating)] += 1
            cloud_exp_values.append(rating)
        if assistant_val:
            rating = int(float(assistant_val))
            app_assistant_exp[str(rating)] += 1
            assistant_exp_values.append(rating)

        # Aggregate per-institution avg (average of all 3 ratings per person)
        person_ratings = [v for v in [ai_val, cloud_val, assistant_val] if v]
        if person_ratings:
            person_avg = sum(float(v) for v in person_ratings) / len(person_ratings)
            inst_tech_totals[institution]["sum"] += person_avg
            inst_tech_totals[institution]["count"] += 1

    # Compute per-institution average technical experience
    tech_by_institution = {}
    for inst, data in inst_tech_totals.items():
        if data["count"] > 0:
            tech_by_institution[inst] = round(data["sum"] / data["count"], 1)
    tech_by_institution = dict(sorted(tech_by_institution.items(), key=lambda x: -x[1]))

    # Quiz stats
    quiz_total = len(quiz_items)
    quiz_taken = sum(1 for q in quiz_items if q.get("quizTaken"))
    quiz_scores = []
    quiz_attempts = defaultdict(int)
    quiz_tech_ability = defaultdict(int)  # distribution of 1-5 from quiz section2
    quiz_tech_values = []

    for q in quiz_items:
        if q.get("quizTaken"):
            score = q.get("mcqScore", 0)
            total_q = q.get("mcqTotal", 1)
            if total_q:
                pct = round(int(score) / int(total_q) * 100)
                quiz_scores.append(pct)
            attempts = int(q.get("mcqAttempts", 1))
            bucket = str(attempts) if attempts <= 3 else "4+"
            quiz_attempts[bucket] += 1

        # Extract technical ability from section2Answers
        section2 = q.get("section2Answers") or []
        for ans in section2:
            q_text = str(ans.get("question", "")).lower()
            if "technical ability" in q_text or "rate your technical" in q_text:
                answer_str = str(ans.get("answer", ""))
                # Parse rating from answers like "3 (Intermediate)" or just "3"
                for ch in answer_str:
                    if ch.isdigit() and 1 <= int(ch) <= 5:
                        rating = int(ch)
                        quiz_tech_ability[str(rating)] += 1
                        quiz_tech_values.append(rating)
                        break

    # Score distribution buckets
    score_dist = defaultdict(int)
    for s in quiz_scores:
        if s <= 20:
            score_dist["0-20%"] += 1
        elif s <= 40:
            score_dist["21-40%"] += 1
        elif s <= 60:
            score_dist["41-60%"] += 1
        elif s <= 80:
            score_dist["61-80%"] += 1
        else:
            score_dist["81-100%"] += 1

    avg_score = round(sum(quiz_scores) / len(quiz_scores), 1) if quiz_scores else 0

    # Cross-reference: applications vs quiz by email
    app_emails = {a.get("email", "").lower() for a in applications}
    quiz_emails = {q.get("email", "").lower() for q in quiz_items if q.get("quizTaken")}
    both = app_emails & quiz_emails
    app_only = app_emails - quiz_emails
    quiz_only = quiz_emails - app_emails

    # Application trend sorted by date
    trend = [{"date": d, "count": c} for d, c in sorted(by_date.items())]

    return {
        "totalApplicants": {
            "all": total,
            "csu": by_org.get("csu", 0),
            "ccc": by_org.get("ccc", 0),
        },
        "qualifiedApplicants": qualified,
        "institutionsCount": len(by_institution),
        "byInstitution": dict(sorted(by_institution.items(), key=lambda x: -x[1])),
        "byMajorCategory": dict(sorted(by_major.items(), key=lambda x: -x[1])),
        "csMajorSplit": {
            "Computing Majors": by_cs.get("Yes", 0),
            "Other Majors": by_cs.get("No", 0),
        },
        "byYearsOfInstruction": dict(by_years),
        "yearsByOrg": {
            "csu": dict(by_years_csu),
            "ccc": dict(by_years_ccc),
        },
        "applicationTrend": trend,
        "technicalExperience": {
            "aiExperience": dict(sorted(app_ai_exp.items())),
            "cloudExperience": dict(sorted(app_cloud_exp.items())),
            "aiAssistantExperience": dict(sorted(app_assistant_exp.items())),
            "avgAiExperience": round(sum(ai_exp_values) / len(ai_exp_values), 1) if ai_exp_values else 0,
            "avgCloudExperience": round(sum(cloud_exp_values) / len(cloud_exp_values), 1) if cloud_exp_values else 0,
            "avgAiAssistantExperience": round(sum(assistant_exp_values) / len(assistant_exp_values), 1) if assistant_exp_values else 0,
            "byInstitution": tech_by_institution,
        },
        "quiz": {
            "totalQuizTakers": quiz_taken,
            "averageScore": avg_score,
            "scoreDistribution": dict(score_dist),
            "attemptDistribution": dict(quiz_attempts),
            "techAbility": dict(sorted(quiz_tech_ability.items())),
            "avgTechAbility": round(sum(quiz_tech_values) / len(quiz_tech_values), 1) if quiz_tech_values else 0,
        },
        "crossReference": {
            "appliedAndQuiz": len(both),
            "appliedOnly": len(app_only),
            "quizOnly": len(quiz_only),
        },
    }


def handle_stats(event):
    """GET /api/stats — aggregated dashboard statistics."""
    params = event.get("queryStringParameters") or {}
    org = params.get("org", "all").lower()

    applications = get_applications(org)
    quiz_items = get_quiz_data(org)
    stats = build_stats(applications, quiz_items)

    return response(200, stats)


def handle_applications(event):
    """GET /api/applications — paginated application list."""
    params = event.get("queryStringParameters") or {}
    org = params.get("org", "all").lower()

    applications = get_applications(org)

    # Strip rawPayload to reduce response size
    clean = []
    for app in applications:
        item = {k: v for k, v in app.items() if k != "rawPayload"}
        clean.append(item)

    # Sort by submittedAt descending
    clean.sort(key=lambda x: x.get("submittedAt", ""), reverse=True)

    return response(200, {"applications": clean, "count": len(clean)})


def handle_quiz(event):
    """GET /api/quiz — quiz data summary."""
    params = event.get("queryStringParameters") or {}
    org = params.get("org", "all").lower()

    quiz_items = get_quiz_data(org)

    # Build per-person quiz summary (no section2Answers to reduce size)
    summaries = []
    for q in quiz_items:
        summaries.append({
            "email": q.get("email", ""),
            "name": q.get("name", ""),
            "uni": q.get("uni", ""),
            "quizTaken": q.get("quizTaken", False),
            "mcqScore": q.get("mcqScore", 0),
            "mcqTotal": q.get("mcqTotal", 0),
            "mcqAttempts": q.get("mcqAttempts", 0),
            "submittedAt": q.get("submittedAt", ""),
        })

    summaries.sort(key=lambda x: x.get("submittedAt", ""), reverse=True)

    return response(200, {"quizData": summaries, "count": len(summaries)})


def handle_combined(event):
    """GET /api/combined — cross-reference applications + quiz."""
    params = event.get("queryStringParameters") or {}
    org = params.get("org", "all").lower()

    applications = get_applications(org)
    quiz_items = get_quiz_data(org)

    # Index by email
    app_by_email = {}
    for a in applications:
        email = a.get("email", "").lower()
        if email:
            app_by_email[email] = {k: v for k, v in a.items() if k != "rawPayload"}

    quiz_by_email = {}
    for q in quiz_items:
        email = q.get("email", "").lower()
        if email:
            quiz_by_email[email] = {
                "quizTaken": q.get("quizTaken", False),
                "mcqScore": q.get("mcqScore", 0),
                "mcqTotal": q.get("mcqTotal", 0),
                "mcqAttempts": q.get("mcqAttempts", 0),
                "submittedAt": q.get("submittedAt", ""),
            }

    all_emails = set(app_by_email.keys()) | set(quiz_by_email.keys())

    combined = []
    for email in sorted(all_emails):
        entry = {"email": email}
        if email in app_by_email:
            entry["application"] = app_by_email[email]
        if email in quiz_by_email:
            entry["quiz"] = quiz_by_email[email]
        entry["status"] = (
            "both" if email in app_by_email and email in quiz_by_email
            else "applicationOnly" if email in app_by_email
            else "quizOnly"
        )
        combined.append(entry)

    return response(200, {"combined": combined, "count": len(combined)})


# Route map
ROUTES = {
    "/api/stats": handle_stats,
    "/api/applications": handle_applications,
    "/api/quiz": handle_quiz,
    "/api/combined": handle_combined,
}


def check_auth(event):
    """Validate the Authorization: Bearer <password> header."""
    auth_header = (event.get("headers") or {}).get("Authorization", "")
    # Also check lowercase (API Gateway may normalize)
    if not auth_header:
        auth_header = (event.get("headers") or {}).get("authorization", "")

    if not auth_header.startswith("Bearer "):
        return False

    provided = auth_header[7:]  # Strip "Bearer "
    return hmac.compare_digest(provided, DASHBOARD_PASSWORD)


def lambda_handler(event, context):
    """Main router for dashboard API."""
    if event.get("httpMethod") == "OPTIONS":
        return response(200, {"message": "ok"})

    # Authenticate
    if not check_auth(event):
        return response(401, {"error": "Unauthorized"})

    path = event.get("path", "")
    handler_fn = ROUTES.get(path)

    if not handler_fn:
        return response(404, {"error": f"Not found: {path}"})

    try:
        return handler_fn(event)
    except Exception as e:
        logger.error(f"Error handling {path}: {e}", exc_info=True)
        return response(500, {"error": "Internal server error"})
