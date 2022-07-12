"""asdf"""

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


def to_threads(data):
    """asdf"""
    threads = {}
    tags = {}
    for row in data:
        # merges threads
        sub: str = row["subject"]
        if sub[0:4].lower() == "re: ":
            sub = sub[4:]
        if sub in threads:
            threads[sub].append(row)
        else:
            threads[sub] = [row]
            tags[sub] = {}
        # merges tags
        for tag in row["tags"]:
            if tag in tags[sub]:
                tags[sub][tag] += 1
            else:
                tags[sub][tag] = 1
    # Merges results of both dictionaries.
    return {
        sub: {"emails": emails, "tags": tgs}
        for (sub, emails), (_, tgs) in zip(threads.items(), tags.items())
    }


def export(results, tags, output_file):
    """sds"""
    with open(output_file, "w", encoding="utf-8") as output_file:
        output_file.write("Subject,Email-Count,Email-IDs,")
        for tag in tags:
            output_file.write(f"{tag},")
        output_file.write("\n")
        for sub, row in results.items():
            output_file.write(f'"{sub}",{len(row["emails"])},')
            email_ids = []
            for mail in row["emails"]:
                email_ids.append(mail["id"])
            output_file.write(f'"{email_ids}",')
            for tag in tags:
                if tag in row["tags"]:
                    output_file.write(f'{row["tags"][tag]},')
                else:
                    output_file.write("0,")
            output_file.write("\n")


DATA_PATH = "./data/cleaner_data/AKEmails.csv"
OUTPUT_PATH = "./data/cleaner_data/AKEmails-export.csv"
INTERESTING_TAGS = [
    "Architecturally Irrelevant",
    "Description Reference",
    "Discussion on Issue",
    "FQAB Group",
    "Influence of Architectural Issues",
    "Information Source",
    "Issue Elaboration",
    "Issue Relationship",
    "Other Reference",
    "Release Group",
]


my_data = load_dataset(DATA_PATH, INTERESTING_TAGS)
my_results = to_threads(my_data)
export(my_results, INTERESTING_TAGS, OUTPUT_PATH)

print(json.dumps(my_results, indent=4))
