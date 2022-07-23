import csv
from scipy.stats import chi2_contingency, fisher_exact


def calculate_co_occurrence(data: list, row_index: int, col_index: int) -> float:
    contingency = [[0, 0], [0, 0]]  # [[nn, nt], [tn, tt]]
    for row in data[1:]:
        contingency[int(row[row_index])][int(row[col_index])] += 1

    # The statistics don't work if there's a cell with c < 5
    has_minimum = True
    for row in contingency:
        for cell in row:
            if cell < 5:
                has_minimum = False

    # stats
    chi2, cp, _, _ = chi2_contingency(contingency, correction=True)
    ftp, fp = fisher_exact(contingency)
    return (
        data[0][row_index],
        data[0][col_index],
        contingency,
        has_minimum,
        chi2,
        cp,
        fp,
        ftp,
    )


def calculate(data_path: str, row_indices: list, col_indices: list) -> list:
    results = [None] * len(row_indices)
    with open(data_path, "r", encoding="utf-8") as data_file:
        data: list = list(csv.reader(data_file, delimiter=",", quotechar='"'))
        for i, rix in enumerate(row_indices):
            results[i] = [None] * len(col_indices)
            for j, cix in enumerate(col_indices):
                results[i][j] = calculate_co_occurrence(data, rix, cix)
    return results


def export(results: list, output_path: str):
    with open(output_path, "w+", encoding="utf-8") as output_file:
        output_file.write(
            "class_a,class_b,cont_nn,cont_nt,cont_tn,cont_tt,min_sup,chi2,chi2-p,fish-p,fish-two-p,\n"
        )
        for row in results:
            for col in row:
                output_file.write(f'"{col[0]}","{col[1]}",')
                for r2 in col[2]:
                    for c2 in r2:
                        output_file.write(f'"{c2}",')
                for ele in col[3:]:
                    output_file.write(f'"{ele}",')
                output_file.write("\n")


if __name__ == "__main__":
    
    DATA_PATH = "./data/the_best_exported_data/export_emails.csv"
    DATA_PATH2 = "./data/the_best_exported_data/export_quotes.csv"

    OUTPUT_PATH = "./data/the_best_exported_data/rat_vs_dec_emails.csv"
    OUTPUT_PATH2 = "./data/the_best_exported_data/rat_vs_dec_quotes.csv"
    OUTPUT_PATH3 = "./data/the_best_exported_data/rat_vs_rat_emails.csv"
    OUTPUT_PATH4 = "./data/the_best_exported_data/rat_vs_rat_quotes.csv"

    # Rationale vs Decision per Email
    export(calculate(DATA_PATH, range(3, 8), range(8, 17)), OUTPUT_PATH)

    # Rationale vs Decision per Quote
    export(calculate(DATA_PATH2, range(6, 11), range(11, 20)), OUTPUT_PATH2)

    # Rationale vs Rationale per email
    export(calculate(DATA_PATH, range(8, 17), range(8, 17)), OUTPUT_PATH3)

    # Rationale vs Rationale per quote
    export(calculate(DATA_PATH2, range(11, 20), range(11, 20)), OUTPUT_PATH4)

    # REL_DATA_PATH = "./data/the_best_exported_data/the_data.csv"
    # REL_DATA_OUT = "./data/the_best_exported_data/rel_vs_rel.csv"
    # REL_DATA_OUT2 = "./data/the_best_exported_data/dec_vs_rel_email.csv"
    # REL_DATA_OUT3 = "./data/the_best_exported_data/dec_vs_rel_issue.csv"

    # export(calculate(REL_DATA_PATH, range(2, 12), range(2, 12)), REL_DATA_OUT)
