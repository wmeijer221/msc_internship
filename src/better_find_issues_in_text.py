"""finds issues in text file, but better."""

import json
import re
from copy import deepcopy
import pandas as pd


def load_issues(issue_file_path: str) -> list:
    """Loads issues from file"""
    dataframe = pd.read_excel(issue_file_path)
    issues = []
    for (_, row) in dataframe.iterrows():
        issue = row["issues key"].strip()
        issues.append(issue)
        spl = issue.split("-")
        if spl[0] != "HDFS":
            prefix = issue[0] if issue[0] != "M" else "MR"
            issues.append(f'{prefix}{issue.split("-")[1]}')
            issues.append(f'{prefix}-{issue.split("-")[1]}')
    return issues

def find_issues_in(iss: list, file_path: str) -> dict:
    """Finds issues in text"""
    results = {}
    found = 0
    with open(file_path, "r", encoding="utf-8") as data_file:
        current_message = {}
        for index, line in enumerate(data_file):
            the_line = line.strip()
            if "id" in current_message and current_message["id"] == "41659":
                print(current_message)
            # set the meta data
            if the_line.startswith("Message id: "):
                current_message["id"] = the_line[len("Message id: ") :].strip()
            elif the_line.startswith("Subject: "):
                current_message["subject"] = the_line[len("Subject: ") :].strip()
            elif the_line.startswith("Date: "):
                current_message["date"] = the_line[len("Date: ") :].strip()
            elif the_line.startswith("Sent from: "):
                current_message["sent_from"] = the_line[len("Sent from: ") :].strip()
            elif the_line.startswith("Email id: "):
                current_message["email_id"] = the_line[len("Email id: ") :].strip()
            elif the_line.startswith("Tags:"):
                current_message["tags"] = [
                    tag.strip() for tag in the_line[len("Tags:") :].split(",")
                ]
            else:
                # search the line for occurrences.
                for issue in iss:
                    # simple check for find.
                    offset = the_line.find(issue)
                    if offset == -1:
                        continue
                    # double check for spurious finds to be sure.
                    pattern = rf"{issue}[^0-9]"
                    re_finds = re.findall(pattern, the_line)
                    if len(re_finds) == 0:
                        continue
                    # add the find
                    if not issue in results:
                        results[issue] = []
                    new_entry = deepcopy(current_message)
                    new_entry["line_index"] = index
                    new_entry["line"] = the_line
                    new_entry["offset"] = offset
                    new_entry["re_finds"] = re_finds
                    results[issue].append(new_entry)
                    found += 1
    return results, found


def find(issue_file_path: str, input_paths: list, output_path: str):
    """Finds all issue references in the provided text files."""
    print("new start")
    issues = load_issues(issue_file_path)
    all_findings = {}
    for in_path in input_paths:
        print(f'Starting {in_path}')
        findings, count = find_issues_in(issues, in_path)
        print(f"Finished. reference count: {count}")
        if all_findings is None:
            # sets initial value.
            all_findings = findings
        else:
            # appends to all findings
            for key, value in findings.items():
                if key not in all_findings:
                    all_findings[key] = value
                else:
                    all_findings[key].extend(value)
    with open(output_path, "w+", encoding="utf-8") as output_file:
        output_file.write(json.dumps(all_findings, indent=4))


ISSUE_FILE_PATH = "./data/IssuesDatasetArchitectural.xlsx"

# Revised
find(
    ISSUE_FILE_PATH,
    [
        "./data/finder/issues-1.txt",
        "./data/finder/issues-2.txt",
        "./data/finder/issues-3.txt",
        "./data/finder/issues-4.txt",
        "./data/finder/issues-5.txt",
        "./data/finder/issues-6.txt",
        "./data/finder/issues-7.txt",
    ],
    "./data/finder/findings.json",
)


# Original
# find(
#     ISSUE_FILE_PATH,
#     ["./data/find_issues_in_text/the_text.txt"],
#     "./data/find_issues_in_text/the_output.json",
# )
