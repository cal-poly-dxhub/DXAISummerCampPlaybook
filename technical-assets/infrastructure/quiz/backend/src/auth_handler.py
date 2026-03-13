import json
import os
import time
import secrets
import string
import boto3

cognito = boto3.client("cognito-idp")
dynamodb = boto3.resource("dynamodb")
auth_table = dynamodb.Table(os.environ["AUTH_STATE_TABLE"])

USER_POOL_ID = os.environ["USER_POOL_ID"]
CLIENT_ID = os.environ["USER_POOL_CLIENT_ID"]
ALLOWED_ORIGINS = set(os.environ.get("ALLOWED_ORIGINS", "").split(","))
CCC_ORIGINS = set(os.environ.get("CCC_ORIGINS", "").split(","))

MAX_OTP_PER_HOUR = 5

# Set per-request by lambda_handler
_cors_origin = ""
_is_ccc = False


def lambda_handler(event, context):
    global _cors_origin, _is_ccc
    headers = event.get("headers") or {}
    origin = headers.get("origin") or headers.get("Origin") or ""
    _cors_origin = origin if origin in ALLOWED_ORIGINS else ""
    _is_ccc = origin in CCC_ORIGINS

    method = event.get("httpMethod", "")
    path = event.get("path", "")

    if method == "POST" and path == "/auth/send-code":
        return send_code(event)
    elif method == "POST" and path == "/auth/verify-code":
        return verify_code(event)
    elif method == "POST" and path == "/auth/refresh":
        return refresh_token(event)
    else:
        return resp(404, {"error": "Not found"})


# ---- Send verification code ------------------------------------------------

def send_code(event):
    body = _parse_body(event)
    if body is None:
        return resp(400, {"error": "Invalid JSON"})

    email = body.get("email", "").strip().lower()

    if not email:
        return resp(400, {"error": "A valid email is required"})
    if not _is_ccc and not email.endswith(".edu"):
        return resp(400, {"error": "A valid .edu email is required"})
    if len(email) > 254:
        return resp(400, {"error": "Email too long"})

    # Rate limit (WAF handles CAPTCHA, this is belt-and-suspenders)
    allowed, _ = _check_rate_limit(email)
    if not allowed:
        return resp(429, {
            "error": "Too many verification codes requested. Try again later.",
        })

    password = _generate_password()

    try:
        user = cognito.admin_get_user(
            UserPoolId=USER_POOL_ID,
            Username=email,
        )
        status = user["UserStatus"]

        if status == "UNCONFIRMED":
            state = auth_table.get_item(Key={"email": email}).get("Item")
            if state and state.get("temp_password"):
                cognito.resend_confirmation_code(
                    ClientId=CLIENT_ID,
                    Username=email,
                )
            else:
                cognito.admin_delete_user(
                    UserPoolId=USER_POOL_ID,
                    Username=email,
                )
                cognito.sign_up(
                    ClientId=CLIENT_ID,
                    Username=email,
                    Password=password,
                    UserAttributes=[{"Name": "email", "Value": email}],
                )
                _store_auth_state(email, password, "pending_verification")

        elif status == "CONFIRMED":
            cognito.forgot_password(
                ClientId=CLIENT_ID,
                Username=email,
            )
            _store_auth_state(email, password, "pending_reset")

        else:
            return resp(400, {"error": "Account in unexpected state. Contact support."})

    except cognito.exceptions.UserNotFoundException:
        cognito.sign_up(
            ClientId=CLIENT_ID,
            Username=email,
            Password=password,
            UserAttributes=[{"Name": "email", "Value": email}],
        )
        _store_auth_state(email, password, "pending_verification")

    return resp(200, {"success": True})


# ---- Verify code and return JWT tokens -------------------------------------

