#!/usr/bin/env python3

#----------------------------------------------------------------------
# bak-to-git-2.py
#
# Step 2: Read a CSV file, created in step 1, and launch the 'Beyond 
# Compare' file differencing tool to see changes.
#
# Manually add commit messages to the CSV file, and select files to
# skip to batch changes into a single commit.
#
# 
#
# 2020-12-21
#----------------------------------------------------------------------

from pathlib import Path
import csv
import subprocess

#  Specify input file.
input_csv = Path.cwd() / 'output' / 'out-1-files-changed.csv'
#input_csv = Path.cwd() / 'test' / 'out-1-files-changed-TEST-1.csv'


def run_bc(left_file, right_file):
    print("Compare\n  L: {0}\n  R: {1}".format(left_file, right_file))
    #subprocess.run(['bcompare', left_file, right_file])


with open(input_csv) as csv_file:
    reader = csv.DictReader(csv_file)
    for row in reader:
        if len(row['sort_key']) > 0:
            print(row['sort_key'])
            if len(row['prev_full_name']) == 0:
                print("New file")
            else:
                no_msg = len(row['COMMIT_MESSAGE']) == 0

                #  If the 'SKIP_Y' field is blank, then rows with an existing 
                #  commit message are skipped.

                #  Setting 'SKIP_Y' to 'Y' will skip the comparison regardless
                #  of the commit message.
                force_skip = row['SKIP_Y'].upper() == 'Y'

                #  Setting 'SKIP_Y' to 'N' will run the comparison regardless
                #  of the commit message.
                force_no_skip = row['SKIP_Y'].upper() == 'N'

                if (not force_skip) and (no_msg or force_no_skip): 
                    run_bc(row['prev_full_name'], row['full_name'])


print('Done.')
