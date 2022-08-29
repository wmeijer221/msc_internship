import csv
from scipy.stats import fisher_exact


def calculate_co_occurrence(data: list, subject: int, outcome: int) -> float:
    # Contingency Format:
    #     YS, NS
    # NO [[a, b],
    # YO  [c, d]]
    contingency = [[0, 0], [0, 0]]
    for entry in data[1:]:
        col = 0 if int(entry[subject]) == 1 else 1
        row = int(entry[outcome])
        contingency[row][col] += 1

    # Stats: whether its: 1) sig. lower, 2) sig. greater, 3) sig. different.
    _, lower_p = fisher_exact(contingency, alternative="less")
    _, greater_p = fisher_exact(contingency, alternative="greater")
    _, two_tailed_p = fisher_exact(contingency, alternative="two-sided")
    return (
        data[0][subject],
        data[0][outcome],
        contingency,
        lower_p,
        greater_p,
        two_tailed_p,
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
            '"Subject","Outcome","Only Sub","Neither","Both","Only Out","Fisher Lower p","Fisher Greater p","Fisher Two-tailed p",\n'
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
    OUTPUT_PATH = "./data/the_best_exported_data/dec_vs_rat_emails.csv"
    OUTPUT_PATH3 = "./data/the_best_exported_data/rat_vs_rat_emails.csv"

    # Rationale vs Decision per Email
    export(calculate(DATA_PATH, range(3, 8), range(8, 17)), OUTPUT_PATH)

    # Rationale vs Rationale per email
    export(calculate(DATA_PATH, range(8, 17), range(8, 17)), OUTPUT_PATH3)

    REL_DATA_PATH = "./data/the_best_exported_data/the_data.csv"
    REL_DATA_OUT = "./data/the_best_exported_data/rel_vs_rel.csv"
    export(calculate(REL_DATA_PATH, range(2, 14), range(2, 14)), REL_DATA_OUT)
