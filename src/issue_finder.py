"""
Loads the architectural issue dataset and the
atlasti data set and determines in what atlas
files what issues are discussed.
"""

import json
import xml.etree.ElementTree as ET
from xmlrpc.client import boolean
from zipfile import ZipFile
import pandas as pd

EXTRACT_PATH: str = "./data/atlas_extract/"
XLSX_DATA_FILE = "./data/IssuesDatasetArchitectural.xlsx"
ATLAS_FILE = "./data/MSc_Internship-2022-05-17T14-09.atlproj"


def get_issue_keys(xlsx_path: str) -> list:
    """Returns issue keys"""
    dataframe = pd.read_excel(xlsx_path)
    return [row["issues key"] for (_, row) in dataframe.iterrows()]


def get_atlas_docs(atlas_path: str) -> tuple:
    """Loads atlas documents."""
    with ZipFile(atlas_path, "r") as atlas_zip:
        atlas_zip.extractall(EXTRACT_PATH)
    tree = ET.parse(EXTRACT_PATH + "project.aprx")
    tree_root = tree.getroot()
    doc_root = tree_root.find("contents")
    doc_ids = [doc.get("loc") for doc in doc_root.findall("content")]
    return doc_ids, tree


def find_keys_in_atlasti(target_keys: list, target_docs: list) -> dict:
    """returns dict with all keys and their corresponding documents."""
    key_docs: dict = {}
    for key in target_keys:
        relevant_docs: list = list()
        for doc in target_docs:
            if find_in_atlas(key, doc):
                relevant_docs.append(doc)
        if len(relevant_docs) > 0:
            key_docs[key] = relevant_docs
    return key_docs


def find_in_atlas(target_key: str, target_doc: str) -> boolean:
    """returns all docs in atlasti corresponding to this file"""
    with open(
        f"{EXTRACT_PATH}contents/{target_doc}/content", "r", encoding="utf-8"
    ) as target_file:
        result = target_file.read().find(target_key)
    return result > -1


def add_tags(keys: dict, atlas_tree: ET.ElementTree) -> dict:
    """gets all quotes of all documents."""
    tree_root = atlas_tree.getroot()
    quotes = {}
    for issue, docs in keys.items():
        issue_quotes = {}
        for doc in docs:
            issue_quotes[doc] = get_quotes(tree_root, doc)
        quotes[issue] = issue_quotes
    return quotes

def get_quotes(tree_root: ET.ElementTree, doc):
    """gets all quotes of the provided document."""
    # Finds respective content
    the_content = None
    for content in tree_root.find("contents").findall("content"): 
        if content.get("loc") == doc: 
            the_content = content
            break

    # Finds respective medium
    the_medium = None
    the_content_id = the_content.get("id")
    for medium in tree_root.find("media").findall("medium"):
        if medium.get("content") == the_content_id:
            the_medium = medium
            break

    # Finds respective medium
    the_document = None
    the_medium_id = the_medium.get("id")
    for document in tree_root.find("documents").findall("document"):
        if document.get("medium") == the_medium_id:
            the_document = document
            break

    # extract quotes.
    quotes = []
    the_layer = the_document.find("layer")
    for quote in the_layer.findall("quotation"):
        entry = {}
        for key in quote.keys():
            entry[key] = quote.get(key)
        location = quote.find("location").find("segmentedTextLoc")
        for key in location.keys(): 
            entry[f'location_{key}'] = location.get(key)
        quotes.append(entry)

    return quotes


issue_keys = get_issue_keys(XLSX_DATA_FILE)
atlas_docs, atlas_tree = get_atlas_docs(ATLAS_FILE)
my_keys = find_keys_in_atlasti(issue_keys, atlas_docs)
data = add_tags(my_keys, atlas_tree)


print(json.dumps(data, indent=4))
