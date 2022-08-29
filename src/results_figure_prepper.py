import csv


def load_dataset(data_path: str, interesting_tags: list) -> list:
    """sdf"""
    data = []
    with open(data_path, "r", encoding="utf-8") as csv_data:
        for _, ele in enumerate(csv.reader(csv_data, delimiter=",", quotechar='"')):
            tags = []
            for tag in ele[5][1:-1].split(", "):
                for itag in interesting_tags:
                    if tag.lower() == itag.lower():
                        tags.append(tag)
            if len(tags) > 0:
                data.append({"id": ele[1], "subject": ele[3], "tags": tags})
    return data


def reformat(data_set: list, interesting_tags: list, output_path: str):
    with open(output_path, "w", encoding="utf-8") as output_file:
        # Header string
        output_file.write("ID,Subject,")
        for tag in interesting_tags:
            output_file.write(f'"{tag}",')
        output_file.write("\n")
        # Content
        for row in data_set:
            subject = row["subject"].replace('"',"'")
            output_file.write(f'\"{row["id"]}\",\"{subject}\",')
            tgs = row["tags"]
            for tag in interesting_tags:
                if tag in tgs:
                    output_file.write("1,")
                else:
                    output_file.write("0,")
            output_file.write("\n")


DATA_PATH = "./data/data_prepper/the_data.csv"
OUTPUT_PATH = "./data/data_prepper/the_export.csv"
INTERESTING_TAGS = [
    "Architecturally Irrelevant",
    "Release Group",
    "Feature Group",
    "Quality Group",
    "Issue Elaboration",
    "Discussion Venue",
    "Issue Impact",
    "Resource",
    "Other Issue Reference",
    "Other",
    # "Group",
    # "Issue Reference"
]

ds = load_dataset(DATA_PATH, INTERESTING_TAGS)
reformat(ds, INTERESTING_TAGS, OUTPUT_PATH)
