"""
Loads the architectural issue dataset and the
atlasti data set and determines in what atlas
files what issues are discussed.
"""

import json
import os
import sys

import xml.etree.ElementTree as ET
from zipfile import ZipFile
import pandas as pd


class IssueFinder:
    """Finds issues in atlas ti project and exports results."""

    def get_issue_keys(self, xlsx_path: str) -> list:
        """Returns issue keys"""
        dataframe = pd.read_excel(xlsx_path)
        return [row["issues key"] for (_, row) in dataframe.iterrows()]

    def get_atlas_docs(self, atlas_path: str) -> tuple:
        """Loads atlas documents."""
        with ZipFile(atlas_path, "r") as atlas_zip:
            atlas_zip.extractall(self.extract_path)
        tree = ET.parse(self.extract_path + "project.aprx")
        tree_root = tree.getroot()
        doc_root = tree_root.find("contents")
        doc_ids = [doc.get("loc") for doc in doc_root.findall("content")]
        return doc_ids, tree

    def find_keys_in_atlasti(self, target_keys: list, target_docs: list) -> dict:
        """returns dict with all keys and their corresponding documents."""
        key_docs: dict = {}
        for key in target_keys:
            relevant_docs: list = list()
            for doc in target_docs:
                if self.find_in_atlas(key, doc):
                    relevant_docs.append(doc)
            if len(relevant_docs) > 0:
                key_docs[key] = relevant_docs
        return key_docs

    def find_in_atlas(self, target_key: str, target_doc: str) -> bool:
        """returns all docs in atlasti corresponding to this file"""
        with open(
            f"{self.extract_path}contents/{target_doc}/content", "r", encoding="utf-8"
        ) as target_file:
            result = target_file.read().find(target_key)
        return result > -1

    def add_tags(self, keys: dict, atlas_tree: ET.ElementTree) -> dict:
        """gets all quotes of all documents."""
        tree_root = atlas_tree.getroot()
        quotes = {}
        for issue, docs in keys.items():
            issue_quotes = {}
            for doc in docs:
                issue_quotes[doc] = self.get_metadata(tree_root, doc)
            quotes[issue] = issue_quotes
        return quotes

    def get_metadata(self, tree_root: ET.ElementTree, doc):
        """
        Gets all relevant metadata of the provided document.
        Has to move throughout the atlas data format to find them:
        ``Doc -(doc, loc)-> Content -(id, content)-> Media -(id, medium)-> Document``
        Read as: ``Source -(sourcefield, targetfield)-> Target``
        """
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
                entry[f"location_{key}"] = location.get(key)

            entry["tag"] = self.get_quote_tag(tree_root, quote)

            quotes.append(entry)

        return {"filename": the_medium.get("name"), "quotes": quotes}

    def get_quote_tag(self, tree_root: ET.ElementTree, quote):
        """Returns tag of respective quote"""

        # Finds respective link.
        the_link = None
        for link in tree_root.find("links").findall("tagQuotLink"):
            if link.get("target") == quote.get("id"):
                the_link = link
                break

        the_tag = None
        for tag in tree_root.find("tags").findall("tag"):
            if tag.get("id") == the_link.get("source"):
                the_tag = tag
                break

        return the_tag.get("name")

    def find_issues(self, xlsx_data_file, atlas_file, output_path, extract_path):
        """Finds and exports issues."""
        self.extract_path = extract_path

        issue_keys = self.get_issue_keys(xlsx_data_file)
        atlas_docs, atlas_tree = self.get_atlas_docs(atlas_file)
        my_keys = self.find_keys_in_atlasti(issue_keys, atlas_docs)
        data = self.add_tags(my_keys, atlas_tree)

        dirname = os.path.dirname(output_path)
        if not os.path.exists(dirname):
            os.mkdir(dirname)

        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write(json.dumps(data, indent=4))


if __name__ == "__main__":
    XLSX_DATA_FILE = sys.argv[1]
    ATLAS_FILE = sys.argv[2]
    OUTPUT_PATH = sys.argv[3]
    EXTRACT_PATH = sys.argv[4]

    finder = IssueFinder()
    finder.find_issues(XLSX_DATA_FILE, ATLAS_FILE, OUTPUT_PATH, EXTRACT_PATH)
