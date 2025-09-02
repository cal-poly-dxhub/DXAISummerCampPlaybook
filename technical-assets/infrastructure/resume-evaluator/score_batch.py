import json
import os
from typing import Any

from helpers.bedrock import llm_model_id
from helpers.s3 import upload_file_to_s3

# VALUES TO CHANGE: jsonl file name and batch job name
input_jsonl_file_name = "resume_scorer_batch_1.jsonl"
batch_job_name = "resume-scorer-batch-1"

# --

aws_account_id = os.environ.get("AWS_ACCOUNT_ID")
role_arn = os.environ.get("BATCH_ROLE_ARN")
batch_bucket_name = "resume-scorer-batch"

input_data_config = {"s3InputDataConfig": {"s3Uri": f"s3://{batch_bucket_name}/"}}
output_data_config = {
    "s3OutputDataConfig": {"s3Uri": f"s3://{batch_bucket_name}/"},
}

if not os.path.exists("assets/Scoring/ScorePrompt.md"):
    print("prompt not found")
    exit(1)

prompt = open("assets/Scoring/ScorePrompt.md", "r").read()


def build_llm_body(id: int, temp: float) -> dict[str, Any]:
    with open(f"simpleResumes/{id}.xml", "r", encoding="utf-8") as f:
        simple_resume = f.read()
        return {
            "recordId": f"score-participant-{id}",
            "modelInput": {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 3072,
                "temperature": temp,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt.replace(
                                    "[input-xml-here]", simple_resume
                                ),
                            }
                        ],
                    }
                ],
            },
        }


if __name__ == "__main__":
    # clear jsonl
    open(input_jsonl_file_name, "w").write("")

    for id in os.listdir("simpleResumes/"):
        if not id.isdigit():
            print(f"skipping {id} (not a number)")
            continue

        id = int(id)

        # skip id if it fails in a run
        bad_ids = []
        if id in bad_ids:
            print(f"skipping {id} (bad id)")
            continue

        print(f"processing participant {id}")

        temps = [0.0, 0.1, 0.2]
        for temp in temps:
            body = build_llm_body(id, temp)
            with open(input_jsonl_file_name, "a") as f:
                json.dump(body, f)
                f.write("\n")

    # upload file to s3
    input_file = upload_file_to_s3(input_jsonl_file_name, batch_bucket_name)

    # start batch job
    response = batch_client.create_model_invocation_job(  # type: ignore
        modelId=llm_model_id,
        inputDataConfig=input_data_config,
        outputDataConfig=output_data_config,
        jobName=batch_job_name,
        roleArn=role_arn,
    )

    job_arn = response.get("jobArn")  # type: ignore
    print(f"batch job started: {job_arn}")
    print(batch_client.get_model_invocation_job(jobIdentifier=job_arn)["status"])  # type: ignore
