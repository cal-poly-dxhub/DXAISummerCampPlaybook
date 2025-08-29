from typing import List
from pydantic import BaseModel, Field
from utils import create_bedrock_client, retry_with_backoff


class MathSolution(BaseModel):
    """Model for step-by-step math problem solving"""

    problem: str = Field(description="The original problem")
    steps: List[str] = Field(
        description="Steps taken to reason through the problem information and solution strategy (not math calculations)"
    )
    calculations: List[str] = Field(
        description="The calculations made to arrive at the final answer"
    )
    final_answer: str = Field(description="Final numerical answer with units")


@retry_with_backoff
def chain_of_thought_example():
    """
    Encourage a model to express its reasoning, increasing the changes of a logically sound response.
    """
    print("\n=== Example 3: Chain of Thought Reasoning ===")

    client = create_bedrock_client()

    math_problem = """
    A company's revenue increased by 15% in Q1, then decreased by 8% in Q2, 
    and finally increased by 12% in Q3. If their starting revenue was $500,000, 
    what was their revenue at the end of Q3?
    """

    # TODO: give the model some steps you'd like to see it take to arrive
    # at a conclusion. What reasoning process might improve your chances
    # of success?

    # Prompt explicitly asking for step-by-step thinking
    prompt = f"""
    Solve this business math problem step by step. Show your reasoning clearly:
    
    Problem: {math_problem}
    
    Think through this systematically:
    
    Be precise with calculations and show intermediate results.
    """

    try:
        result = client.chat.completions.create(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1200,
            temperature=0.1,  # Low temperature for mathematical accuracy
            response_model=MathSolution,
        )  # type: ignore

        print("Reasoning:")
        for i, step in enumerate(result.steps, 1):
            print(f"{i}. {step}")

        print("\nSolution Steps:")
        for i, step in enumerate(result.calculations, 1):
            print(f"{i}. {step}")
        print(f"\nFinal Answer: {result.final_answer}")
        return result

    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    chain_of_thought_example()
