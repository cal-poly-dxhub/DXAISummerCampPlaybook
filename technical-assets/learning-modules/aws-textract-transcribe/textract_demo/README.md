# Cal Poly AI Summer Camp: AWS Textract Demo
Welcome to our AI Summer Camp project! This demo walks you through how to extract text and structured data from scanned documents using **Amazon Textract**.

You'll learn how to:
- Detect raw text from PDFs/images
- Analyze forms and tables
- Run custom queries using natural language
- Process real-world PDFs with just a few lines of Python

## Contact Information
Instructor: Dhvani Goel - dhgoel@calpoly.edu

## Prerequisites
Ensure your AWS account has access to:
- `textract:AnalyzeDocument`
- `textract:DetectDocumentText`
- `s3:*` (for future S3 integration)
- Optional: `textract:AnalyzeDocumentWithAdapter` if using custom queries with adapters

You should also have:
- Python 3.7+
- AWS CLI configured
- Boto3 installed (`pip install boto3`)

## What You'll Learn
Goal: Extract data from documents using multiple Textract features

- How to extract plain text using `DetectDocumentText`
- How to extract key-value pairs and tables using `AnalyzeDocument`
- How to ask natural-language questions with **Textract Custom Queries**
- How to structure outputs for processing or automation

## Getting Started

Follow these steps in order:

### 1. Clone the Repository
```bash
git clone https://github.com/cal-poly-dxhub/aws-textract-transcribe.git
cd aws-textract-transcribe
cd textract_demo
```

### 2. Create a Virtual Environment

For macOS/Linux:
```bash
python -m venv venv
source venv/bin/activate
```

For Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Required Packages

```bash
pip install -r requirements.txt
```

## How to Run Each Script

### Raw Text Detection

```bash
python scripts/detect_text.py
```
- Uses detect_document_text
- Outputs all lines of printed or handwritten text
- Best for simple OCR use cases

### Forms + Tables Extraction

```bash
python scripts/analyze_forms_tables.py
```
- Uses analyze_document with FeatureTypes=['FORMS', 'TABLES']
- Extracts key-value pairs from forms and cell-by-cell data from tables
- Great for structured documents

### Custom Queries with Adapter

```bash
python scripts/custom_queries.py
```
- Uses analyze_document with FeatureTypes=['QUERIES']
- Asks questions like: “Who is the grantor?”, “What county is the property located in?”
- Reads adapter ID from adapter.config
