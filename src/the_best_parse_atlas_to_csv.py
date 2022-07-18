"""
Transforms a web atlas project to .csv format. 
Two files are exported on two granularity levels: 
- quotes:   containing the atlas quotation and its rationale types, 
            as well, as the id and subject of the containing email. 
- email:    containing the decision types as well as the rationale 
            types of all quotes included inside said mail, as well 
            as the id and subject of the discussed mail.
"""

import os
from zipfile import ZipFile
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
from copy import deepcopy
import itertools
import re


def load_atlas_as_tree(atlas_project_path: str, atlas_output_path: str) -> ET.Element:
    """Loads the atlas project as an ET tree."""
    with ZipFile(atlas_project_path, "r") as atlas_zip:
        atlas_zip.extractall(atlas_output_path)
    tree = ET.parse(os.path.join(atlas_output_path, "project.aprx"))
    root = tree.getroot()
    return root


# Load all quotes
def load_all_quotes(root: Element) -> dict:
    """Loads all quotes contained in the atlas project."""
    quotes = {}
    tags = {tg.get("id"): tg.get("name") for tg in root.find("tags").findall("tag")}
    quote_tags = {}
    for tql in root.find("links").findall("tagQuotLink"):
        trg = tql.get("target")
        src = tags[tql.get("source")]
        if trg in quote_tags:
            quote_tags[trg].append(src)
        else:
            quote_tags[trg] = [src]
    # load quotations per document (unique id-to-segmentindices)
    for doc in root.find("documents").findall("document"):
        doc_id = doc.get("id")
        quotes[doc_id] = []
        for qt in doc.find("layer").findall("quotation"):
            try:
                comment_obj = qt.find("comment")
                comment_id = (
                    comment_obj.get("content") if comment_obj is not None else None
                )
                tloc = qt.find("location").find("segmentedTextLoc")
                qt_entry = {
                    "thread": doc.get("name"),
                    "id": qt.get("id"),
                    "sSegment": int(tloc.get("sSegment")),
                    "sOffset": int(tloc.get("sOffset")),
                    "eSegment": int(tloc.get("eSegment")),
                    "eOffset": int(tloc.get("eOffset")),
                    #           - and apply the results from a and b on it.
                    "tags": quote_tags[qt.get("id")],
                    "comment_content_id": comment_id,
                }
                quotes[doc_id].append(qt_entry)
                if qt_entry["sSegment"] != qt_entry["eSegment"]:
                    print(f'{qt_entry["sSegment"]=}, {qt_entry["eSegment"]=}')
            except KeyError:
                qid = qt.get("id")
                print(f"Failed on {qid}")
        quotes[doc_id].sort(key=lambda x: x["sSegment"])
    #       d. now we have {doc_id: [{quote_id, segmentindices, tags}]}
    return quotes


# generate data
def generate_data(root: Element, quotes: dict) -> list:
    """Generates data to export acquired from the atlas project."""
    cnt_to_doc = {
        cnt.get("id"): cnt.get("loc")
        for cnt in root.find("contents").findall("content")
    }
    tags_per_email: dict[str, list] = {doc_id: [] for doc_id in quotes.keys()}
    tags_per_quote = {doc_id: [] for doc_id in quotes.keys()}
    for doc_id, quotes in quotes.items():
        # Open respective HTML document with XML parser.
        doc_loc = cnt_to_doc[f"cnt_{doc_id[4:]}"]
        print(f"{doc_loc=}")
        doc_file = f"{ATLAS_PATH_OUT}contents/{doc_loc}/content"
        parser = ET.XMLParser()
        parser.entity["nbsp"] = " "
        d_root = ET.parse(doc_file, parser=parser).getroot()
        # data and flags
        current_email = {
            "document": doc_id,
            "id": None,
            "subject": None,
            "type_tags": None,
            "rationale_tags": set(),
        }
        quote_index = 0
        email_id_flag = False
        email_subject_flag = False
        email_tags_flag = False
        for ele in iter(d_root.find("body")):
            # Stores all email entries their decision types and their rationale types.
            if ele.tag == "h2" and current_email["id"] is not None:
                tags_per_email[doc_id].append(deepcopy(current_email))
                current_email["id"] = None
                current_email["subject"] = None
                current_email["type_tags"] = None
                current_email["rationale_tags"] = set()
            # Sets email information.
            text = ele.find("span").text
            l_text = text.lower()
            if l_text.startswith("email id:"):
                email_id_flag = True
                continue
            elif l_text.startswith("subject:"):
                email_subject_flag = True
                continue
            elif l_text.startswith("tags:"):
                email_tags_flag = True
                continue
            elif email_id_flag:
                email_id_flag = False
                current_email["id"] = text
                continue
            elif email_subject_flag:
                email_subject_flag = False
                current_email["subject"] = text
                continue
            elif email_tags_flag:
                email_tags_flag = False
                current_email["type_tags"] = text.strip().split(", ")
                continue
            # updating quotes cannot be done when the last one is handled.
            if quote_index >= len(quotes):
                continue
            # handles all quotes
            current_quote = quotes[quote_index]
            eid = int(ele.get("id")) + 1
            while eid == current_quote["sSegment"]:
                quotation = text[current_quote["sOffset"] : current_quote["eOffset"]]
                quote_tags = current_quote["tags"]
                # updates current email
                current_email["rationale_tags"].update(quote_tags)
                # exports quotation.
                new_entry = {
                    "quote": quotation,
                    "tags": quote_tags,
                    "email_id": current_email["id"],
                    "email_subject": current_email["subject"],
                    "comment": "",
                }

                # load respective comment
                comment_id = current_quote["comment_content_id"]
                if comment_id is not None:
                    new_entry["comment"] = load_comment(cnt_to_doc, comment_id)

                # Adds it to the list
                tags_per_quote[doc_id].append(new_entry)
                quote_index += 1
                if quote_index < len(quotes):
                    current_quote = quotes[quote_index]
                else:
                    break
        # make sure the final one gets in too.
        if current_email["id"] is not None:
            tags_per_email[doc_id].append(deepcopy(current_email))
    return tags_per_email, tags_per_quote


