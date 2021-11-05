# BakToGit


This set of scripts is for doing an **initial setup** of a git repository, including a commit history, based on a set of work-in-progress backup files.  This process is **not** meant to be used as part of an ongoing workflow once the git repository has been populated.


## bak_to_git_1.py

This script uses backup files, created by my `wipbak` script, to build a series of git commits. This is for a project where that script was configured to make work-in-progress backups of the fiew files in the project. Git was not considered at the start, so this is a way to "bak" into a commit history.

**Step 1:** Build a list of backup files and extract the date_time tags from the file names. Sort the list so the files changed in backups with the same date_time tag can be compared and commited as one commit. This step only builds the list and writes it to a CSV file.

When the output from this script is ready to use, the output file should be copied or moved to a new location to use for step 2. That will keep work-in-progress separate from new outputs.

In step 2, the files will be compared so commit messages can be entered in the CSV file. Files can also be skipped so changes can be batched into a single commit.


## bak_to_git_2.py

**Step 2:** Read a CSV file, created in step 1, and launch the 'Beyond Compare' file differencing tool to see changes.

This script does not write any output files.

While using this script to launch the comparisons. Manually add commit messages to the CSV file, and select files to skip to batch changes into a single commit.  I use *LibreOffice Calc* for that, making sure it saves back to CSV format (even if it suggests otherwise).

The manual editing does not have to be done in one session. The bak_to_git_2.py script will skip rows that already have a *commit message*, or are marked to *skip*.


## bak_to_git_3.py

**Step 3:** Read a CSV file edited in step 2 where commit messages are added and files to be skipped are flagged.

This script will run the `git` command to commit each change with the specified date and time.


## bak_to_fossil_3.py

**Step 3 (alternate):** Read a CSV file edited in step 2 where commit messages are added and files to be skipped are flagged.

This script will run the `fossil` command (instead of *git*) to commit each change with the specified date and time.


## Links

### Git
[Git](https://git-scm.com/)
[Git - commit - date formats](https://git-scm.com/docs/git-commit#_date_formats)
[Git - Environment Variables](https://git-scm.com/book/en/v2/Git-Internals-Environment-Variables)

### Fossil
[Fossil: Home](https://fossil-scm.org/home/doc/trunk/www/index.wiki)
[Fossil: Help: commit](https://fossil-scm.org/home/help?cmd=commit)