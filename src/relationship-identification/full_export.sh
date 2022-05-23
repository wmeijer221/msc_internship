
ISSUES_PATH="./data/IssuesDatasetArchitectural.xlsx"
ATlAS_PATH="./data/MSc_Internship-2022.atlproj"
MATCHES_PATH="./data/issue-mail-relations/matches.json"
EXTRACT_PATH="./data/atlas_extract/"

DATA_OUTPUT_PATH="./data/issue-mail-relations/data/"
ATLAS_DATA_PATH="./data/atlas_extract/contents"

echo "finding issues"
# Finds issues. 
python3 ./src/relationship-identification/issue_finder.py $ISSUES_PATH $ATlAS_PATH $MATCHES_PATH $EXTRACT_PATH

echo "creating links"
# Outputs mail data.
python3 ./src/relationship-identification/text_composer.py $DATA_OUTPUT_PATH $MATCHES_PATH $ATLAS_DATA_PATH

echo "done"
