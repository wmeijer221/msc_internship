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


def get_atlas_docs(atlas_path: str):
    """Loads atlas documents."""
    with ZipFile(atlas_path, "r") as atlas_zip:
        atlas_zip.extractall(EXTRACT_PATH)
    tree = ET.parse(EXTRACT_PATH + "project.aprx")
    tree_root = tree.getroot()
    doc_root = tree_root.find("contents")
    doc_ids = [doc.get("loc") for doc in doc_root.findall("content")]
    return doc_ids


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
    with open(f"{EXTRACT_PATH}contents/{target_doc}/content", "r", encoding="utf-8") as target_file:
        result = target_file.read().find(target_key)
    return result > -1


keys = get_issue_keys(XLSX_DATA_FILE)
atlas_docs = get_atlas_docs(ATLAS_FILE)
keys = find_keys_in_atlasti(keys, atlas_docs)
print(json.dumps(keys, indent=4))