def load_comment(cnt_to_doc: dict, comment_content_id: str) -> str:
    """Loads the text stored in te atlasti comment."""
    comment_loc = cnt_to_doc[comment_content_id]
    print(f"{comment_loc=}")
    comment_file = f"{ATLAS_PATH_OUT}contents/{comment_loc}/content"
    with open(comment_file, "r", encoding="utf-8") as comment_data:
        old_data = comment_data.read()
        new_data = ""
        prev_span_end = 0
        for f in re.finditer(r"<br id=\".\">", old_data):
            span = f.span()
            delta = span[1] - span[0]
            new_data = f'{new_data}{old_data[prev_span_end:span[0]]}{" " * delta}'
            prev_span_end = span[1]
        new_data = f"{new_data}{old_data[prev_span_end:]}"
    with open(comment_file, "w", encoding="utf-8") as output_file:
        output_file.write(new_data)
    comment_root = ET.parse(comment_file).getroot()
    comment_text = ""
    for line in comment_root.find("body").find("p").findall("span"):
        comment_text = f"{comment_text}\n{line.text}"
    return comment_text


def export_tpe(entries: dict, output_path: str, type_tags: list, rat_tags: list):
    """exports the email .csv"""
    with open(output_path, "w+", encoding="utf-8") as output_file:
        # header
        output_file.write("document,email_id,email_subject,")
        for tag in itertools.chain(type_tags, rat_tags):
            output_file.write(f"\"{tag}\",")
        output_file.write("\n")
        # data entries
        for doc_id, entries in entries.items():
            for entry in entries:
                # email meta data
                email_id = entry["id"]
                email_subject = entry["subject"].replace('"', "'")
                output_file.write(f'{doc_id},{email_id},"{email_subject}",')
                # Decision type tags.
                for tag in type_tags:
                    output_file.write("1," if tag in entry["type_tags"] else "0,")
                # rationale types
                for tag in rat_tags:
                    output_file.write("1," if tag in entry["rationale_tags"] else "0,")
                output_file.write("\n")


def export_tpq(entries: dict, output_path: str, rat_tags: list):
    """exports the quote .csv"""
    with open(output_path, "w+", encoding="utf-8") as output_file:
        # header
        output_file.write("document,email_id,email_subject,quote,comment,")
        for tag in rat_tags:
            output_file.write(f"\"{tag}\",")
        output_file.write("\n")
        # entries

        for doc_id, entries in entries.items():
            for entry in entries:
                email_id = entry["email_id"]
                email_subject = entry["email_subject"]
                quote = entry["quote"].replace('"', "'")
                comment = entry["comment"].replace('"', "'")
                output_file.write(
                    f'{doc_id},{email_id},"{email_subject}","{quote}","{comment}",'
                )
                for tag in rat_tags:
                    output_file.write("1," if tag in entry["tags"] else "0,")
                output_file.write("\n")


def parse(
    atlas_path_in: str,
    atlas_path_out: str,
    output_path1: str,
    output_path2: str,
    dec_types: list,
    rat_types: list,
):
    """Parses the atlas project to the two datafiles."""
    a_root = load_atlas_as_tree(atlas_path_in, atlas_path_out)
    a_quotes: dict = load_all_quotes(a_root)
    tpe, tpq = generate_data(a_root, a_quotes)
    export_tpe(tpe, output_path1, dec_types, rat_types)
    export_tpq(tpq, output_path2, rat_types)


ATLAS_PATH_IN = "./data/the_best_exported_data/ds.atlproj"
ATLAS_PATH_OUT = "./data/the_best_exported_data/extract/"
OUTPUT_PATH = "./data/the_best_exported_data/export_emails.csv"
OUTPUT_PATH2 = "./data/the_best_exported_data/export_quotes.csv"
DEC_TYPES = [
    "existence-behavioral",
    "existence-structural",
    "process",
    "property",
    "technology",
]
RAT_TYPES = [
    "Assumption",
    "Constraints",
    "Decision Rule",
    "Domain Experience",
    "Solution Benefits and Drawbacks",
    "Solution Evaluation",
    "Solution Risks and Non-Risks",
    "Solution Trade-off",
    "Solution Comparison",
    "Other",
]

if __name__ == "__main__":
    parse(
        ATLAS_PATH_IN, ATLAS_PATH_OUT, OUTPUT_PATH, OUTPUT_PATH2, DEC_TYPES, RAT_TYPES
    )
