import pandas as pd


DEC_TYPE_DATA_PATH = "./data/IssuesDatasetArchitectural.xlsx"
REL_DATA_PATH = "./data/the_best_exported_data/the_data.csv"
DATA_OUT = "./data/the_best_exported_data/the_data_with_issues.csv"

xl_file = pd.ExcelFile(DEC_TYPE_DATA_PATH)
