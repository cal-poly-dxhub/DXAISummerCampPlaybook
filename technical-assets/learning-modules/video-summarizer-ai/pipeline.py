import boto3
import time
import json
from tqdm.auto import tqdm
import uuid


# === CONFIG ===
REGION = "us-west-2"
BUCKET = "rag-ingest-data-test"
OBJECT_KEY = "summer_camp_rickroll.mp4"


# Generate a random job name
short_id = str(uuid.uuid4())[:4]
JOB_NAME = f"transcription-{short_id}"
TRANSCRIPT_JSON_KEY = f"{JOB_NAME}.json"




def main():
   transcribe = boto3.client("transcribe", region_name=REGION)
   s3 = boto3.client("s3", region_name=REGION)
   bedrock = boto3.client("bedrock-runtime", region_name=REGION)


   s3_uri = f"s3://{BUCKET}/{OBJECT_KEY}"


   # === STEP 1: Start Transcription ===
   try:
       transcribe.start_transcription_job(
           TranscriptionJobName=JOB_NAME,
           Media={"MediaFileUri": s3_uri},
           MediaFormat=OBJECT_KEY.split(".")[-1],
           LanguageCode="en-US",
           OutputBucketName=BUCKET,
       )
       print(f"[-->] Started new transcription job: {JOB_NAME}")
   except transcribe.exceptions.ConflictException:
       print(f"[!] Job {JOB_NAME} already exists. Using it...")


   # === STEP 2: Wait for Completion ===
   print("[...] Waiting for transcription to complete...")


   with tqdm(
       desc="Transcribing", bar_format="{desc} |{bar}| {elapsed} elapsed", ncols=80
   ) as pbar:
       while True:
           job = transcribe.get_transcription_job(TranscriptionJobName=JOB_NAME)
           status = job["TranscriptionJob"]["TranscriptionJobStatus"]


           if status in ["COMPLETED", "FAILED"]:
               pbar.set_description(f"Job {status}")
               break


           time.sleep(5)
           pbar.update(1)


   # === STEP 3: Read Transcript from S3 ===
   if status == "COMPLETED":
       obj = s3.get_object(Bucket=BUCKET, Key=TRANSCRIPT_JSON_KEY)
       data = json.loads(obj["Body"].read())
       transcript = data["results"]["transcripts"][0]["transcript"]
       print("\n[<>] Transcript Preview:\n", transcript[:1000], "...\n")


       # === STEP 4: Summarize via Bedrock ===
       prompt = (
           "\n\nHuman: Summarize the following transcript, what is being said in the video, make a quick summary about the song? "
           "what is the most used sentence in this passage. "
           "Include bullet points (number the bullet points starting with 1) "
           "and have at least 5, but no more than 7, total bullet points. "
           "Label each bullet point with a numerical value:\n"
           f"{transcript}\n\nAssistant:"
       )


       response = bedrock.invoke_model(
           modelId="anthropic.claude-v2",
           contentType="application/json",
           accept="application/json",
           body=json.dumps({"prompt": prompt, "max_tokens_to_sample": 10000}),
       )


       result = json.loads(response["body"].read())
       print("[#] Summary:\n", result.get("completion", result))


   else:
       print("[X] Transcription job failed.")




if __name__ == "__main__":
   main()



