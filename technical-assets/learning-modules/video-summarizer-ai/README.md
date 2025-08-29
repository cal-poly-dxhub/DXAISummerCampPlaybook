# Cal Poly AI Summer Camp: Audio Transcription & Summarization Pipeline


Welcome to our AI Summer Camp project! This hands-on activity will teach you how to convert audio files into structured, easy-to-read summaries using **Amazon Transcribe** and **Amazon Bedrock**. You'll learn how to trigger and track transcription jobs, retrieve results, and generate bullet-point summaries using an LLM — all with Python and AWS.

Video Link Tutorial: https://drive.google.com/file/d/1UkFAlLpEo_sR_fUloA3mLRNMNUdhoEIf/view?usp=drive_link
## Contact


**Instructor**: Kartik Malunjkar kmalunjk@calpoly.edu


## Prerequisites
AWS CLI set up with proper credentials
IAM permissions for: (Navigate into IAM roleson AWS console and check for adminstrator access)
- transcribe:StartTranscriptionJob
- transcribe:GetTranscriptionJob
- s3:* for the relevant bucket
- bedrock:InvokeModel


## What You'll Learn
- Goal: Write scirpt to summarize a video based on your prompt
- How to launch transcription jobs with **Amazon Transcribe**
- How to read transcript results from an **S3 bucket**
- How to generate **summaries** using ** Claude v2** on teh video you uplaoded




## Getting Started


Follow these steps in order:


### 1. Clone the Repository


```bash
git clone https://github.com/cal-poly-dxhub/video-summarizer-ai.git


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


### 4. Run the Pipeline to summarize Video


```bash
python pipeline.py
```




This project demonstrates how to:
- Start a transcription job from an `.m4a` or `.mp3` file stored in S3
- Track the job's progress using a live progress bar
- Retrieve the raw transcript from S3 once complete
- Format a Bedrock prompt to generate 5–7 concise, numbered bullet points (can change the prompt)
- Display the summary in your terminal


## Common Issues


1. AWS Credentials & Permissions
Issue: AccessDenied, NoCredentialsError, copy paste temprary access keys into terminal
Fix: Run aws configure; ensure IAM role allows transcribe:*, bedrock:InvokeModel, s3:GetObject
2.  S3 File Access
Issue: Transcribe can't find or access your .mp4 or .mp3
Fix: Check file exists in S3, path is correct (s3://bucket/file), and object permissions allow access
3. Transcribe Input Validity
Issue: Unsupported format, silent/corrupt audio, or empty transcript
Fix: Use .mp3, .mp4, .mov, .wav with real spoken content; test with short, clean audio
6. Transcript URI Retrieval
Issue: Transcript link fails (403, expired, or empty)
Fix: Wait for job completion; check TranscriptFileUri manually; retry fetch if needed
5. Bedrock Model Call
Issue: Model not found, payload error, or too-long input
Fix: Use correct model ID (e.g., Claude 3); validate JSON structure; chunk long transcripts into smaller pieces


## Learn More
[Amazon Transcribe Documentation] — https://docs.aws.amazon.com/transcribe/latest/dg/what-is-transcribe.html
[StartTranscriptionJob API Reference] — https://docs.aws.amazon.com/transcribe/latest/dg/API_StartTranscriptionJob.html
[GitHub Example: AWS Transcribe Pipeline] — https://github.com/aws-samples/aws-transcribe-example



