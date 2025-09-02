import base64
import json
import os
from typing import Any, Union

import requests
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore

load_dotenv()

gid: str = os.getenv("COGNITO_GENERAL_FORM_ID")  # type: ignore
sid: str = os.getenv("COGNITO_SUPPLEMENTAL_FORM_ID")  # type: ignore
ytt_api = YouTubeTranscriptApi()


# fetch from cognito form
def fetch_cognito(url: str) -> Union[dict[str, Any], None]:
    """
    fetch from cognito form
    """
    headers: dict[str, str] = {
        "Authorization": "Bearer " + os.getenv("COGNITO_TOKEN"),  # type: ignore
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        data: dict[str, str] = response.json()
        return data
    except Exception as e:
        print(f"Error fetching row {id}: {e}")
        return None


# fetch row from cognito form
def fetch_row(form_id: int, row_id: int) -> Union[dict[str, Any], None]:
    """
    get an applicant row from cognito form
    """
    url: str = f'{os.getenv("COGNITO_BASE_URL")}/{form_id}/entries/{row_id}'

    response = fetch_cognito(url)
    return response


# fetch file from cognito form
def fetch_file(form_id: int, row_id: int, file_id: str) -> Union[bytes, None]:
    """
    get an applicant file from cognito form
    """
    url: str = (
        f'{os.getenv("COGNITO_BASE_URL")}/{form_id}/entries/{row_id}/files/{file_id}'  # type: ignore
    )

    response = fetch_cognito(url)
    if response is None:
        return None

    data = response["Content"]
    return base64.b64decode(data)


# fetch youtube transcripts from cognito form
def transcript_from_link(link: Union[str, None]) -> Union[str, None]:
    """
    get an applicant's youtube transcripts from youtube link
    """
    if link is None:
        return None

    print("youtube video present")
    if ".be/" in link:
        id = link.split(".be/")[1]
        transcript: list[dict[str, str]] = ytt_api.fetch(id).to_raw_data()  # type: ignore
        return (" ").join([t["text"] for t in transcript])
    elif "/watch?v=" in link:
        id = link.split("/watch?v=")[1]
        transcript: list[dict[str, str]] = ytt_api.fetch(id).to_raw_data()  # type: ignore
        return (" ").join([t["text"] for t in transcript])
    else:
        print("could not process link:", link)


# get metadata from general form json
def get_metadata(general_form: dict[str, Any]) -> dict[str, str]:
    """
    get metadata from general cognito form
    """
    metadata: dict[str, str] = {
        "id": general_form["Id"][3:],
        "timestamp": general_form["Entry"]["Timestamp"],
        "first": general_form["Name"]["First"],
        "last": general_form["Name"]["Last"],
        "middle": general_form["Name"]["Middle"],
        "middle_initial": general_form["Name"]["MiddleInitial"],
        "prefix": general_form["Name"]["Prefix"],
        "suffix": general_form["Name"]["Suffix"],
        "email": general_form["YourUniversityEmailAddressedu"],
        "phone": general_form["Phone"],
        "resume_id": general_form["PleaseUploadACopyOfYourResumeAsAPDFFile"][0]["Id"],
        "resume_name": general_form["PleaseUploadACopyOfYourResumeAsAPDFFile"][0][
            "Name"
        ],
        "major": general_form[
            "WhatAcademicMajorAreYouStudyingincludingAdditionalAcademicProgramsAsApplicable"
        ],
        "year": general_form[
            "HowManyYearsOfInstructionHaveYouCompletedmayIncludeTransferCredit"
        ],
        "of_age": general_form["WillYouBeAge18OrOlderOnJuly272025"],
    }
    return metadata


# load data and files from general form into rows/ and participants.csv
def load_general_rows() -> None:
    """
    load all rows and their files from the general form
    """
    latest_id: int = 0
    current_id: int = 0

    # TODO: never exits loop
    while current_id - 20 < latest_id:
        print(f"fetching general row {current_id}")

        # fetch row from general form
        response = fetch_row(int(gid), current_id)
        if response is not None:
            os.makedirs(f"rows/{current_id}", exist_ok=True)
            with open(f"rows/{current_id}/general.json", "w") as f:
                json.dump(response, f, indent=4)

            # download resume/cover letter from general
            files = response["PleaseUploadACopyOfYourResumeAsAPDFFile"]
            for i, file in enumerate(files):
                file_id = file["Id"]
                data = fetch_file(int(gid), current_id, file_id)
                if data is not None:
                    with open(f"rows/{current_id}/file_{i}.pdf", "wb") as f:
                        f.write(data)

            # get metadata
            metadata = get_metadata(response)
            with open(f"rows/{current_id}/metadata.json", "w") as f:
                json.dump(metadata, f, indent=4)

            # save metadata to csv
            with open("participants.csv", "a") as f:
                for key, value in metadata.items():
                    if key == "of_age":
                        f.write(f'"{value}"\n')
                    else:
                        f.write(f'"{value}",')

        latest_id = current_id
        current_id += 1


# load data and files from supplemental form form into supplemental/
def load_supplemental_rows() -> None:
    """
    load all rows from the supplemental form\n
    ***uses general form id***
    """
    latest_id: int = 0
    current_id: int = 0

    # TODO: never exits loop
    while current_id - 20 < latest_id:
        print(f"fetching supplemental row {current_id}")

        response = fetch_row(int(sid), current_id)
        if response is not None:
            os.makedirs(f"supplemental/{current_id}", exist_ok=True)

            # load metadata
            with open(f"supplemental/{current_id}/supplemental.json", "w") as f:
                json.dump(response, f, indent=4)

            # download files
            files = response[
                "SupportingDocumentationForYourProjectQuestionifApplicableInPDFFormat"
            ]
            for i, file in enumerate(files):
                file_id = file["Id"]
                data = fetch_file(int(sid), current_id, file_id)
                if data is not None:
                    with open(f"supplemental/{current_id}/file_{i}.pdf", "wb") as f:
                        f.write(data)

            # get youtube transcript 1
            t1 = transcript_from_link(response["YouTubeLink"])
            if t1 is not None:
                with open(f"supplemental/{current_id}/transcript1.txt", "w") as f:
                    f.write(t1)
            # get youtube transcript 2
            t2 = transcript_from_link(response["YouTubeLink2"])
            if t2 is not None:
                with open(f"supplemental/{current_id}/transcript2.txt", "w") as f:
                    f.write(t2)

        latest_id = current_id
        current_id += 1


def load_csv():
    csv_file = "participants.csv"
    folder_path = "rows"
    headers = [
        "id",
        "timestamp",
        "first",
        "last",
        "middle",
        "middle_initial",
        "prefix",
        "suffix",
        "email",
        "phone",
        "resume_id",
        "resume_name",
        "major",
        "year",
        "of_age",
    ]

    # Check if we need to write the header
    file_exists = os.path.isfile(csv_file)
    with open(csv_file, "a") as f:
        if not file_exists:
            f.write(",".join(headers) + "\n")

        for dir_name in os.listdir(folder_path):
            metadata_path = os.path.join(folder_path, dir_name, "metadata.json")
            if os.path.isfile(metadata_path):
                try:
                    with open(metadata_path, "r") as meta_file:
                        data = json.load(meta_file)
                    row = [str(data.get(h, "")).replace(",", " ") for h in headers]
                    f.write(",".join(row) + "\n")
                except Exception as e:
                    print(f"Skipping {metadata_path}: {e}")


# match rows from general and supplemental forms and move them to rows/
def match_rows() -> None:
    """
    match rows from general and supplemental forms
    """
    # load rows from csv
    # go through all folders in rows/ and add metadata to csv

    with open("participants.csv", "r") as f:
        lines = f.readlines()

    data = [
        [
            (int(value) if value.isdigit() else (None if value == "None" else value))
            for value in l.strip().replace('"', "").split(",")
        ]
        for l in lines
    ]

    # remove header
    data = data[1:]

    # load all supplemental data\
    supplemental_ids = [
        int(folder)
        for folder in os.listdir("supplemental/")
        if os.path.isdir(f"supplemental/{folder}")
    ]

    print(f"found {len(data)} general ids")
    print(f"found {len(supplemental_ids)} supplemental ids")

    for id in supplemental_ids:
        with open(f"supplemental/{id}/supplemental.json", "r") as f:
            supplemental = json.load(f)
            metadata = {
                "email": supplemental["YourUniversityEmailAddressedu"],
                # "phone": supplemental["Phone"], # no phone in supplemental
                "first": supplemental["Name"]["First"],
                "last": supplemental["Name"]["Last"],
                "middle": supplemental["Name"]["Middle"],
                "middle_initial": supplemental["Name"]["MiddleInitial"],
                "prefix": supplemental["Name"]["Prefix"],
                "suffix": supplemental["Name"]["Suffix"],
            }

        # find matching row in general data
        for row in data:
            if (
                row[8] == metadata["email"]
                # or row[2] == metadata["phone"]
                or (row[2] == metadata["first"] and row[3] == metadata["last"])
                # and row[5] == metadata["middle"]
                # and row[6] == metadata["middle_initial"]
                # and row[7] == metadata["prefix"]
                # and row[8] == metadata["suffix"]
            ):
                row_id = row[0]
                print(f"found match for {row_id} at {id}")

                # print(
                #     f'email: {row[8]} == {metadata["email"]}\t\t{row[2]} == {metadata["first"]}\t\t{row[3]} == {metadata["last"]}'
                # )

                # move data to rows/
                os.rename(
                    f"supplemental/{id}/supplemental.json",
                    f"rows/{row_id}/supplemental.json",
                )

                # move other files if they exist
                for file in os.listdir(f"supplemental/{id}"):
                    if file.startswith("file_") or file.startswith("transcript"):
                        os.rename(
                            f"supplemental/{id}/{file}",
                            f"rows/{row_id}/supplemental_{file}",
                        )

                # move transcript files
                for i in range(1, 3):
                    if os.path.exists(f"supplemental/{id}/transcript{i}.txt"):
                        os.rename(
                            f"supplemental/{id}/transcript{i}.txt",
                            f"rows/{row_id}/supplemental/transcript{i}.txt",
                        )

                # move on
                os.removedirs(f"supplemental/{id}")
                break


if __name__ == "__main__":
    """
    simplecv:
    - get all applicant info from cognito forms
        - put that into xml
    - get all applicant files from wherever
        - transcribe youtube videos
    - send prompt, xml (no applicant metadata), documentation to bedrock
    - save response xml to s3 with id of applicant as name
    """

    # csv headers
    # THIS WILL OVERWRITE THE CSV IF EXISTS - IF RUNNING THIS MULTIPLE TIMES, MAKE SURE TO DELETE THIS LINE ON CONTINUED RUNS
    with open("participants.csv", "w") as f:
        f.write(
            '"id","timestamp","first","last","middle","middle_initial","prefix","suffix","email","phone","resume_id","resume_name","major","year","of_age"\n'
        )

    load_general_rows()

    # if supplemental information: uncomment below lines
    # load_supplemental_rows()
    # match_rows()
    # os.rename("supplemental", "unmatched")
    # print(
    #     "loaded and matched rows, now manually check unmatched folder for missed programatic matches in rows/"
    # )
