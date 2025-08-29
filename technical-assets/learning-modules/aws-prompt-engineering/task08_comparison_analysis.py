from typing import List, Dict
from pydantic import BaseModel, Field
from utils import create_bedrock_client, retry_with_backoff


class ProductComparison(BaseModel):
    """Model for comparing products or services"""

    items_compared: List[str] = Field(description="Items being compared")
    comparison_criteria: List[str] = Field(description="Criteria used for comparison")
    detailed_analysis: Dict[str, Dict[str, str]] = Field(
        description="Detailed analysis for each item across criteria"
    )
    recommendation: str = Field(description="Overall recommendation based on analysis")
    best_for_scenarios: Dict[str, str] = Field(
        description="Which option is best for different use cases"
    )


@retry_with_backoff
def comparison_analysis_example():
    """
    Example 7: Tree of thought for complex comparisons
    Shows how to get structured comparative analysis
    """
    print("\n=== Example 7: Comparative Analysis ===")

    client = create_bedrock_client()

    # Complex comparison prompt
    prompt = """
    Compare these three programming languages for college students learning their first language:
    1. Python
    2. JavaScript  
    3. Java
    
    Analyze them across these criteria:
    - Learning curve and beginner-friendliness
    - Job market opportunities
    - Versatility and use cases
    - Community support and resources
    - Long-term career prospects
    
    Consider multiple perspectives:
    - Academic learning environment
    - Industry requirements
    - Personal project possibilities
    - Future technology trends
    
    Provide a nuanced analysis that acknowledges trade-offs and different student goals.
    Include specific recommendations for different scenarios.
    """

    try:
        result = client.chat.completions.create(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2500,
            temperature=0.4,  # Balanced for analytical thinking
            response_model=ProductComparison,
        )

        print("Programming Language Comparison for College Students")
        print("=" * 55)
        print(f"Languages: {', '.join(result.items_compared)}")
        print(f"Criteria: {', '.join(result.comparison_criteria)}")

        print("\nDetailed Analysis:")
        for item, analysis in result.detailed_analysis.items():
            print(f"\n{item.upper()}:")
            for criterion, assessment in analysis.items():
                print(f"  • {criterion}: {assessment}")

        print(f"\nRecommendation:\n{result.recommendation}")

        print("\nBest For Different Scenarios:")
        for scenario, choice in result.best_for_scenarios.items():
            print(f"• {scenario}: {choice}")

        return result

    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    comparison_analysis_example()
