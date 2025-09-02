import base64
import json
import os
from io import BytesIO
from typing import Any

import boto3
from dotenv import load_dotenv
from lxml import etree  # type: ignore
from pdf2image import convert_from_path  # type: ignore

from simple_resume_batch_postprocess import str_to_xml

load_dotenv()


modelId = "anthropic.claude-3-5-sonnet-20241022-v2:0"


bedrock_client = boto3.client(  # type: ignore
    "bedrock-runtime",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    aws_session_token=os.getenv("AWS_SESSION_TOKEN"),
)


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
    }


# for all ids that failed in the batch
# max total files size is 5mb
# max total documents is 20
ids: list[int] = [0]
if __name__ == "__main__":
    for id in ids:
        try:
            print(f"processing participant: {id}")
            body = get_body_template(id)
            images = fetch_pdf_base64(id)
            for im in images:
                body["messages"][0]["content"].append(get_image_template(im))

            response = bedrock_client.invoke_model(  # type: ignore
                modelId=modelId,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )

            data = json.loads(response["body"].read().decode("utf-8"))  # type: ignore
            print(data["content"][0]["text"])
            text = data["content"][0]["text"]
            str_to_xml(id, text)
        except KeyError as e:
            print(f"KeyError: {e} in id {id}")
