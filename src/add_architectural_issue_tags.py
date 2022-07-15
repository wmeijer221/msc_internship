"""Obsolete: the web version of atlas can't import .atlproj documents..."""

import os
import datetime
import uuid

import zipfile
from zipfile import ZipFile
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
import pandas as pd


def load_atlas_as_tree(atlas_project_path: str, atlas_output_path: str) -> ET.Element:
    """Loads the atlas project as an ET tree."""
    with ZipFile(atlas_project_path, "r") as atlas_zip:
        atlas_zip.extractall(atlas_output_path)
    tree = ET.parse(os.path.join(atlas_output_path, "project.aprx"))
    root = tree.getroot()
    return root, tree


def load_issues(issue_file_path: str) -> list:
    """Loads architectural issues."""
    dataframe = pd.read_excel(issue_file_path)
    return [row["issues key"] for (_, row) in dataframe.iterrows()]


def get_issue_quotes(
    atlas_root: Element, issues: list, atlas_project_path: str
) -> list:
    """Returns all quotes corresponding with architectural issues."""
    quotes = []
    for document in atlas_root.find("contents").findall("content"):
        doc_tree = ET.parse(
            os.path.join(atlas_project_path, "contents", document.get("loc"), "content")
        ).getroot()
        for element in iter(doc_tree.find("body")):
            inner_content = element.find("span")
            if inner_content is None:
                continue
            for issue_key in issues:
                index = inner_content.text.find(issue_key)
                if index == -1:
                    continue
                quotes.append(
                    {
                        "cnt_id": document.get("id"),
                        "sOffset": str(index),
                        "eOffset": str(index + len(issue_key)),
                        "sSegment": element.get("id"),
                        "eSegment": element.get("id"),
                    }
                )
    return quotes


def make_content_to_document_map(atlas_root: Element) -> dict:
    """returns a map."""

    content_to_document_map: dict = {}
    for content in atlas_root.find("contents").findall("content"):
        content_id = content.get("id")
        for medium in atlas_root.find("media").findall("medium"):
            if medium.get("content") != content_id:
                continue
            medium_id = medium.get("id")
            for document in atlas_root.find("documents").findall("document"):
                if document.get("medium") != medium_id:
                    continue
                content_to_document_map[content_id] = document
                break
            break
    return content_to_document_map


def add_issue_quotes(atlas_root: ET.Element, issue_quotes: list):
    """Adds issue quotations to the atlas project."""

    quote_ids = []
    content_to_document_map = make_content_to_document_map(atlas_root)
    for issue_quote in issue_quotes:
        document = content_to_document_map[issue_quote["cnt_id"]]
        sublayer: Element = document.find("layer")

        # creates new quotation element
        new_quotation = Element("quotation")

        # adds correct id.
        last_child = list(iter(sublayer))[-1]
        id_split = last_child.get("id").split("_")
        id_counter = int(id_split[-1]) + 1
        chunks = id_split[:-1]
        chunks.append(str(id_counter))
        new_id = "_".join(chunks)
        new_quotation.set("id", new_id)
        new_quotation.set("number", str(id_counter))

        # adds other fields.
        new_quotation.set("owner", "usr_1")
        creation_date = f"{datetime.datetime.now():%Y-%m-%dT%H:%M:%SZ}"
        new_quotation.set("cDate", creation_date)
        new_quotation.set("mDate", creation_date)
        new_quotation.set("mUser", "usr_1")
        new_quotation.set("guid", str(uuid.uuid4()))

        sublayer.append(new_quotation)

        # adds new location
        new_location = Element("location")
        new_quotation.append(new_location)

        # adds new segmentedTextLoc
        new_segmented_text_loc = Element("segmentedTextLoc")
        new_segmented_text_loc.set("sSegment", issue_quote["sSegment"])
        new_segmented_text_loc.set("sOffset", issue_quote["sOffset"])
        new_segmented_text_loc.set("eSegment", issue_quote["eSegment"])
        new_segmented_text_loc.set("eOffset", issue_quote["eOffset"])

        new_location.append(new_segmented_text_loc)

        quote_ids.append(new_id)

    return quote_ids


def add_tag_quote_link(atlas_root: ET.Element, quotes_ids: list, tag_id: str):
    links: ET.Element = atlas_root.find("links")

    for quote_id in quotes_ids:

        new_tagquote = Element("tagQuotLink")

        new_tagquote.set("source", tag_id)
        new_tagquote.set("target", quote_id)
        new_tagquote.set("owner", "usr_1")
        new_tagquote.set("cDate", f"{datetime.datetime.now():%Y-%m-%dT%H:%M:%SZ}")
        new_tagquote.set("cUser", "usr_1")
        new_tagquote.set("guid", str(uuid.uuid4()))

        links.append(new_tagquote)


def save_tree(atlas_tree: ET.ElementTree, atlas_output_path: str):
    """saves the upgraded tree."""
    
    with open(atlas_output_path, "wb") as output_path:
        atlas_tree.write(output_path, encoding="utf-8")


def zip_atlas_project(atlas_project_path: str, atlas_extract_path: str):
    """Exports the upgraded project as a zip"""
    with ZipFile(atlas_project_path, "w", zipfile.ZIP_DEFLATED) as ziph:
        for root, _, files in os.walk(atlas_extract_path):
            for file in files:
                ziph.write(
                    os.path.join(root, file),
                    os.path.relpath(os.path.join(root, file), atlas_extract_path),
                )


if __name__ == "__main__":
    ATLAS_PROJECT_FILE = "./data/MSc_Internship-2022.atlproj"
    ATLAS_EXTRACT_PATH = "./data/atlas_extract/"
    ISSUE_FILE_PATH = "./data/IssuesDatasetArchitectural.xlsx"
    TAG_ID = "t_26"
    ATLAS_EXPORT_PATH = "./data/Upgraded.atlproj"

    atlas_root, atlas_tree = load_atlas_as_tree(ATLAS_PROJECT_FILE, ATLAS_EXTRACT_PATH)
    issues = load_issues(ISSUE_FILE_PATH)

    issue_quotes = get_issue_quotes(atlas_root, issues, ATLAS_EXTRACT_PATH)
    new_quote_ids = add_issue_quotes(atlas_root, issue_quotes)
    add_tag_quote_link(atlas_root, new_quote_ids, TAG_ID)

    output_path = os.path.join(ATLAS_EXTRACT_PATH, "project.aprx")
    save_tree(atlas_tree, output_path)

    zip_atlas_project(ATLAS_EXPORT_PATH, ATLAS_EXTRACT_PATH)
