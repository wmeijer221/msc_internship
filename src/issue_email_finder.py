"""
Identifies what emails of the atlas project 
reference what issue keys and stores these links.
"""


import os
import json

from zipfile import ZipFile
import xml.etree.ElementTree as ET
import pandas as pd


def load_atlas_as_tree(atlas_project_path: str, atlas_output_path: str) -> ET.Element:
    with ZipFile(atlas_project_path, "r") as atlas_zip:
        atlas_zip.extractall(atlas_output_path)
    tree = ET.parse(os.path.join(atlas_output_path, "project.aprx"))
    root = tree.getroot()
    return root


def load_issues(issue_file_path: str) -> list:
    dataframe = pd.read_excel(issue_file_path)
    return [row["issues key"] for (_, row) in dataframe.iterrows()]


def find_issue_references_in_documents(
    tree_root: ET.Element, issues: list, atlas_project_path: str
) -> dict:
    """returns dictionary of documents that reference issue keys."""

    issue_references = {}

    # iterates through all documents.
    for document in tree_root.find("contents").findall("content"):
        document_path = os.path.join(
            atlas_project_path, "contents", document.get("loc"), "content"
        )
        with open(document_path, "r", encoding="utf-8") as atlas_document:
            atlas_data: str = atlas_document.read()

            # iterates through all architectural issues.
            for issue_key in issues:
                index: int = atlas_data.find(issue_key)

                if index == -1:
                    continue

                try:
                    issue_references[issue_key]
                except KeyError:
                    issue_references[issue_key] = []

                issue_references[issue_key].append(document.get("loc"))

    return issue_references


def find_issue_references_in_mails(
    issue_referencing_documents: dict, atlas_project_path: str
) -> dict:
    """returns dictionary of emails reference issue keys."""

    found_references = {}
    previous_element = None

    for issue_key, documents in issue_referencing_documents.items():
        for document in documents:

            # Gets document.
            document_path = os.path.join(
                atlas_project_path, "contents", document, "content"
            )
            doc_root = ET.parse(document_path).getroot()

            # Iterates through all internal headers that
            # store individual pieces of text.
            current_mail = None
            for entry in iter(doc_root.find("body")):
                if entry.tag == "h2":
                    current_mail = entry.find("span").text
                    continue

                # searches issue
                inner_html = entry.find("span")

                # ignore cases without innerhtml
                if inner_html is None:
                    continue

                # ignores entries without issue reference.
                index = inner_html.text.find(issue_key)
                if index > -1 and previous_element == "Body:":
                    # Adds email entry if its the body
                    try:
                        found_references[issue_key]
                    except KeyError:
                        found_references[issue_key] = []

                    found_references[issue_key].append(
                        {
                            "document_guid": document,
                            "email": current_mail,
                            "found_at": index,
                            "email_text": inner_html.text,
                        }
                    )
                previous_element = inner_html.text

    return found_references


def store_referencing_emails(issue_referencing_emails: dict, linking_path: str):
    """Outputs the issue references as json."""

    dirname: str = os.path.dirname(linking_path)
    if not os.path.exists(dirname):
        os.mkdir(dirname)

    with open(linking_path, "w", encoding="utf-8") as output_file:
        output_file.write(json.dumps(issue_referencing_emails, indent=4))


def make_readable_files(issue_referencing_emails: dict, readable_file_output_path: str):
    """Outputs found references to plain text."""

    dirname: str = os.path.dirname(readable_file_output_path)
    if not os.path.exists(dirname):
        os.mkdir(dirname)

    for issue, documents in issue_referencing_emails.items():
        with open(
            os.path.join(readable_file_output_path, issue), "w", encoding="utf-8"
        ) as output_file:
            for document in documents:
                output_file.write(
                    f'{document["email"]}\n\n{document["email_text"]}\n\n\n\n'
                )


def find(
    atlas_project_path: str,
    atlas_output_path: str,
    issue_file_path: str,
    link_file_path: str,
    readable_file_output_path: str,
):
    tree_root = load_atlas_as_tree(atlas_project_path, atlas_output_path)
    issues = load_issues(issue_file_path)
    issue_referencing_documents = find_issue_references_in_documents(
        tree_root, issues, atlas_output_path
    )
    issue_referencing_emails = find_issue_references_in_mails(
        issue_referencing_documents, atlas_output_path
    )
    store_referencing_emails(issue_referencing_emails, link_file_path)
    make_readable_files(issue_referencing_emails, readable_file_output_path)


if __name__ == "__main__":
    ATLAS_PROJECT_PATH = "./data/MSc_Internship-2022.atlproj"  # sys.argv[1]
    ATLAS_OUTPUT_PATH = "./data/atlas_extract/"  # sys.argv[2]
    ISSUE_FILE_PATH = "./data/IssuesDatasetArchitectural.xlsx"  # sys.argv[3]
    LINK_FILE_PATH = "./data/issue-mail-relations/links.json"  # sys.argv[4]
    READABLE_FILE_OUTPUT_PATH = (
        "./data/issue-mail-relations/readable-files/"  # sys.argv[5]
    )

    find(
        ATLAS_PROJECT_PATH,
        ATLAS_OUTPUT_PATH,
        ISSUE_FILE_PATH,
        LINK_FILE_PATH,
        READABLE_FILE_OUTPUT_PATH,
    )
