"""Exports atlas ti as a CSV file."""


import os
from zipfile import ZipFile
import xml.etree.ElementTree as ET


def export_to_csv(atlas_project_path: str, atlas_extract_path: str, output_path: str):
    """Exports atlas ti as a CSV file."""

    _, root = _load_atlas_as_tree(atlas_project_path, atlas_extract_path)
    atlas_tag_quotes = _load_atlas_tag_quotes(root)
    quotes = _load_quotes_with_mail(atlas_tag_quotes, root, atlas_extract_path)
    quotes = _add_tags(quotes, root)

    if not os.path.exists(os.path.dirname(output_path)):
        os.mkdir(os.path.dirname(output_path))

    _export(quotes, f"{output_path}-complete.csv")


def _load_atlas_as_tree(atlas_project_path: str, atlas_output_path: str) -> ET.Element:
    """unzips atlas project and retursn the tree and root XML objects."""
    with ZipFile(atlas_project_path, "r") as atlas_zip:
        atlas_zip.extractall(atlas_output_path)
    tree = ET.parse(os.path.join(atlas_output_path, "project.aprx"))
    root = tree.getroot()
    return tree, root


def _load_atlas_tag_quotes(root: ET.Element) -> dict:
    """Loads dict where key is a doc id having a list of respective quote metadata objects."""
    tag_quotes = {}
    for doc in root.find("documents").findall("document"):
        layer = doc.find("layer")

        if layer is None:
            continue

        quotes = layer.findall("quotation")
        entries = [None] * len(quotes)

        for index, quotation in enumerate(quotes):
            quotation_location = quotation.find("location").find("segmentedTextLoc")

            quote_entry = {"id": quotation.get("id")}

            for key, value in quotation_location.items():
                quote_entry[key] = value

            entries[index] = quote_entry

        tag_quotes[doc.get("id")] = entries

    return tag_quotes


def _load_quotes_with_mail(
    quotes_per_doc: dict, root: ET.Element, atlas_extract_path: str
) -> list:
    """Identifies the email in which the quote was made."""
    results = []

    base_path: str = f"{atlas_extract_path}/contents/"
    cnt_id_to_doc_id = _build_cnt_id_to_doc_id(root)

    for content in root.find("contents").findall("content"):
        # loads doc quotes if existing.
        content_id = content.get("id")
        if content_id not in cnt_id_to_doc_id:
            continue
        doc_id = cnt_id_to_doc_id[content.get("id")]
        quotes = quotes_per_doc[doc_id]
        quotes.sort(key=lambda x: int(x["sSegment"]))
        sub_results = [None] * len(quotes)

        # Opens respective content file.
        loc = content.get("loc")
        body = ET.parse(f"{base_path}/{loc}/content").getroot().find("body")

        # iterates through all HTML headers to
        # find email headers and quotes.
        current_mail = None
        current_quote_index = 0
        for element in iter(body):
            # sets new email name.
            if element.tag == "h2":
                current_mail = element.find("span").text
                continue

            # skips unquotes elements.
            if (
                int(element.get("id"))
                < int(quotes[current_quote_index]["sSegment"]) - 1
            ):
                continue

            # Adds all quotes inside this text element.
            caught_up = False
            while not caught_up:
                new_quote = quotes[current_quote_index]
                new_quote["doc_id"] = doc_id
                new_quote["email_id"] = current_mail
                new_quote["quote_text"] = element.find("span").text[
                    int(new_quote["sOffset"]) : int(new_quote["eOffset"])
                ]
                sub_results[current_quote_index] = new_quote
                current_quote_index += 1
                caught_up = (
                    current_quote_index >= len(quotes)
                    or int(element.get("id"))
                    < int(quotes[current_quote_index]["sSegment"]) - 1
                )

            # stops if no more quote are saught.
            if current_quote_index >= len(quotes):
                break

        results.extend(sub_results)
    return results


def _build_cnt_id_to_doc_id(root: ET.Element) -> dict:
    """Returns a dictionary that points from content id to document id."""
    cnt_id_to_doc_id = {}
    for content in root.find("contents").findall("content"):
        content_id = content.get("id")
        for medium in root.find("media").findall("medium"):
            if medium.get("content") != content_id:
                continue
            medium_id = medium.get("id")
            for doc in root.find("documents").findall("document"):
                if doc.get("medium") != medium_id:
                    continue
                cnt_id_to_doc_id[content_id] = doc.get("id")
                break
            break
    return cnt_id_to_doc_id


def _add_tags(quotes: list, root: ET.Element) -> list:
    """Adds tag id and descriptor to the quotes"""
    tag_id_to_tag = {
        tag.get("id"): tag.get("name") for tag in root.find("tags").findall("tag")
    }

    # loads tag id to tag_data list.
    quote_to_tag = {}
    for quote in root.find("links").findall("tagQuotLink"):
        target = quote.get("target")
        id = quote.get("source")
        name = tag_id_to_tag[quote.get("source")]
        if target not in quote_to_tag:
            quote_to_tag[target] = {
                "id": id,
                "name": name,
            }
            continue
        replaced = quote_to_tag[target]
        replaced["id"] = f'{replaced["id"]}; {id}'
        replaced["name"] = f'{replaced["name"]}; {name}'

    # adds tag ids and tag names to items.
    for index, quote in enumerate(quotes):
        if quote.get("id") not in quote_to_tag:
            continue

        tag_data = quote_to_tag[quote.get("id")]
        quote["tag_id"] = tag_data["id"]
        quote["tag_name"] = tag_data["name"]
        quotes[index] = quote

    return quotes


def _export(quotes: list, output_path: str):
    """exports list of quotes to CSV format."""
    with open(output_path, "w", encoding="utf-8") as output_file:
        column_names = list(quotes[0].keys())
        output_file.write(f"{str(column_names)[1:-1]}\n")
        for quote in quotes:
            for value in quote.values():
                o_value = str(value).replace('"', "").replace("'", "")
                output_file.write(f"'{o_value}', ")
            output_file.write("\n")


if __name__ == "__main__":
    ATLAS_PROJECT_PATH = "./data/MSc_Internship-2022.atlproj"
    ATLAS_EXTRACT_PATH = "./data/atlas_extract/"
    OUTPUT_PATH = "./data/csvs/MSc_Internship-2022"

    export_to_csv(ATLAS_PROJECT_PATH, ATLAS_EXTRACT_PATH, OUTPUT_PATH)
