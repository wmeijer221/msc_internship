import json
from posixpath import split

from numpy import true_divide


def contains_any(listA: list, listB: list) -> bool:
    for ele in listB:
        if ele in listA:
            return True
    return False


def handle(data: dict, tags: list, t_map: dict):
    unique_emails = set()
    unique_threads = set()
    unique_issues = {}
    for issue_id, issue in data.items():
        for ref in issue:
            if not contains_any(ref["tags"], tags):
                continue

            unique_emails.add(ref["email_id"])
            subject = ref["subject"]
            # it's a reply
            if subject.lower().startswith("re: ") or subject.lower()[2] == ":":
                subject = subject[4:]
            unique_threads.add(subject)
            # Figuring out what issues are referenced
            issue_split = issue_id.split("-")
            if len(issue_split) == 1:
                t = issue_split[0]
                if t.startswith("Y"):
                    r_issue_id = f"YARN-{t[1:]}"
                else:
                    r_issue_id = f"HADOOP-{t[1:]}"
            else:
                proj_key = t_map[issue_split[0]]
                r_issue_id = f"{proj_key}-{issue_split[-1]}"
            if r_issue_id not in unique_issues:
                unique_issues[r_issue_id] = set()
            unique_issues[r_issue_id].add(issue_id)
    for k, v in unique_issues.items():
        unique_issues[k] = list(v)
    return list(unique_emails), list(unique_threads), unique_issues


INPUT_FILE = "./data/the_best_exported_data/findings.json"
INTERESTING_TAGS = [
    "Release Group",
    "Feature Group",
    "Quality Group",
    "Issue Elaboration",
    "Discussion Venue",
    "Issue Impact",
    "Resource",
    "Other Issue Reference",
    "Other",
]

tag_maps = {
    "C": "CASSANDRA",
    "CASSANDRA": "CASSANDRA",
    "H": "HADOOP",
    "HADOOP": "HADOOP",
    "HDFS": "HDFS",
    "T": "TAJO",
    "TAJO": "TAJO",
    "MR": "MAPREDUCE",
    "MAPREDUCE": "MAPREDUCE",
    "Y": "YARN",
    "YARN": "YARN",
}


with open(INPUT_FILE, "r", encoding="utf-8") as input_file:
    data = json.loads(input_file.read())
    ue, ut, ui = handle(data, INTERESTING_TAGS, tag_maps)
    print(json.dumps(ue, indent=4))
    print(json.dumps(ut, indent=4))
    print(json.dumps(ui, indent=4))
    print(
        f"Excluding Irrelevant:\nUnique Emails: {len(ue)}, Unique Threads {len(ut)}, Unique Issues: {len(ui)}"
    )
    print("\n\n\n\n\n\n\n\n\n\n\n\n\n")
    INTERESTING_TAGS.append("Architecturally Irrelevant")
    ue, ut, ui = handle(data, INTERESTING_TAGS, tag_maps)
    print(json.dumps(ue, indent=4))
    print(json.dumps(ut, indent=4))
    print(json.dumps(ui, indent=4))
    print(
        f"Including Irrelevant:\nUnique Emails: {len(ue)}, Unique Threads {len(ut)}, Unique Issues: {len(ui)}"
    )
