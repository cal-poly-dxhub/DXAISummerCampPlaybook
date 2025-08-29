from typing import List, Literal
from pydantic import BaseModel, Field
from utils import create_bedrock_client, retry_with_backoff
import json


class MovieReview(BaseModel):
    """Model for extracting movie review sentiment and details"""

    title: str = Field(description="Movie title")
    sentiment: Literal["Positive", "Negative", "Neutral"] = Field(
        description="Overall sentiment"
    )
    rating: float = Field(ge=1.0, le=10.0, description="Rating out of 10")  # type: ignore
    key_points: List[str] = Field(description="Main points mentioned in review")


@retry_with_backoff
def basic_extraction_example():
    """
    Introduce automated extraction of structured data from unstructured prose.
    """
    print("\n=== Example 1: Basic Structured Extraction ===")

    client = create_bedrock_client()

    # TODO: Add to the fields you'd like to extract or change the review text to see
    # how the output changes.

    review_text = """
    I watched The Matrix last night and wow! The special effects were groundbreaking 
    for 1999, and Keanu Reeves delivered a solid performance. The philosophical themes 
    about reality and choice really made me think. The action sequences were incredible, 
    especially the bullet-time effects. I'd give it a 9/10 - definitely a must-watch!
    """

    # Clear, specific instruction with context
    prompt = f"""
    Analyze this movie review and extract key information:
    
    Review: {review_text}
    """  # No tedious specification of fields necessary!

    try:
        result = client.chat.completions.create(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.1,  # Low temperature for consistent extraction
            response_model=MovieReview,
        )

        print(f"Movie: {result.title}")
        print(f"Sentiment: {result.sentiment}")
        print(f"Rating: {result.rating}/10")
        print(f"Key Points: {', '.join(result.key_points)}")

        print()

        print("Represented as JSON:")
        print(json.dumps(result.model_dump(), indent=2))

        return result

    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    basic_extraction_example()
