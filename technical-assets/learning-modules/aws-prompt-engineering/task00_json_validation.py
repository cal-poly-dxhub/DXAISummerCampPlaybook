from typing import List, Literal
from pydantic import field_validator, BaseModel, Field, EmailStr
import json
from utils import retry_with_backoff


class UserProfile(BaseModel):
    """
    Introduce PyDantic models and the notion of data validation.
    """

    user_id: str = Field(
        description="User ID - must be under 32 chars, lowercase and dashes only"
    )
    age: int = Field(ge=13, le=120, description="User age between 13 and 120")
    email: EmailStr = Field(description="Valid email address")
    preferences: List[str] = Field(description="User preferences list")
    status: Literal["active", "inactive", "pending"] = Field(
        description="Account status"
    )

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v):
        if len(v) >= 32:
            raise ValueError("User ID must be under 32 characters")
        if not v.replace("-", "").islower():
            raise ValueError("User ID must contain only lowercase letters and dashes")
        return v


@retry_with_backoff
def json_validation_example():
    """
    Example 0: JSON parsing and Pydantic validation with intentional failures
    Demonstrates JSON string creation, parsing, and validation errors
    """
    print("\n=== Example 0: JSON Validation with Intentional Failures ===")

    # Create a JSON string with intentional validation issues
    json_string = """
    {
        "user_id": "USER-123-TOO-LONG-USERNAME-THAT-EXCEEDS-32-CHARS",
        "age": 150,
        "preferences": ["reading", "gaming", "cooking"],
        "email": "invalid-email",
        "status": "active"
    }
    """

    # TODO: why doesn't the model validate this JSON object?

    print("Original JSON string:")
    print(json_string)

    # Parse JSON string as dictionary
    try:
        parsed_dict = json.loads(json_string)
        print(f"\nParsed dictionary: {parsed_dict}")
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        return None

    # Attempt to validate with Pydantic model (should fail)
    print("\nAttempting Pydantic validation...")
    try:
        validated_profile = UserProfile(**parsed_dict)
        print("✅ Validation successful!")
        print(f"Validated profile: {validated_profile}")
        return validated_profile
    except Exception as e:
        print("❌ Validation failed!")
        print(f"Validation error: {e}")

        return None


if __name__ == "__main__":
    json_validation_example()
