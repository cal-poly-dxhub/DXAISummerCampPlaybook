# resume-evaluator

## setup

### aws resources

- s3 buckets
  - `resume-evaluator-participant-files`

### virtual environment

```bash
python3.9 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### credentials

- create a `.env` file

```bash
cp .env.example .env
```

- fill in the `.env` file with your AWS credentials and other required environment variables
  - to create an `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`, IAM --> Users --> your user --> Security Credentials --> Programmatic access (CLI)

### fetch all form data and do programatic matching

```bash
python load_from_cognito.py
```

- this will fetch all the data, files, youtube transcripts from the general form and supplemental form
- it will then match the data between the two forms
- any supplemental form that does not have a matching general form will end up in the `unmatched` folder

### do manual matching

- manually match the data in the `unmatched` folder

### compile images and run batch job

- define batch job name and jsonl file name in `simple_resume_batch.py`
- once all data is matched into `rows/` folder, run the batch job to compile images and generate the final output

```bash
python simple_resume_batch.py
```

### download the simple resume batch output

- download the batch output from S3 to the root folder of this project

### postprocess batch simple resume creation

- run the post batch XML creation script to generate the final simple resume XML files
- all simple resume XML files with metadata will be saved in `simpleResumes/` folder

```bash
python simple_resume_batch_postprocess.py
```

### run the scoring batch

- define batch job name and jsonl file name in `score_batch.py`
- run the scoring batch job

```bash
python score_batch.py
```

### download the scoring batch output

- download the batch output from S3 to the root folder of this project

### postprocess scoring batch output

- run the post batch scoring to generate the final scoring csv
