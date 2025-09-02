import base64
import json
import os
from io import BytesIO
from typing import Any

import boto3
from dotenv import load_dotenv
from lxml import etree  # type: ignore
from pdf2image import convert_from_path  # type: ignore

from helpers.bedrock import llm_model_id
from helpers.s3 import upload_file_to_s3

load_dotenv()

# VALUES TO CHANGE: jsonl file name and batch job name
input_jsonl_file_name = "resume_evaluation_batch_4.jsonl"
batch_job_name = "resume-eval-batch-4"

# --

aws_account_id = os.environ.get("AWS_ACCOUNT_ID")
role_arn = os.environ.get("BATCH_ROLE_ARN")
batch_bucket_name = "resume-evaluator-batch"


batch_client = boto3.client(  # type: ignore
    "bedrock",  # type: ignore
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
)

input_data_config = {"s3InputDataConfig": {"s3Uri": f"s3://{batch_bucket_name}/"}}
output_data_config = {
    "s3OutputDataConfig": {"s3Uri": f"s3://{batch_bucket_name}/"},
}

if not os.path.exists("assets/SimpleResume/XMLPrompt.md") or not os.path.exists(
    "assets/SimpleResume/SimpleResume.xml"
):
    print("prompts not found")
    exit(1)

prompt = open("assets/SimpleResume/XMLPrompt.md").read()
xml = open("assets/SimpleResume/SimpleResume.xml").read()


# fetch all images base64 from files from id
def fetch_pdf_base64(id: int) -> list[str]:
    """
    Convert all PDFs in 'rows/{id}' to JPEGs, then return all images as base64 strings.
    """
    files = os.listdir(f"rows/{id}")
    pdfs = [f for f in files if f.endswith(".pdf")]
    b64: list[str] = []

    for pdf in pdfs:
        images = convert_from_path(f"rows/{id}/{pdf}")
        for image in images:
            buffer = BytesIO()
            image.save(buffer, format="JPEG")
            buffer.seek(0)
            b64_image = base64.b64encode(buffer.read()).decode("utf-8")
            b64.append(b64_image)

    return b64


def get_image_template(data: str) -> dict[str, Any]:
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/jpeg",
            "data": data,
        },
    }


def get_body_template(id: int) -> dict[str, Any]:
    t: str = prompt.replace("[input-xml-here]", xml)

    transcript1 = None
    transcript2 = None

    # check for transcripts
    if os.path.exists(f"rows/{id}/supplemental_transcript1.txt"):
        transcript1 = open(f"rows/{id}/supplemental_transcript1.txt").read()
    if os.path.exists(f"rows/{id}/supplemental_transcript2.txt"):
        transcript2 = open(f"rows/{id}/supplemental_transcript2.txt").read()

    if transcript1 is not None or transcript2 is not None:
        t += "\n\n**Youtube Transcript Supplemental Participant Info:**\n\n"
    if transcript1 is not None:
        t += f"{transcript1}\n\n"
    if transcript2 is not None:
        t += transcript2

    return {
        "recordId": f"evaluate-participant-{id}",
        "modelInput": {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 3072,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": t},
                    ],
                }
            ],
        },
    }


if __name__ == "__main__":
    # clear jsonl
    open(input_jsonl_file_name, "w").write("")

    for id in os.listdir("rows/"):
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
        body = get_body_template(id)
        images = fetch_pdf_base64(id)
        for im in images:
            body["modelInput"]["messages"][0]["content"].append(get_image_template(im))

        with open(input_jsonl_file_name, "a") as f:
            json.dump(body, f)
            f.write("\n")

    # upload file to s3
    input_file = upload_file_to_s3(input_jsonl_file_name, batch_bucket_name)

    # start batch transform job
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
