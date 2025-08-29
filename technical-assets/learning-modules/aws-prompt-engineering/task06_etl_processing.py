from typing import List, Optional
from pydantic import BaseModel, Field
from utils import create_bedrock_client, retry_with_backoff, extract_text_from_pdf


class ProcessedPaper(BaseModel):
    """
    TODO: define the outputs you want to extract from the paper here,
    using components of old PyDantic models.
    """


@retry_with_backoff
def etl_processing_example():
    """
    Process a PDF start to finish and declaratively define the output you want.
    """
    print("\n=== Example 5: ETL Data Processing ===")

    client = create_bedrock_client()

    # TODO: download a PDF you want to extract text from and point to it
    # using its path here.
    pdf_text = extract_text_from_pdf(pdf_file_path="")

    # TODO: define your extraction prompt here!
    prompt = None

    try:
        result = client.chat.completions.create(
            modelId="anthropic.claude-3-5-sonnet-20241022-v2:0",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.5,  # Balanced temperature for processing
            response_model=ProcessedPaper,
        )  # type: ignore

        with open("procesed_paper.json", "w") as f:
            f.write(result.model_dump_json(indent=2))

        return result

    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    etl_processing_example()
