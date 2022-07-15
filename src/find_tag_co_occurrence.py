"""Calculates simple co-occurrence of tags."""

import json
import os
import xml.etree.ElementTree as ET
from zipfile import ZipFile
import networkx as nx
import matplotlib.pyplot as plt
from scipy.stats import chi2_contingency


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
        if "tag_id" not in tag:
            continue

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


def filter_ignored(tags: dict, ignored: list) -> dict:
    """Filters ignored tags out of the co_occurrence dict."""
    # removes origin tags.
    for ignored_tag in ignored:
        if ignored_tag in tags:
            del tags[ignored_tag]
    # removes target tags
    for tag, occurrences in tags.items():
        for ignored_tag in ignored:
            if ignored_tag in occurrences:
                del occurrences[ignored_tag]
        tags[tag] = occurrences
    return tags


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


def chi_square(co_occurrence: dict):
    """Performs chi square test."""
    sorted_keys = list(co_occurrence.keys())
    sorted_keys.sort(key=lambda x: int(x[2:]))

    matrix = [None] * len(sorted_keys)
    for i, current_key in enumerate(sorted_keys):
        matrix[i] = [0] * len(sorted_keys)
        for j, other_key in enumerate(sorted_keys):
            try:
                matrix[i][j] = co_occurrence[current_key][other_key]
            except KeyError:
                continue  # ignored

    stat, p, dof, expected = chi2_contingency(matrix)

    print(stat)
    print(p < 0.05)
    print(dof)
    print(matrix)
    print(expected)


def draw_co_occurrence_network(
    co_occurrence: dict, name: str, root: ET.Element, results_path: str
):
    """Draws a co-occurrence network."""
    node_scalar_factor = 2000
    edge_scalar_factor = 0.5

    graph = nx.Graph()
    for source, targets in co_occurrence.items():
        source_id = int(source[2:])
        for target, weight in targets.items():
            target_id = int(target[2:])

            if weight == 0:
                continue

            if source_id == target_id:
                graph.add_node(source_id, size=weight)
            else:
                graph.add_edge(source_id, target_id, weight=weight)

    # loads tags from atlas project
    tag_id_to_name_map = {
        int(tag.get("id")[2:]): tag.get("name")
        for tag in root.find("tags").findall("tag")
    }

    # drawing custimization
    plt.figure(1, figsize=(80, 50), dpi=20)
    pos = nx.spring_layout(graph, k=0.42, iterations=50)
    nx.draw(
        graph,
        pos,
        # with_labels=True,
        node_color="#bababa",
        font_size=46,
        font_weight="bold",
        labels={node: tag_id_to_name_map[node] for node in graph.nodes()},
        node_size=[v * node_scalar_factor for v in graph.nodes()],
        width=[graph[s][t]["weight"] * edge_scalar_factor for s, t in graph.edges()],
    )
    plt.savefig(f"{results_path}/results-{name}.png")
    plt.clf()


def draw_co_occurrence_heatmap(
    co_occurrence: dict, name: str, root: ET.Element, results_path: str
):
    """Exports data in heatmap format."""
    # builds matrix data structure from dict.
    matrix = [[0] * len(co_occurrence) for i in range(len(co_occurrence))]
    key_to_index = {key: index for index, key in enumerate(co_occurrence.keys())}
    for key, occurrences in co_occurrence.items():
        index = key_to_index[key]
        for other_key, count in occurrences.items():
            other_index = key_to_index[other_key]
            matrix[index][other_index] = count

    # exports data.
    plt.imshow(matrix, cmap="hot", interpolation="nearest")
    plt.savefig(f"{results_path}/results-{name}.png")
    plt.clf()


def export_to_csv(co_occurrence: dict, name: str, output_path: str, root: ET.Element):
    # builds matrix data structure.
    matrix = [[0] * len(co_occurrence) for i in range(len(co_occurrence))]
    key_to_index = {key: index for index, key in enumerate(co_occurrence.keys())}
    for key, occurrences in co_occurrence.items():
        index = key_to_index[key]
        for other_key, count in occurrences.items():
            other_index = key_to_index[other_key]
            matrix[index][other_index] = count

    # Loads tags
    index_to_key = {
        key_to_index[tag.get("id")]: tag.get("name")
        for tag in root.find("tags").findall("tag")
        if tag.get("id") in key_to_index
    }

    with open(
        f"{output_path}/{name}-results.csv", "w", encoding="utf-8"
    ) as output_file:
        output_file.write(
            f"Co-Occurrence Matrix: {name}, {str([index_to_key[i] for i in range(len(matrix))])[1:-1]}\n"
        )
        for index, row in enumerate(matrix):
            output_file.write(f"{index_to_key[index]}, {str(row)[1:-1]}\n")


def export_results(co_occurrence: dict, name: str, output_path: str, root: ET.Element):
    """exports results."""
    export_to_csv(co_occurrence, f"{name}-co-occurrence", output_path, root)
    draw_co_occurrence_network(co_occurrence, f"{name}-graph", root, output_path)
    draw_co_occurrence_heatmap(co_occurrence, f"{name}-heatmap", root, output_path)


def find_tag_co_occurrence(
    atlas_project_file: str,
    atlas_extract_path: str,
    ignored_tags_file: str,
    results_path: str,
):
    """Finds co-occurrence and exports respective files."""
    # loads atlas.ti project as xml.
    atlas_root, _ = load_atlas_as_tree(atlas_project_file, atlas_extract_path)

    # loads project tag data.
    proj_tags = load_tags(atlas_root)
    proj_tags = append_tag_data(proj_tags, atlas_root)
    proj_tags = append_mail_data(proj_tags, atlas_root, atlas_extract_path)

    # Co-occurrence calculations for co-occurrence in individual
    # mails and complete mailing threads.
    with open(ignored_tags_file, "r", encoding="utf-8") as input_file:
        ignored_tags = [tag.strip() for tag in input_file.readlines()]

    thread_occurrence = calculate_tag_occurrence_using_key(proj_tags, "doc_id")
    thread_occurrence = filter_ignored(thread_occurrence, ignored_tags)
    thread_co_occurrence = calculate_co_occurrence(thread_occurrence)
    export_results(thread_co_occurrence, "thread", results_path, atlas_root)
    # doc_chi_results = chi_square(doc_co_occurrence)

    mail_occurrence = calculate_tag_occurrence_using_key(proj_tags, "email_id")
    mail_occurrence = filter_ignored(mail_occurrence, ignored_tags)
    mail_co_occurrence = calculate_co_occurrence(thread_occurrence)
    export_results(mail_co_occurrence, "mail", results_path, atlas_root)

    # Outputs all of the gathered data.
    output = {
        "proj_tags": proj_tags,
        "ignored_tags": ignored_tags,
        "thread_occurrence": thread_occurrence,
        "thead_co_occurrence": thread_co_occurrence,
        "email_occurrence": mail_occurrence,
        "email_co_occurrence": mail_co_occurrence,
    }

    with open(f"{results_path}/results.json", "w", encoding="utf-8") as output_file:
        output_file.write(json.dumps(output, indent=4))


if __name__ == "__main__":
    ATLAS_PROJECT_FILE = "./data/MSc_Internship-2022.atlproj"
    ATLAS_EXTRACT_PATH = "./data/atlas_extract/"
    RESULTS_PATH = "./data/co_occurrence"
    IGNORED_TAGS_FILE = f"{RESULTS_PATH}/ignored_tags.txt"

    find_tag_co_occurrence(
        ATLAS_PROJECT_FILE, ATLAS_EXTRACT_PATH, IGNORED_TAGS_FILE, RESULTS_PATH
    )
