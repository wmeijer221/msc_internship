"""
Generates query for the search engine from xlsx issue file.
"""

import pandas as pd

DATA_FILE = "./data/IssuesDatasetArchitectural.xlsx"

xl_file = pd.ExcelFile(DATA_FILE)

df = pd.read_excel(DATA_FILE)

TEST_FOR_REPO_DIFF = True

DEFQ = ''

QUERY = DEFQ

prev_repo = ""

for index, row in df.iterrows():
    repo, key = row["issues key"].split("-")

    if TEST_FOR_REPO_DIFF and repo != prev_repo:
        # print(QUERY[:-3])
        print(f'{QUERY}')
        prev_repo = repo
        QUERY = DEFQ

    QUERY = f'{QUERY} {repo}\-{key}'
    # QUERY = f'{QUERY} ((SUBJECT LIKE \'%{key}%\' OR  BODY LIKE \'%{key}%\') AND (SUBJECT LIKE \'%{repo}%\' OR BODY LIKE \'%{repo}%\')) OR'

# print(QUERY[:-3])
print(f'{QUERY}')

xl_file.close()
