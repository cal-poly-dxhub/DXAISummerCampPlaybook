from typing import List, Literal
from pydantic import BaseModel, Field
from utils import create_bedrock_client, retry_with_backoff


class EmailClassification(BaseModel):
    """Model for email classification with confidence scores"""

    category: Literal["Spam", "Important", "Personal", "Work", "Promotional"] = Field(
        description="Primary email category"
    )
    reasoning: str = Field(description="Brief explanation of classification")
    urgency: Literal["Low", "Medium", "High"] = Field(description="Urgency level")


@retry_with_backoff
def few_shot_classification_example():
    """
    Give a model a small number of examples to derive a pattern.
    """

    print("\n=== Example 2: Few-Shot Email Classification ===")

    client = create_bedrock_client()

    # Example emails to classify
    test_email = """
    Subject: URGENT: System maintenance tonight
    From: it-team@company.com
    
    IT Team
    """

    # TODO: give the model a few examples of "right answers". Try changing the input emails.
    # What examples might help cover some edge cases?

    # Few-shot prompt with clear examples
    prompt = f"""
    Classify emails into categories based on these examples:
    
    EXAMPLES:
    Now classify this email:
    {test_email}
    """

    try:
        result = client.chat.completions.create(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.2,
            response_model=EmailClassification,
        )  # type: ignore

        print(f"Category: {result.category}")
        print(f"Urgency: {result.urgency}")
        print(f"Reasoning: {result.reasoning}")
        return result

    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    few_shot_classification_example()
