"""Turns issue findings into text documents."""

import json
import sys
import os
from xml.etree.ElementTree import Element
import xml.etree.ElementTree as ET


def get_all_entries(tree_root: ET.ElementTree) -> list:
    """Returns all html entries of a given atlas tree."""
    html_body = tree_root.find("body")
    entries = html_body.findall("h2")
    entries.extend(html_body.findall("h3"))
    return entries


def find_data_for_issue_document_combination(
    issue: str, doc_id: str, metadata: dict, atlas_data_path
):
    """generates single outputfile for a given issue-document combi."""
    issue_findings = {}

    tree = ET.parse(f"{atlas_data_path}/{doc_id}/content")
    tree_root = tree.getroot()

    current_mail = None
    for element in iter(tree_root.find("body")):
        if element.tag == "h2":
            current_mail = element.find("span").text
            continue

        for quote in metadata["quotes"]:

            # Tests if the quote is in this element.
            quote_loc = int(quote["location_sSegment"])
            if int(element.get("id")) != quote_loc - 1:
                continue

            # adds entry
            inner_html: Element = element.find("span")
            text: str = inner_html.text
            issue_findings[quote_loc] = {
                "issue_id": issue,
                "filename": metadata["filename"],
                "file_guid": doc_id,
                "quote_loc": quote_loc,
                "email_id": current_mail,
                "email_body": text,
            }

    return [value for (key, value) in issue_findings.items()]


def compose(data_file_path, output_dir, atlas_data_path):
    """Composes the issue mail links."""
    with open(data_file_path, "r", encoding="utf-8") as data_file:
        data: dict = json.loads(data_file.read())

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    for issue_id, documents in data.items():
        for document_id, document_metadata in documents.items():
            findings = find_data_for_issue_document_combination(
                issue_id, document_id, document_metadata, atlas_data_path
            )
            with open(
                f"{output_dir}{issue_id}-{document_id}.json", "w", encoding="utf-8"
            ) as output_file:
                output_file.write(json.dumps(findings, indent=4))


if __name__ == "__main__":
    OUTPUT_DIR = sys.argv[1]
    DATA_FILEPATH = sys.argv[2]
    ATLAS_DATA_PATH = sys.argv[3]
    compose(DATA_FILEPATH, OUTPUT_DIR, ATLAS_DATA_PATH)
