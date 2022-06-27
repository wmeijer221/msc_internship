"""finds issues in text file, but better."""

import json
from copy import deepcopy
import pandas as pd


def load_issues(issue_file_path: str) -> list:
    """Loads issues from file"""
    dataframe = pd.read_excel(issue_file_path)
    return [row["issues key"] for (_, row) in dataframe.iterrows()]


def find_issues_in(iss: list, file_path: str) -> dict:
    """Finds issues in text"""
    results = {}
    found = 0
    with open(file_path, "r", encoding="utf-8") as data_file:
        current_message = {}
        for index, line in enumerate(data_file):
            if index % 2000 == 0:
                print(f"{index=}")
            the_line = line.strip()
            if the_line.startswith("Message id: "):
                current_message["id"] = the_line[len("Message id: ") :]
            elif the_line.startswith("Subject: "):
                current_message["subject"] = the_line[len("Subject: ") :]
            elif the_line.startswith("Date: "):
                current_message["date"] = the_line[len("Date: ") :]
            elif the_line.startswith("Sent from: "):
                current_message["sent_from"] = the_line[len("Sent from: ") :]
            elif the_line.startswith("Tags: "):
                current_message["tags"] = [
                    tag.strip() for tag in the_line[len("Tags: ") :].split(",")
                ]
            for issue in iss:
                offset = the_line.find(issue)
                if offset == -1:
                    continue
                if not issue in results:
                    results[issue] = []
                new_entry = deepcopy(current_message)
                new_entry["line"] = the_line
                new_entry["offset"] = offset
                results[issue].append(new_entry)
                found += 1
    return results, found


ISSUE_FILE_PATH = "./data/IssuesDatasetArchitectural.xlsx"
TEXT_FILE_PATH = "./data/find_issues_in_text/better_text.txt"
OUTPUT_PATH = "./data/find_issues_in_text/better_output.json"

issues = load_issues(ISSUE_FILE_PATH)
found_issues, count = find_issues_in(issues, TEXT_FILE_PATH)

print(f"{count=}")
print(f"{len(found_issues.keys())=}")

with open(OUTPUT_PATH, "w", encoding="utf-8") as output_file:
    output_file.write(json.dumps(found_issues, indent=4))
