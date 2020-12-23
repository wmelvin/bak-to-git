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

import csv
import shutil
import subprocess
from collections import namedtuple
from datetime import datetime
from pathlib import Path


#  Specify input file.
#input_csv = Path.cwd() / 'output' / 'out-1-files-changed-EDIT.csv'
input_csv = Path.cwd() / 'test' / 'out-1-files-changed-TEST-1.csv'

repo_dir = '~/Desktop/test/bakrot_repo'

log_name = Path.cwd() / 'bak-to-git-3.log'


CommitProps = namedtuple(
    'FileProps', 
    'sort_key, full_name, datetime_tag, base_name, commit_message'
)


def write_log(msg):
    with open(log_name,  'a') as log_file:
        log_file.write(f"[{datetime.now():%Y%m%d_%H%M%S}] {msg}\n")


def datetime_tag_to_str(dt_tag):
    # yyyymmdd_hhmmss
    # 012345678901234
    return '{0}-{1}-{2} {3}:{4}:{5}'.format(
        dt_tag[:4],
        dt_tag[4:6],
        dt_tag[6:8],
        dt_tag[9:11],
        dt_tag[11:13],
        dt_tag[13:]
    )

write_log('BEGIN')

commit_list = []

write_log(f"Read {input_csv}")

with open(input_csv) as csv_file:
    reader = csv.DictReader(csv_file)
    for row in reader:
        if len(row['full_name']) > 0:
            do_skip = str(row['SKIP_Y']).upper() == 'Y'
            if not do_skip:
                commit_list.append(
                    CommitProps(
                        row['sort_key'],
                        row['full_name'],
                        row['datetime_tag'],
                        row['base_name'],
                        row['COMMIT_MESSAGE']
                    )
                )

commit_list.sort()

datetime_tags = []
for item in commit_list:
    if not item.datetime_tag in datetime_tags:
        datetime_tags.append(item.datetime_tag)

datetime_tags.sort()

target_path = Path(repo_dir).resolve()

for dt_tag in datetime_tags:
    print(dt_tag)

    datetime_str = datetime_tag_to_str(dt_tag)

    git_env = {"GIT_COMMITTER_DATE": datetime_str, "GIT_AUTHOR_DATE": datetime_str}

    commit_msg = ''

    for item in commit_list:
        if item.datetime_tag == dt_tag:
            s = item.commit_message.strip()
            if 0 < len(s) and not s.endswith('.'):
                s += ". "
            commit_msg += s
            target_name =  target_path / Path(item.base_name).name
            existing_file = Path(target_name).exists()
            print(f"COPY {item.full_name}")
            print(f"  TO {target_name}")
            # Copy file to target repo location.
            shutil.copy2(item.full_name, target_name)
            if not existing_file:
                write_log(f"({item.datetime_tag}) RUN git add {item.base_name}")
                result = subprocess.run(["git", "add", item.base_name], cwd=target_path, env=git_env)                
                assert result.returncode == 0

    if len(commit_msg) == 0:
        commit_msg = f"({dt_tag})"
    else:
        commit_msg = commit_msg.strip()

    print(f"Commit message: '{commit_msg}'\n")

    write_log(f"({dt_tag}) RUN git commit '{commit_msg}'")
    result = subprocess.run(["git", "commit", "-a", "-m", commit_msg], cwd=target_path, env=git_env)
    assert result.returncode == 0

write_log('END')

print('Done (bak-to-git-3.py).')
