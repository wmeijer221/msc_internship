import csv


AKEMAILS_PATH = "./data/cleaner_data/AKEmails-export2.csv"
RATIONALE_PATH = "./data/atlas_to_csv/export.csv"
OUTPUT_PATH = "./data/rationale_data_prepper/export.csv"


rationale = {}
with open(RATIONALE_PATH, "r", encoding="utf-8") as rationale_data:
    for row in csv.reader(rationale_data, delimiter=",", quotechar='"'):
        email_id = row[2]
        if email_id in rationale:
            rationale[email_id].append(row)
        else:
            rationale[email_id] = [row]

print(rationale)

data_out = []

with open(AKEMAILS_PATH, "r", encoding="utf-8") as ak_data:
    for row in csv.reader(ak_data, delimiter=",", quotechar='"'):
        email_id = row[0]
        new_entry = {
            "email_id": row[0],
            "email_subject": row[1],
            # decision type
            "existence-behavioral": row[2],
            "existence-structural": row[3],
            "process": row[4],
            "property": row[5],
            "technology": row[6],
            # decision rationale
            "assumption": 0,
            "constraints": 0,
            "decision_rule": 0,
            "domain_experience": 0,
            "benefits_and_Drawbacks": 0,
            "solution_evaluation": 0,
            "risks_non_risks": 0,
            "tradeoff": 0,
            "solution_comparison": 0,
            "other": 0,
        }
        keys = list(new_entry.keys())[7:]
        for rat in rationale[email_id] if email_id in rationale else []:
            for i, t in enumerate(rat[2:]):
                if t == 1:
                    new_entry[keys[i]] = 1
        data_out.append(new_entry)

with open(OUTPUT_PATH, "w+", encoding="utf-8") as output_file:
    for key in data_out[0].keys(): 
        output_file.write(f"{str(key)},")
    output_file.write("\n")
    for entry in data_out:
        for value in entry.values():
            output_file.write(f"\"{str(value)}\",")
        output_file.write("\n")
