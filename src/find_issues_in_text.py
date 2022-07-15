"""finds issues in text file"""

import json
import pandas as pd


def load_issues(issue_file_path: str) -> list:
    """Loads issues from file"""
    dataframe = pd.read_excel(issue_file_path)
    return [row["issues key"] for (_, row) in dataframe.iterrows()]


def find_issues_in(iss: list, file_path: str) -> dict:
    """Finds the issues"""
    results = {}
    found = 0
    with open(file_path, "r", encoding="utf-8") as data_file:
        for index, line in enumerate(data_file):
            print(f'{index=}')
            for issue in iss:
                line_offset = line.find(issue)
                if line_offset != -1:
                    res = (line, index)
                    found += 1
                    if issue in results:
                        results[issue].append(res)
                    else:
                        results[issue] = [res]
    return results, found


ISSUE_FILE_PATH = "./data/IssuesDatasetArchitectural.xlsx"
TEXT_FILE_PATH = "./data/find_issues_in_text/text.txt"
OUTPUT_PATH = "./data/find_issues_in_text/output.json"

issues = load_issues(ISSUE_FILE_PATH)
found_issues, count = find_issues_in(issues, TEXT_FILE_PATH)

print(f'{count=}')

with open(OUTPUT_PATH, "w", encoding="utf-8") as output_file:
    output_file.write(json.dumps(found_issues, indent=4))
