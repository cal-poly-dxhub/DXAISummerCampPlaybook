from typing import List
from pydantic import BaseModel, Field
from utils import create_bedrock_client, retry_with_backoff


class TechnicalExplanation(BaseModel):
    """Model for technical explanations with different complexity levels"""

    topic: str = Field(description="The technical topic being explained")
    complexity_level: str = Field(description="Target audience complexity level")
    explanation: str = Field(description="Main explanation content")
    key_concepts: List[str] = Field(description="Important concepts covered")
    practical_examples: List[str] = Field(description="Real-world examples")
    next_steps: str = Field(description="Suggested next learning steps")


@retry_with_backoff
def advanced_prompt_with_flags_example():
    """
    Example 6: Advanced prompting with flags and context control
    Shows how to use flags to control AI behavior and output style
    """
    print("\n=== Example 6: Advanced Prompting with Flags ===")

    client = create_bedrock_client()

    topic = "machine learning"
    audience = "college students new to programming"

    # Advanced prompt with multiple flags and context
    prompt = f"""
    [FLAG: EDUCATIONAL_CONTENT]
    [FLAG: BEGINNER_FRIENDLY]
    [FLAG: INCLUDE_EXAMPLES]
    [FLAG: PRACTICAL_FOCUS]
    [FLAG: ENCOURAGE_LEARNING]
    
    Context: You are an experienced computer science professor explaining to {audience}.
    
    Task: Explain {topic} in an engaging, accessible way.
    
    Guidelines:
    - Use analogies and real-world examples
    - Avoid overwhelming technical jargon
    - Focus on practical applications
    - Encourage further exploration
    - Make it relevant to student life
    
    Topic to explain: {topic}
    
    Structure your explanation to build understanding progressively.
    """

    try:
        result = client.chat.completions.create(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.5,  # Balanced for educational content
            response_model=TechnicalExplanation,
        )

        print(f"Topic: {result.topic}")
        print(f"Level: {result.complexity_level}")
        print(f"\nExplanation:\n{result.explanation}")
        print(f"\nKey Concepts:")
        for concept in result.key_concepts:
            print(f"• {concept}")
        print(f"\nPractical Examples:")
        for example in result.practical_examples:
            print(f"• {example}")
        print(f"\nNext Steps: {result.next_steps}")

        return result

    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    advanced_prompt_with_flags_example()
