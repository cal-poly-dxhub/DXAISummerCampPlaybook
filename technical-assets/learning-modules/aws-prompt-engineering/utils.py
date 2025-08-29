import boto3
import time
from typing import List, Literal, Dict, Optional
from pydantic import BaseModel, Field
import pdfplumber
import instructor


def create_bedrock_client():
    """Create an instructor-wrapped Bedrock client for structured outputs"""
    bedrock_client = boto3.client("bedrock-runtime", region_name="us-west-2")
    return instructor.from_bedrock(bedrock_client)


def retry_with_backoff(func, max_retries=3):
    """Decorator to handle API throttling with exponential backoff"""

    def wrapper(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if "(ThrottlingException)" in str(e) and attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    print(f"Rate limited. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue
                raise e

    return wrapper


def extract_text_from_pdf(pdf_file_path: str) -> str:
    """Extract text from PDF using pdfplumber"""
    print(f"Extracting text from {pdf_file_path}...")

    extracted_text = ""
    with pdfplumber.open(pdf_file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                extracted_text += text + "\n"
    return extracted_text
