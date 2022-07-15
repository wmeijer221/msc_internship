"""
restructures the output of ``better_find_issues_in_text.py`` 
to have emails is primary entities instead of issue keys.
"""

from copy import deepcopy
import json

with open(
    "./data/find_issues_in_text/the_output.json", "r", encoding="utf-8"
) as data_file:
    data = json.loads(data_file.read())

results = {}

for issue, finds in data.items():
    for find in finds:
        if find["id"] not in results:
            new_res = deepcopy(find)
            del new_res["id"]
            del new_res["line_index"]
            del new_res["line"]
            del new_res["offset"]
            del new_res["re_finds"]
            new_res["issues"] = {}
            results[find["id"]] = new_res
        if issue in results[find["id"]]["issues"]:
            continue
        results[find["id"]]["issues"][issue] = {
            "line_index": find["line_index"],
            "line": find["line"],
            "offset": find["offset"],
            "re_finds": find["re_finds"],
        }


print(f"{len(results.keys())=}")

with open(
    "./data/find_issues_in_text/reformatted_output.json", "w", encoding="utf-8"
) as output_file:
    output_file.write(json.dumps(results, indent=4))
