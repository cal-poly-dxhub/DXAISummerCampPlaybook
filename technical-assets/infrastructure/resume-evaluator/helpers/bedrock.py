import json
import os
import time
from typing import Any

from dotenv import load_dotenv

load_dotenv()


import boto3

# 3.5 sonnet for batch (3.7 is not available in batch)
llm_model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"

client = boto3.client(  # type: ignore
    "bedrock-runtime",
    region_name="us-west-2",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    # config=boto3.config.Config(retries={"max_attempts": 10}),  # type: ignore
)
bedrock = boto3.client(  # type: ignore
    "bedrock",
    region_name="us-west-2",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    # config=boto3.config.Config(retries={"max_attempts": 10}),  # type: ignore
)


def test_bedrock():
    aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_session_token = (os.getenv("AWS_SESSION_TOKEN"),)
    print("aws_access_key_id:", aws_access_key_id)
    print("aws_secret_access_key:", aws_secret_access_key)
    print("aws_session_token:", aws_session_token)
    response = bedrock.list_foundation_models()  # type: ignore
    summarries = response["modelSummaries"]  # type: ignore
    for model in summarries:  # type: ignore
        print(model["modelName"], "| model id:", model["modelId"])  # type: ignore


def invoke_llm(body: Any, modelId: str = llm_model_id, retries: int = 0) -> Any:
    # print("invoking llm, retries:", retries)
    try:
        return client.invoke_model(modelId=modelId, body=body)  # type: ignore
    except Exception as e:
        if "(ThrottlingException)" in str(e) and retries < 3:
            time.sleep((retries + 1) * 8)
            return invoke_llm(
                body,
                modelId,
                retries + 1,
            )
        print(e)
        exit(1)


if __name__ == "__main__":
    # test_bedrock()
    test_prompt: Any = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "tell me a joke",
                    }
                ],
            }
        ],
    }

    serialized_prompt = json.dumps(test_prompt)

    response = invoke_llm(
        serialized_prompt, modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    )

    response_body = response["body"].read().decode("utf-8")

    print("response:", response_body)  # type: ignore
