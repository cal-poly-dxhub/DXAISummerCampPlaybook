import boto3
from utils import retry_with_backoff


@retry_with_backoff
def test_dials_and_parameters():
    """
    Introduce the main API call we'll be using.
    """
    print("\n=== Testing Dials and Parameters ===")

    client = boto3.client("bedrock-runtime", region_name="us-west-2")

    # TODO: change the prompt and some settings to get an understanding of how the API works.

    # Pre-prepared prompt for testing
    prompt = """You are a helpful AI assistant. Please provide a creative and engaging response to the following question:

Question: What are three innovative ways that artificial intelligence could help solve climate change in the next decade?

Please structure your response with clear bullet points and keep it concise but informative."""

    try:
        result = client.converse(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            messages=[{"role": "user", "content": [{"text": prompt}]}],
            inferenceConfig={
                "temperature": 0.8,  # Higher temperature for more creative responses
                "topP": 0.9,  # Top-p sampling for controlled randomness
                "maxTokens": 500,  # Limit response length
                "stopSequences": ["<END>", "###"],
            },
        )

        print(f"Response: {result['output']['message']['content'][0]['text']}")
        return result

    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    test_dials_and_parameters()
