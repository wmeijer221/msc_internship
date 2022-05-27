"""Calculates simple co-occurrence of tags."""

import json
import os
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET
from zipfile import ZipFile


def load_atlas_as_tree(atlas_project_path: str, atlas_output_path: str) -> ET.Element:
    """Loads the atlas project as an ET tree."""
    with ZipFile(atlas_project_path, "r") as atlas_zip:
        atlas_zip.extractall(atlas_output_path)
    tree = ET.parse(os.path.join(atlas_output_path, "project.aprx"))
    root = tree.getroot()
    return root, tree


def load_tags(root: ET.Element) -> dict:
    """loads tags from root."""
    doc_tags = {}

    for document in root.find("documents").findall("document"):
        layer = document.find("layer")
        if layer is None:
            continue

        for quotation in layer.findall("quotation"):
            quotation_location = quotation.find("location").find("segmentedTextLoc")

            q_data = {
                "quote_id": quotation.get("id"),
                "doc_id": document.get("id"),
                "med_id": document.get("medium"),
            }

            for key, value in quotation_location.items():
                q_data[key] = value

            doc_tags[q_data["quote_id"]] = q_data

    return doc_tags


def append_tag_data(tags: dict, root: ET.Element) -> dict:
    """Adds tag ids to the tag entries."""
    for tag_link in root.find("links").findall("tagQuotLink"):
        try:
            new_entry = tags[tag_link.get("target")]
        except KeyError:
            continue

        new_entry["tag_id"] = tag_link.get("source")
        tags[new_entry["quote_id"]] = new_entry

    return tags


def append_mail_data(tags: dict, root: ET.Element, atlas_path: str) -> dict:
    """Adds what email the tags are inside of to the tag list."""
    reorder = {value["med_id"]: [] for value in tags.values()}
    for tag in tags.values():
        reorder[tag["med_id"]].append(tag)

    cnt_id_to_cnt = {
        content.get("id"): content
        for content in root.find("contents").findall("content")
    }

    med_to_content = {
        medium.get("id"): cnt_id_to_cnt[medium.get("content")]
        for medium in root.find("media").findall("medium")
    }

    for medium_id, doc_tags in reorder.items():
        content = med_to_content[medium_id]

        doc_path = os.path.join(atlas_path, "contents", content.get("loc"), "content")
        doc_root = ET.parse(doc_path).getroot()

        doc_tags.sort(key=lambda x: int(x["sSegment"]))
        cur_tag_index = 0

        cur_email = None

        for element in iter(doc_root.find("body")):
            if element.tag == "h2":
                cur_email = element.find("span").text
                continue

            if int(element.get("id")) < int(doc_tags[cur_tag_index]["sSegment"]) - 1:
                continue

            caught_up = False
            while not caught_up:
                new_tags = doc_tags[cur_tag_index]
                new_tags["email_id"] = cur_email
                tags[new_tags["quote_id"]] = new_tags
                cur_tag_index += 1
                caught_up = cur_tag_index >= len(doc_tags) or int(
                    element.get("id")
                ) + 1 < int(doc_tags[cur_tag_index]["sSegment"])

            if cur_tag_index >= len(doc_tags):
                break

    return tags


def calculate_tag_occurrence_using_key(tags: dict, key: str) -> dict:
    """Calculates the numbers of times a tag occurs, grouped by the given key."""
    co_occurrence = {}

    for tag_id, tag in tags.items():
        group = tag[key]
        tag_id = tag["tag_id"]

        try:
            target_group = co_occurrence[group]
        except KeyError:
            co_occurrence[group] = {}
            target_group = co_occurrence[group]

        try:
            target_group[tag_id] += 1
        except KeyError:
            target_group[tag_id] = 1

    return co_occurrence


def calculate_co_occurrence(occurrence: dict) -> dict:
    """Returns the co_occurrence of items."""
    co_occurrence = {}

    for doc_sightings in occurrence.values():
        for tag_id in doc_sightings.keys():

            try:
                co_occurrence[tag_id]
            except KeyError:
                co_occurrence[tag_id] = {}

            for other_tag_id, other_sighting_count in doc_sightings.items():
                try:
                    co_occurrence[tag_id][other_tag_id] += other_sighting_count
                except KeyError:
                    co_occurrence[tag_id][other_tag_id] = other_sighting_count

            co_occurrence[tag_id][tag_id] -= 1

    return co_occurrence


if __name__ == "__main__":
    ATLAS_PROJECT_FILE = "./data/MSc_Internship-2022.atlproj"
    ATLAS_EXTRACT_PATH = "./data/atlas_extract/"

    atlas_root, atlas_tree = load_atlas_as_tree(ATLAS_PROJECT_FILE, ATLAS_EXTRACT_PATH)

    proj_tags = load_tags(atlas_root)
    proj_tags = append_tag_data(proj_tags, atlas_root)

    proj_tags = append_mail_data(proj_tags, atlas_root, ATLAS_EXTRACT_PATH)

    doc_occurrence = calculate_tag_occurrence_using_key(proj_tags, "doc_id")
    doc_co_occurrence = calculate_co_occurrence(doc_occurrence)

    mail_occurrence = calculate_tag_occurrence_using_key(proj_tags, "email_id")
    mail_co_occurrence = calculate_co_occurrence(doc_occurrence)

    output = {
        "proj_tags": proj_tags,
        "doc_occurrence": doc_occurrence,
        "doc_co_occurrence": doc_co_occurrence,
        "email_occurrence": mail_occurrence,
        "email_co_occurrence": mail_co_occurrence,
    }

    print(json.dumps(output, indent=4))

    # plt.imshow(doc_co_occurrence,interpolation='nearest', cmap='Reds')
    # plt.colorbar()
    # plt.show()
