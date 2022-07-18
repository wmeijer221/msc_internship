# MSc Internship Sourcecode
Repository for sourcecode related to my master's research internship.

## Note:
Any script that interacts with an Atlas.ti project, expects it to be in the web format as reading it relies on the inner content files being html.
This repository does not contain any data itself, so contact the researchers if desired.
All used paths are hard-coded, so refer to the individual scripts for the used file locations.



## Relevant Scripts: 
There are a bunch of scripts in this projects; some work, some don't, some are old, some are actually relevant still. 
Here's a summary of the relevant ones, per study that they're used for. 

### Decision Rationale
- ``the_best_parse_atlas_to_csv.py`` - parses a web atlas project to a CSV file, preserving the email decision types, the thread info, and mail subject, as well as, the quotes and classes attached to that. exports two files, a per email view showing what emails have what kruchten types + rationale types, and an overview of all quotations where they are located and their rationale types. 

### Issue-Email Relationships
- ``better_find_issues_in_text.py`` - takes the txt export of the data browser and a xlsx file of architectural issues, searches for all issue references in the emails and outputs them in a json file. 
- ``restructure_found_issues.py`` - takes the result of ``better_find_issues_in_text.py`` and restructures them. This is useful while classifying using the email browser whilst keeping track of what issues are referenced in what emails (some emails reference multiple issues and not all of them are architectural).
- ``results_figure_prepper.py`` - takes the csv output of the email browser and restructures it to be better usable for the results. Used by the issue-email relationship study.
- ``generate_query.py`` - generates lucene query that can be used to find all issues in the email dataset. 




