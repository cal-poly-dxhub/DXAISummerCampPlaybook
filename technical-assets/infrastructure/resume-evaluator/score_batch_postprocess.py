import json
from typing import Optional

from lxml import etree  # type: ignore

from score_batch import input_jsonl_file_name

batch_output_file_name = f"{input_jsonl_file_name}.out"


def fetch_scores(
    id: int, text: str
) -> Optional[tuple[int, int, int, int, int, int, int]]:
    """
    recover scores from llm output
    returns a tuple of the scores
    """

    """```json
{
   "Collaboration": {"chainOfThought": string, "score": int},
   "Initiative": {"chainOfThought": string, "score": int},
   "Creativity": {"chainOfThought": string, "score": int},
   "Communication": {"chainOfThought": string, "score": int},
   "ProblemDecomposition": {"chainOfThought": string, "score": int},
   "GrowthMindset": {"chainOfThought": string, "score": int},
   "TechnicalExperience": {"chainOfThought": string, "score": int}
}
```"""

    try:
        scores = json.loads(text)

        return (
            scores["Collaboration"]["score"],
            scores["Initiative"]["score"],
            scores["Creativity"]["score"],
            scores["Communication"]["score"],
            scores["ProblemDecomposition"]["score"],
            scores["GrowthMindset"]["score"],
            scores["TechnicalExperience"]["score"],
        )
    except json.JSONDecodeError as e:
        print(f"ERROR: id: {id} | JSONDecodeError: {e}")


if __name__ == "__main__":
    headers = [
        "id",
        "Collaboration",
        "Initiative",
        "Creativity",
        "Communication",
        "Problem Decomposition",
        "Growth Mindset",
        "Technical Experience",
    ]
    participant_score_info = open("participant_score_info.csv", "a")
    participant_score_info.write(",".join(headers) + "\n")

    with open(batch_output_file_name, "r") as f:
        for index, line in enumerate(f):
            try:
                data = json.loads(line)
                id = data["recordId"].split("-")[-1]
                if not id.isdigit():
                    print(f"skipping {id} (not a number)")
                    continue

                id = int(id)
                try:
                    text = data["modelOutput"]["content"][0]["text"]
                    scores = fetch_scores(id, text)
                    if scores is not None:
                        participant_score_info.write(
                            f"{id},{scores[0]},{scores[1]},{scores[2]},{scores[3]},{scores[4]},{scores[5]},{scores[6]}\n"
                        )
                except KeyError as e:
                    print(f"KeyError: {e} in id {id}")
            except Exception as e:
                print(f"Error processing line: {index}, {e}")
