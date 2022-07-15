# The goal: generate a CSV that contains: the following:
#   - unique id
#   - email id
#   - email subject
#   - email tags
#   - quote
#   - quote classes
# To do this we have to:
#   0) Load the atlas project.
#   1) Load all quotes
#       a. load the tags (id-to-name)
#       b. load the tagQuoteLinks (quote_id-to-tag_id)
#       c. load quotations per document (unique id-to-segmentindices)
#           - and apply the results from a and b on it.
#       d. now we have {doc_id: [{quote_id, segmentindices, tags}]}
#   2) load all document content guids
#   3) iterate through results of 1
#       a. transform doc_id to cnt_id (s.t. e.g. "doc_10" == "cnt_10")
#       b. iterate through the document's body and through the quotes simultaneously.
#           i: if the element's text starts with, store them
#               - email id:
#               - subject:
#               - tags:
#           ii: if the element-id + 1 equals the quote segment start, then:
#               - extract the quote
#               - create new data entry
#   4) export all data entries
#       a. filter email tags on relevant tags
#       b. output 0/1 per existing tag
#       c. output 0/1 per existing class

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


def get_quote_links(root: Element) -> dict:
    """Loads tag quote links from root."""
    tags = {tg.get("id"): tg.get("name") for tg in root.find("tags").findall("tag")}
    quote_links = {}
    for tql in root.find("links").findall("tagQuotLink"):
        target_id = tql.get("target")
        tag = tags[tql.get("source")]
        if target_id in quote_links:
            quote_links[target_id].append(tag)
        else:
            quote_links[target_id] = [tag]
    return quote_links


def get_med_to_document_guid(a_root) -> dict:
    """returns the document id for all media"""
    doc_contents = [
        {"med": med.get("id"), "cnt": med.get("content")}
        for med in a_root.find("media").findall("medium")
    ]
    docs = {}
    for index, cnt in enumerate(a_root.find("contents").findall("content")):
        docs[doc_contents[index]["med"]] = cnt.get("loc")
        if index == len(doc_contents) - 1:
            break
    return docs


def get_quotes(root: Element, quote_links: dict) -> list:
    """Returns quotations with corresponding tags"""
    quote_segments = {}
    for doc in root.find("documents").findall("document"):
        doc_quotes = []
        for qt in doc.find("layer").findall("quotation"):
            try:
                loc = qt.find("location").find("segmentedTextLoc")
                quote = {
                    "lineStart": int(loc.get("sSegment")),
                    "lineEnd": int(loc.get("eSegment")),
                    "substringStart": int(loc.get("sOffset")),
                    "substringEnd": int(loc.get("eOffset")),
                    "tags": quote_links[qt.get("id")],
                }
                doc_quotes.append(quote)
            except KeyError:
                trg = qt.get("id")
                print(f"failed to output {trg}")
        quote_segments[doc.get("medium")] = doc_quotes
    return quote_segments


ATLAS_PATH_IN = "./data/atlas_to_csv/ds.atlproj"
ATLAS_PATH_OUT = "./data/atlas_to_csv/extract/"


a_root, a_tree = load_atlas_as_tree(ATLAS_PATH_IN, ATLAS_PATH_OUT)

# {med_id: [{linestart, lineEnd, SubstringStart, SubstringEnd}]}
quotes = get_quotes(a_root, get_quote_links(a_root))
# [{medium_id: file_name}]
med_to_doc = get_med_to_document_guid(a_root)
# {content_id: file_name}
comments = {
    cmt.get("id"): cmt.get("loc") for cmt in a_root.find("contents").findall("content")
}


for key, doc in med_to_doc.items():
    qts = quotes[key]
    found_quotes = []
    c_qts = 0

    print(doc)

    data_path = f"{ATLAS_PATH_OUT}contents/{doc}/content"
    data_root = ET.parse(data_path).getroot()

    for element in iter(data_root.find("body")):
        if int(element.get("id")) + 1 == int(qts[c_qts]["lineStart"]):
            line = element.find("span").text
            found_quotes.append(
                line[qts[c_qts]["substringStart"] : qts[c_qts]["substringEnd"]]
            )
            c_qts += 1
