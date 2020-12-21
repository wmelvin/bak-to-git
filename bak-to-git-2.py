#!/usr/bin/env python3

#----------------------------------------------------------------------
# bak-to-git-2.py
#
# 
#
# 2020-09-11
#----------------------------------------------------------------------

# from pathlib import Path
# from collections import namedtuple
import csv
import subprocess


def run_bc(left_file, right_file):
    subprocess.run(['bcompare', left_file, right_file])




#input_csv = '~/Desktop/wemDesk/20200905_BakToGit/out-1-files-changed.csv'
input_csv = 'out-1-files-changed.csv'

with open(input_csv) as csv_file:
    reader = csv.DictReader(csv_file)
    for row in reader:
        print(row['sort_key'])
        if len(row['prev_full_name']) == 0:
            print("New file")
        else:
            run_bc(row['prev_full_name'], row['full_name'])


print('Done.')
