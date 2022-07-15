import csv
import json


def load_dataset(data_path: str, interesting_tags: list) -> list:
    """sdf"""
    data = []
    with open(data_path, "r", encoding="utf-8") as csv_data:
        for _, ele in enumerate(csv.reader(csv_data, delimiter=",", quotechar='"')):
            tags = []
            for tag in ele[5][1:-1].split(", "):
                for itag in interesting_tags:
                    if tag == itag:
                        tags.append(tag)
            if len(tags) > 0:
                data.append({"id": ele[1], "subject": ele[3], "tags": tags})
    return data


def export(ds: list, output_path: str, tags: list):
    with open(output_path, "w", encoding="utf-8") as output_file:
        output_file.write("Subject,Email-ID,")
        for tag in tags:
            output_file.write(f"{tag},")
        output_file.write("\n")
        for entry in ds:
            entry_id = entry["id"]
            entry_subject = entry["subject"]
            output_file.write(f'{entry_id},"{entry_subject}",')
            entry_tags = entry["tags"]
            for tag in tags:
                if tag in entry_tags:
                    output_file.write("1,")
                else:
                    output_file.write("0,")
            output_file.write("\n")


DATA_PATH = "./data/cleaner_data/AKEmails.csv"
OUTPUT_PATH = "./data/cleaner_data/AKEmails-export2.csv"
INTERESTING_TAGS = [
    "existence-behavioral",
    "existence-structural",
    "process",
    "property",
    "technology",
]

export(load_dataset(DATA_PATH, INTERESTING_TAGS), OUTPUT_PATH, INTERESTING_TAGS)
