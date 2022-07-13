# The goal: generate a CSV that contains: the following:
#   - unique id
#   - email id
#   - email subject
#   - email tags
#   - quote
#   - quote classes
# To do this we have to:

# Note: you might have to remove HTML tags to make this work; use the following to search them and remove them:
#   &nbsp;
#   <br id="...">
# MAKE SURE TO REPLACE THEM WITH EMPTY SPACES OF EQUAL LENGTH; ELSE THE ATLAS INDICES MESS UP.

import os
from zipfile import ZipFile
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element

#   0) Load the atlas project.
def load_atlas_as_tree(atlas_project_path: str, atlas_output_path: str) -> ET.Element:
    """Loads the atlas project as an ET tree."""
    with ZipFile(atlas_project_path, "r") as atlas_zip:
        atlas_zip.extractall(atlas_output_path)
    tree = ET.parse(os.path.join(atlas_output_path, "project.aprx"))
    root = tree.getroot()
    return root


ATLAS_PATH_IN = "./data/atlas_to_csv/ds.atlproj"
ATLAS_PATH_OUT = "./data/atlas_to_csv/extract/"
a_root = load_atlas_as_tree(ATLAS_PATH_IN, ATLAS_PATH_OUT)

#   1) Load all quotes
def load_all_quotes(root: Element) -> dict:
    quotes = {}
#       a. load the tags (id-to-name)
    tags = {tg.get("id"): tg.get("name") for tg in root.find("tags").findall("tag")}
#       b. load the tagQuoteLinks (quote_id-to-tag_id)
    quote_tags = {}
    for tql in root.find("links").findall("tagQuotLink"):
        trg = tql.get("target")
        src = tags[tql.get("source")]
        if trg in quote_tags:
            quote_tags[trg].append(src)
        else:
            quote_tags[trg] = [src]
#       c. load quotations per document (unique id-to-segmentindices)
    for doc in root.find("documents").findall("document"):
        doc_id = doc.get("id")
        quotes[doc_id] = []
        for qt in doc.find("layer").findall("quotation"):
            try:
                tloc = qt.find("location").find("segmentedTextLoc")
                qt_entry  = {
                    "thread": doc.get("name"),
                    "id": qt.get("id"),
                    "sSegment": int(tloc.get("sSegment")),
                    "sOffset": int(tloc.get("sOffset")),
                    "eSegment": int(tloc.get("eSegment")),
                    "eOffset": int(tloc.get("eOffset")),
    #           - and apply the results from a and b on it.
                    "tags": quote_tags[qt.get("id")]
                }
                quotes[doc_id].append(qt_entry)
                if (qt_entry["sSegment"] != qt_entry["eSegment"]):
                    print(f'{qt_entry["sSegment"]=}, {qt_entry["eSegment"]=}')
            except KeyError:
                qid = qt.get("id")
                print(f'Failed on {qid}')
        quotes[doc_id].sort(key=lambda x: x["sSegment"])
#       d. now we have {doc_id: [{quote_id, segmentindices, tags}]}
    return quotes
a_quotes = load_all_quotes(a_root)

def generate_data(root: Element) -> list:
    #   2) load all document content guids
    cnt_to_doc = {cnt.get("id"): cnt.get("loc") for cnt in a_root.find("contents").findall("content")}

    #   3) iterate through results of 1
    data_entries = []
    for doc_id, quotes in a_quotes.items():
    #       a. transform doc_id to cnt_id (s.t. e.g. "doc_10" == "cnt_10")
        cnt_id = f'cnt_{doc_id[4:]}'
        doc_loc = cnt_to_doc[cnt_id]
        print(f'{cnt_id}: {doc_loc}')
        if len(quotes) == 0:
            continue
        doc_file = f'{ATLAS_PATH_OUT}contents/{doc_loc}/content'
        parser = ET.XMLParser()
        parser.entity["nbsp"] = ' '
    #       b. iterate through the document's body and through the quotes simultaneously.
        d_root = ET.parse(doc_file, parser = parser).getroot()
        current_email_id = ""
        current_email_subject = ""
        current_email_tags = ""
        email_id_flag = False
        email_subject_flag = False
        email_tags_flag = False
        current_quote_index = 0
        for ele in iter(d_root.find("body")):
    #           i: if the element's text starts with, store them
    #               - email id:
    #               - subject:
    #               - tags:
            try:
                text = ele.find("span").text.lower()
            except AttributeError:
                text = ele.find("strong").text.lower()
            if text.startswith("email id:"):
                email_id_flag = True
                continue
            elif text.startswith("subject:"):
                email_subject_flag = True
                continue
            elif text.startswith("tags:"):
                email_tags_flag = True
                continue
            elif email_id_flag:
                email_id_flag = False
                current_email_id = text
                continue
            elif email_subject_flag:
                email_subject_flag = False
                current_email_subject = text
                continue
            elif email_tags_flag:
                email_tags_flag = False
                current_email_tags = text
                continue
        #           ii: if the element-id + 1 equals the quote segment start, then:
            current_quote = quotes[current_quote_index]
            eid = int(ele.get("id")) + 1
            while eid == current_quote["sSegment"]:
                quote = text[current_quote["sOffset"]:current_quote["eOffset"]]
            #               - create new data entry
                new_entry = {
                    "email_thread": current_quote["thread"],
                    "email_id": current_email_id,
                    "email_subject": current_email_subject,
                    "email_tags": current_email_tags,
                    "quote_text": quote,
                    "quote_tags": current_quote["tags"],
                }
                data_entries.append(new_entry)
                current_quote_index += 1
                if current_quote_index >= len(quotes):
                    break
                current_quote = quotes[current_quote_index]
            if current_quote_index >= len(quotes):
                break
    return data_entries

my_results = generate_data(a_root)
print(f'{len(my_results)=}')

#   4) export all data entries
OUTPUT_PATH = "./data/atlas_to_csv/export.csv"
INTERESTING_TAGS = [
    "existence-behavioral",
    "existence-structural",
    "process",
    "property",
    "technology",
]
def export_data(results: list, root: Element):
    with open(OUTPUT_PATH, "w", encoding="utf-8") as output_file:
        output_file.write("thread,email_id,email_subject,")
        for tag in INTERESTING_TAGS:
            output_file.write(f'{tag}, ')
        output_file.write("quote_text,")
        quote_tags = [tg.get("name") for tg in root.find("tags").findall("tag")]
        for tgn in quote_tags:
            output_file.write(f"{tgn},")
        output_file.write("\n")
        for entry in results:
            thread_name = entry["email_thread"]
            email_id = entry["email_id"]
            email_subject = entry["email_subject"]
            output_file.write(f"{thread_name},{email_id},\"{email_subject}\",")
#       b. output 0/1 per existing tag
            for tg in INTERESTING_TAGS:
                if tg in entry["email_tags"]:
                    output_file.write("1,")
                else:
                    output_file.write("0,")
            entry_quote = entry["quote_text"].replace("\"", "")
            output_file.write(f'\"{entry_quote}\",')
#       c. output 0/1 per existing class
            for qtg in quote_tags:
                if qtg in entry["quote_tags"]:
                    output_file.write("1,")
                else: 
                    output_file.write("0,")
            output_file.write("\n")

export_data(my_results, a_root)