def verify_code(event):
    body = _parse_body(event)
    if body is None:
        return resp(400, {"error": "Invalid JSON"})

    email = body.get("email", "").strip().lower()
    code = body.get("code", "").strip()

    if not email or not code:
        return resp(400, {"error": "Email and code are required"})
    if len(code) > 10:
        return resp(400, {"error": "Invalid code format"})

    state = auth_table.get_item(Key={"email": email}).get("Item")
    if not state or not state.get("temp_password"):
        return resp(400, {"error": "No pending verification. Please request a new code."})

    password = state["temp_password"]
    status = state.get("status", "")

    try:
        if status == "pending_verification":
            cognito.confirm_sign_up(
                ClientId=CLIENT_ID,
                Username=email,
                ConfirmationCode=code,
            )
        elif status == "pending_reset":
            cognito.confirm_forgot_password(
                ClientId=CLIENT_ID,
                Username=email,
                ConfirmationCode=code,
                Password=password,
            )
        else:
            return resp(400, {"error": "Invalid auth state. Please request a new code."})

        auth_result = cognito.admin_initiate_auth(
            UserPoolId=USER_POOL_ID,
            ClientId=CLIENT_ID,
            AuthFlow="ADMIN_USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": email,
                "PASSWORD": password,
            },
        )

        tokens = auth_result["AuthenticationResult"]
        return resp(200, {
            "success": True,
            "idToken": tokens["IdToken"],
            "accessToken": tokens["AccessToken"],
            "refreshToken": tokens["RefreshToken"],
            "expiresIn": tokens["ExpiresIn"],
        })

    except cognito.exceptions.CodeMismatchException:
        return resp(400, {"error": "Invalid verification code."})
    except cognito.exceptions.ExpiredCodeException:
        return resp(400, {"error": "Code expired. Please request a new one."})
    except cognito.exceptions.NotAuthorizedException as e:
        print(f"Auth error: {e}")
        return resp(400, {"error": "Authentication failed. Please request a new code."})
    except Exception as e:
        print(f"Unexpected auth error: {e}")
        return resp(500, {"error": "Authentication failed."})


# ---- Refresh tokens --------------------------------------------------------

def refresh_token(event):
    body = _parse_body(event)
    if body is None:
        return resp(400, {"error": "Invalid JSON"})

    token = body.get("refreshToken", "")
    if not token:
        return resp(400, {"error": "Refresh token is required"})

    try:
        result = cognito.admin_initiate_auth(
            UserPoolId=USER_POOL_ID,
            ClientId=CLIENT_ID,
            AuthFlow="REFRESH_TOKEN_AUTH",
            AuthParameters={"REFRESH_TOKEN": token},
        )
        tokens = result["AuthenticationResult"]
        return resp(200, {
            "success": True,
            "idToken": tokens["IdToken"],
            "accessToken": tokens["AccessToken"],
            "expiresIn": tokens["ExpiresIn"],
        })
    except Exception:
        return resp(401, {"error": "Token refresh failed. Please sign in again."})


# ---- Helpers ---------------------------------------------------------------

def _parse_body(event):
    try:
        return json.loads(event.get("body", "{}"))
    except (json.JSONDecodeError, TypeError):
        return None


def _check_rate_limit(email):
    now = int(time.time())
    one_hour_ago = now - 3600

    item = auth_table.get_item(Key={"email": email}).get("Item", {})
    otp_sends = item.get("otp_sends", [])
    recent = [int(ts) for ts in otp_sends if int(ts) > one_hour_ago]

    if len(recent) >= MAX_OTP_PER_HOUR:
        return False, len(recent)

    recent.append(now)
    auth_table.update_item(
        Key={"email": email},
        UpdateExpression="SET otp_sends = :sends, #ttl = :ttl",
        ExpressionAttributeNames={"#ttl": "ttl"},
        ExpressionAttributeValues={
            ":sends": recent,
            ":ttl": now + 7200,
        },
    )
    return True, len(recent)


def _store_auth_state(email, password, status):
    now = int(time.time())
    auth_table.update_item(
        Key={"email": email},
        UpdateExpression="SET temp_password = :pw, #s = :status, #ttl = :ttl",
        ExpressionAttributeNames={"#s": "status", "#ttl": "ttl"},
        ExpressionAttributeValues={
            ":pw": password,
            ":status": status,
            ":ttl": now + 7200,
        },
    )


def _generate_password():
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(chars) for _ in range(32))


def resp(status_code, body):
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
