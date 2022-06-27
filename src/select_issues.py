"""asdf"""

from math import floor
import random
import re
import json

with open(
    "./data/find_issues_in_text/output.json", "r", encoding="utf-8"
) as input_file:
    json_data = json.loads(input_file.read())

print(f"{len(json_data.keys())} referenced issues")


with open("./data/find_issues_in_text/text.txt", "r", encoding="utf-8") as text_file:
    td = text_file.readlines()

meta_datas = {}

# finds meta data of issue-referencing emails.
for key, appearances in json_data.items():
    num_appearances = len(appearances)
    random_selection = floor(random.random() * num_appearances)
    selection = appearances[random_selection]
    search_index = selection[1] - 1

    PATTERN = r"(\t)*Body---->>>"
    found_meta = False
    tries = 0
    while not found_meta and tries < 50:
        search_line = td[search_index]
        found_meta = len(re.findall(PATTERN, search_line)) > 0
        search_index -= 1
        tries += 1

    if not found_meta:
        continue

    meta_data = td[search_index - 5 : search_index + 1]

    meta_datas[key] = meta_data


# creates search query for subjects.
print(
    f"{len(meta_datas)=}; {floor(len(meta_datas) / len(json_data.keys()) * 10000) / 100}% hits."
)
query = ""
for key, value in meta_datas.items():
    subject = value[1].strip()[9:]
    query += f'(subject:"{subject}") OR '
query = query[:-4]

with open("./data/find_issues_in_text/query.txt", "w", encoding="utf-8") as output_file:
    output_file.write(query)

with open("./data/find_issues_in_text/mail_names.csv", "w", encoding="utf-8") as of2:
    for key, value in meta_datas.items():
        of2.write(f"\"{key}\", \"{value[1].strip()[9:]}\"\n")
