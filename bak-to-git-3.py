#!/usr/bin/env python3

#----------------------------------------------------------------------
# bak-to-git-3.py
#
# Step 3: Read a CSV file edited in step 2 where commit messages are 
# added and files to be skipped are flagged.
#
# Run git to commit each change with the specified date and time.
#
# 
#
# 2020-12-22
#----------------------------------------------------------------------

from pathlib import Path
import csv
import subprocess

#  Specify input file.
#input_csv = Path.cwd() / 'output' / 'out-1-files-changed-EDIT.csv'
input_csv = Path.cwd() / 'test' / 'out-1-files-changed-TEST-1.csv'

datetime_tags = []

with open(input_csv) as csv_file:
    reader = csv.DictReader(csv_file)
    for row in reader:
        if len(row['sort_key']) > 0:
            #print(row['sort_key'])
            do_skip = str(row['SKIP_Y']).upper() == 'Y'
            if not do_skip:
                dt_tag = row['datetime_tag']
                if not dt_tag in datetime_tags:
                    datetime_tags.append(dt_tag)

for t in datetime_tags:
    print(t)

