import boto3
import time
import json
import uuid
from tqdm.auto import tqdm


REGION = "us-east-2"
# CHANGE THIS TO YOUR BUCKET NAME!
BUCKET = "transcribe-example-sharon"
# FEEL FREE TO CHANGE THESE VIDS BY ADDING YOUR OWN!
FILES = {
    "basic": "transcribe.mp4",
    "speakers": "911_call.mp3",
    "auto_lang": "spanish_podcast.mp3",
}

def wait_for_job(transcribe, job_name):
    print(f"[...] Waiting for {job_name} to complete...")
    with tqdm(desc="Transcribing", ncols=80) as pbar:
        while True:
            job = transcribe.get_transcription_job(TranscriptionJobName=job_name)
            status = job["TranscriptionJob"]["TranscriptionJobStatus"]
            if status in ["COMPLETED", "FAILED"]:
                pbar.set_description(f"Job {status}")
                break
            time.sleep(5)
            pbar.update(1)
    return status


def print_transcript_from_s3(s3, bucket, key, show_speakers=False):
    obj = s3.get_object(Bucket=bucket, Key=key)
    data = json.loads(obj["Body"].read())
    if show_speakers:
        items = data["results"]["items"]
        segments = data["results"].get("speaker_labels", {}).get("segments", [])
        for seg in segments:
            speaker = seg["speaker_label"]
            words = [w["alternatives"][0]["content"]
                     for w in items
                     if w["type"] == "pronunciation"
                     and float(seg["start_time"]) <= float(w["start_time"]) <= float(seg["end_time"])]
            print(f"{speaker}: {' '.join(words)}")
    else:
        # print("\n[<>] Transcript:\n", data["results"]["transcripts"][0]["transcript"], "...\n")
        print("\n[<>] Transcript Preview:\n", data["results"]["transcripts"][0]["transcript"][:1000], "...\n")


def run_demo(mode):
    transcribe = boto3.client("transcribe", region_name=REGION)
    s3 = boto3.client("s3", region_name=REGION)
    job_id = f"{mode}-demo-{str(uuid.uuid4())[:5]}"
    file_key = FILES[mode]
    s3_uri = f"s3://{BUCKET}/{file_key}"
    output_key = f"{job_id}.json"

    print(f"\n=== DEMO MODE: {mode.upper()} ===")
    print(f"[-->] File: {file_key}\n[-->] Job: {job_id}")

    if mode == "basic":
        transcribe.start_transcription_job(
            TranscriptionJobName=job_id,
            Media={"MediaFileUri": s3_uri},
            MediaFormat="mp4",
            LanguageCode="en-US",
            OutputBucketName=BUCKET,
        )

    elif mode == "speakers":
        transcribe.start_transcription_job(
            TranscriptionJobName=job_id,
            Media={"MediaFileUri": s3_uri},
            MediaFormat="mp4",
            LanguageCode="en-US",
            OutputBucketName=BUCKET,
            Settings={
                "ShowSpeakerLabels": True,
                "MaxSpeakerLabels": 3,
            },
        )

    elif mode == "auto_lang":
        transcribe.start_transcription_job(
            TranscriptionJobName=job_id,
            Media={"MediaFileUri": s3_uri},
            MediaFormat="mp4",
            # two options here!
            # - 1. let transcribe identify the languge
            IdentifyLanguage=True,
            # - 2. manually add in the language
            # LanguageCode="es-US",
            OutputBucketName=BUCKET,
        )

    else:
        print("[X] Unknown mode.")
        return

    status = wait_for_job(transcribe, job_id)

    if status == "COMPLETED":
        show_speakers = (mode == "speakers")
        print_transcript_from_s3(s3, BUCKET, output_key, show_speakers=show_speakers)
    else:
        print("[X] Transcription failed.")


if __name__ == "__main__":
    for mode in FILES.keys():
        run_demo(mode)
