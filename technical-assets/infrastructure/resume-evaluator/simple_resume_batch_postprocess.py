import json
import os

from lxml import etree  # type: ignore

from simple_resume_batch import input_jsonl_file_name

batch_output_file_name = f"{input_jsonl_file_name}.out"


def str_to_xml(id: int, text: str) -> str:
    """
    recover XML from llm output, inject metadata, and save to file
    returns path to saved XML file
    """
    # extract XML portion from the llm output
    start_idx = text.find("<SimpleResume")
    if start_idx == -1:
        print(f"No <SimpleResume> root element found for participant {id}")
        return ""

    xml_fragment = text[start_idx:]

    # parse dirty XML
    parser = etree.XMLParser(recover=True)
    try:
        root = etree.fromstring(xml_fragment.encode("utf-8"), parser=parser)  # type: ignore
    except Exception as e:
        raise ValueError(f"Failed to parse XML: {e}")

    # load metadata
    metadata_path = f"rows/{id}/metadata.json"
    if os.path.exists(metadata_path):
        with open(metadata_path, "r") as meta_file:
            metadata = json.load(meta_file)

        # create <Metadata> element
        metadata_elem = etree.Element("Metadata")  # type: ignore
        for key, value in metadata.items():
            sub = etree.SubElement(metadata_elem, key)  # type: ignore
            sub.text = str(value) if value is not None else ""

        # inject <Metadata> at the top of <SimpleResume>
        root.insert(0, metadata_elem)

    else:
        print(f"Warning: metadata.json not found for ID {id}")

    # pretty-print and save
    pretty_xml = etree.tostring(root, pretty_print=True, encoding="unicode")  # type: ignore
    os.makedirs("simpleResumes", exist_ok=True)
    file_path = f"simpleResumes/{id}.xml"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(pretty_xml)  # type: ignore

    return file_path


if __name__ == "__main__":
    # reads the batch out file and creates XML files from llm output
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
                    str_to_xml(id, text)
                except KeyError as e:
                    print(f"KeyError: {e} in id {id}")
            except Exception as e:
                print(f"Error processing line: {index}, {e}")
