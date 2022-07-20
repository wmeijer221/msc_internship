"""
Generates query for the search engine from xlsx issue file.
"""

import pandas as pd

DATA_FILE = "./data/IssuesDatasetArchitectural.xlsx"

xl_file = pd.ExcelFile(DATA_FILE)

df = pd.read_excel(DATA_FILE)

TEST_FOR_REPO_DIFF = False

DEFQ = ""

QUERY = DEFQ

PREV_REPO = ""

for index, row in df.iterrows():
    repo, key = row["issues key"].split("-")

    if TEST_FOR_REPO_DIFF and repo != PREV_REPO:
        print(QUERY[3:])
        PREV_REPO = repo
        QUERY = DEFQ

    # QUERY = f'{QUERY} OR ((+subject:"{repo}\\-{key}") OR (+body:"{repo}\\-{key}") OR (+body:"{key}"))'
    QUERY = f'{QUERY} {key}'

print(QUERY[3:])

xl_file.close()
