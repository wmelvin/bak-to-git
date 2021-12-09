# bak-to-git


This set of scripts is for doing an **initial setup** of a git repository, including a commit history, based on a set of work-in-progress backup files.  This process is **not** meant to be used as part of an ongoing workflow once the git repository has been populated.


## bak_to_git_1.py

This script uses backup files, created by my [wipbak](https://github.com/wmelvin/wipbak) script, to build a series of git commits. This is for a project where that script was configured to make work-in-progress backups of the few files in the project. Git was not considered at the start, so this is a way to "bak" into a commit history.

**Step 1:** Build a list of backup files and extract the date_time tags from the file names. Sort the list so the files changed in backups with the same date_time tag can be compared and committed as one commit. This step only builds the list and writes it to a CSV file.

When the output from this script is ready to use, the output file should be copied or moved to a new location to use for step 2. That will keep work-in-progress separate from new outputs.

In step 2, the files will be compared so commit messages can be entered in the CSV file. Files can also be skipped so changes can be batched into a single commit.

### usage ###

```
usage: bak_to_git_1.py [-h] [--output-dir OUTPUT_DIR] [--timestamp]
                       [--write-debug] [--skip-names SKIP_NAMES]
                       source_dir

BakToGit Step 1: Read backup (.bak) files, created by the 'wipbak' script, and
write a CSV file with the data need to build a git commit history.

positional arguments:
  source_dir            Source directory containing the *.bak files created by
                        'wipbak'.

optional arguments:
  -h, --help            show this help message and exit
  --output-dir OUTPUT_DIR
                        Name of output directory, which must already exist.
  --timestamp           Include a date_time stamp in the output file names.
  --write-debug         Write files containing additional details useful for
                        debugging.
  --skip-names SKIP_NAMES
                        File names to mark SKIP_Y in output. Separate multiple
                        names with commas (no spaces).
```

## bak_to_git_2.py

**Step 2:** Read a CSV file, created in step 1, and launch the file comparison (diff) tool to see changes. The default tool is [Beyond Compare](https://www.scootersoftware.com/), a commercial product. The `--compare-cmd` option can be used to run a different executable, for example `--compare-cmd=meld` to use [Meld](https://meldmerge.org/).

While using this script to launch the comparisons, manually add commit messages to the CSV file, and select files to skip (to batch changes into a single commit).  I use *LibreOffice Calc* for that, making sure it saves back to CSV format (even if it suggests otherwise).

The comparison tool must be closed before the script will continue. At that point it prompts for input. Press 'y' or 'Enter' to continue to the next comparison, 'n' to stop, or 'k' to continue and *keep* the same left-side file for the next comparison.

The manual editing does not have to be done in one session. The *bak_to_git_2.py* script will skip rows in the CSV file that already have text in the COMMIT_MESSAGE column, or have a 'Y' in the SKIP_Y column.

The only output file this script writes is a log file.

### usage ###

```
usage: bak_to_git_2.py [-h] [--skip-backup] [--log-dir LOG_DIR]
                       [--compare-cmd RUN_CMD]
                       input_csv

BakToGit Step 2: Run Beyond Compare (bcompare) to review source file changes
between 'wipbak' backups. This is to be used along with manually editing the
CSV file to set the 'SKIP_Y' and 'COMMIT_MESSAGE' columns.

positional arguments:
  input_csv             Path to CSV file created by bak_to_git_1.py.

optional arguments:
  -h, --help            show this help message and exit
  --skip-backup         Do not create a backup of the input CSV file. By
                        default, a backup copy is created at the start of a
                        session.
  --log-dir LOG_DIR     Output directory for log files.
  --compare-cmd RUN_CMD
                        Alternate executable command to launch a file
                        comparison tool. The tool must take the names of two
                        files to compare as the first two command-line
                        arguments. The default is 'bcompare' (Beyond Compare
                        by Scooter Software).
```

## bak_to_git_3.py

**Step 3:** Read a CSV file edited in step 2 where commit messages are added and files to be skipped are flagged.

This script will run the `git` command to commit each change with the specified date and time.

### usage ###

```
usage: bak_to_git_3.py [-h] [--log-dir LOG_DIR] [--filter-file FILTER_FILE]
                       [--what-if]
                       input_csv repo_dir

BakToGit Step 3: ...

positional arguments:
  input_csv             Path to CSV file, manually edited in step 2 to add
                        commit messages.
  repo_dir              Path to repository directory. This should be a new
                        (empty) repository, or one where the first commit from
                        the wipbak files is an appropriate next commit.

optional arguments:
  -h, --help            show this help message and exit
  --log-dir LOG_DIR     Output directory for log files.
  --filter-file FILTER_FILE
                        Path to text file with list of string replacements in
                        comma-separated format ("old string", "new string").
  --what-if             Run in 'what-if' mode, and do not ask to commit
                        changes.
```

## bak_to_fossil_3.py

**Step 3 (alternate):** Read a CSV file edited in step 2 where commit messages are added and files to be skipped are flagged.

This script will run the `fossil` command (instead of *git*) to commit each change with the specified date and time.

### usage ###

```
usage: bak_to_fossil_3.py [-h] [--repo-name REPO_NAME] [--init-date INIT_DATE]
                          [--log-dir LOG_DIR] [--fossil-exe FOSSIL_EXE]
                          [--filter-file FILTER_FILE]
                          input_csv repo_dir

BakToGit Step 3 (alternate): Use fossil instead of git...

positional arguments:
  input_csv             Path to CSV file, manually edited in step 2 to add
                        commit messages.
  repo_dir              Path to repository directory. This should be a new
                        (empty) repository, or one where the first commit from
                        the wipbak files is an appropriate next commit.

optional arguments:
  -h, --help            show this help message and exit
  --repo-name REPO_NAME
                        Name of the fossil repository (usually has a .fossil
                        extension).
  --init-date INIT_DATE
                        Date and time to use for fossil repository
                        initialization. This should be at, or before, the time
                        of the first source (.bak) file to commit. Use the ISO
                        8601 format for date and time (yyyy-mm-ddThh:mm:ss).
                        Example: 2021-07-14T16:20:01
  --log-dir LOG_DIR     Output directory for log files.
  --fossil-exe FOSSIL_EXE
                        Path to the Fossil executable file.
  --filter-file FILTER_FILE
                        Path to text file with list of string replacements in
                        comma-separated format ("old string", "new string").
```

## Reference

### Git

[Main Page](https://git-scm.com/)

Book:
- [Recording Changes to the Repository](https://git-scm.com/book/en/v2/Git-Basics-Recording-Changes-to-the-Repository)
- [Environment Variables](https://git-scm.com/book/en/v2/Git-Internals-Environment-Variables)
- [Tagging](https://git-scm.com/book/en/v2/Git-Basics-Tagging)

Docs:
- [commit - date formats](https://git-scm.com/docs/git-commit#_date_formats)
- [git-tag](https://git-scm.com/docs/git-tag)
- [git-mv](https://git-scm.com/docs/git-mv)

### Fossil

[Fossil: Home](https://fossil-scm.org/home/doc/trunk/www/index.wiki)
[Fossil Help: commit](https://fossil-scm.org/home/help?cmd=commit)
