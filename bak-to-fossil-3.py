#!/usr/bin/env python3

# ---------------------------------------------------------------------
#  bak-to-fossil-3.py
#
#  Step 3: Read a CSV file edited in step 2 where commit messages are
#  added and files to be skipped are flagged.
#
#  Run fossil (instead of git) to commit each change with the
#  specified date and time.
#
#  
#
#  2021-08-23
# ---------------------------------------------------------------------

import csv
import subprocess
from collections import namedtuple
from datetime import datetime
from datetime import timedelta
from pathlib import Path


#  Specify input file.
input_csv = Path.cwd() / 'prepare' / 'out-1-files-changed-UPLOAD-1-newpath.csv'
#  "-newpath" = Changed '/Work/' to '/Projects/' in file paths.


repo_dir = '~/Desktop/test/bakrot_fossil'

log_name = Path.cwd() / 'log-bak-to-fossil-3.txt'

#  Set to False for debugging without actually running the SCM commands.
#  This will still copy files to the repo directory.
do_run_scm = False

fossil_exe = "~/bin/fossil"


CommitProps = namedtuple(
    'FileProps',
    'sort_key, full_name, datetime_tag, base_name, commit_message'
)


def write_log(msg):
    with open(log_name,  'a') as log_file:
        log_file.write(f"[{datetime.now():%Y%m%d_%H%M%S}] {msg}\n")


def get_date_strings(dt_tag):

    #  Tag format: yyyymmdd_hhmmss
    #       index: 012345678901234
    #
    iso_fmt = '{0}-{1}-{2}T{3}:{4}:{5}'.format(
        dt_tag[:4],
        dt_tag[4:6],
        dt_tag[6:8],
        dt_tag[9:11],
        dt_tag[11:13],
        dt_tag[13:]
    )

    commit_dt = datetime.fromisoformat(iso_fmt)

    #  I feel like the author date should be a little before
    #  the committer date, rather than exactly the same,
    #  but that might be silly.
    #
    author_dt = commit_dt - timedelta(seconds=5)

    return (
        author_dt.strftime('%Y-%m-%dT%H:%M:%S'),
        commit_dt.strftime('%Y-%m-%dT%H:%M:%S')
    )


def copy_filtered_content(src_name, dst_name):
    with open(src_name, 'r') as src_file:
        with open(dst_name, 'w') as dst_file:
            for line in src_file.readlines():
                #  Filter out the email address I was using at the time.
                s = line.replace('(**REDACTED**)', '')
                s = s.replace('**REDACTED**', '')
                dst_file.write(s)


def main():
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
        if item.datetime_tag not in datetime_tags:
            datetime_tags.append(item.datetime_tag)

    datetime_tags.sort()

    target_path = Path(repo_dir).resolve()

    for dt_tag in datetime_tags:
        print(dt_tag)

        author_dt, commit_dt = get_date_strings(dt_tag)

        commit_msg = ''

        for item in commit_list:
            if item.datetime_tag == dt_tag:
                s = item.commit_message.strip()
                if 0 < len(s) and not s.endswith('.'):
                    s += ". "
                commit_msg += s
                target_name = target_path / Path(item.base_name).name
                existing_file = Path(target_name).exists()

                print(f"COPY {item.full_name}")
                print(f"  TO {target_name}")

                #  Copy file to target repo location.
                copy_filtered_content(item.full_name, target_name)

                if not existing_file:
                    cmds = [fossil_exe, "add", item.base_name]
                    write_log(
                        "({0}) RUN '{1}'".format(item.datetime_tag, cmds)
                    )
                    if do_run_scm:
                        result = subprocess.run(cmds, cwd=target_path)
                        assert result.returncode == 0

        if len(commit_msg) == 0:
            commit_msg = f"({dt_tag})"
        else:
            commit_msg = commit_msg.strip()

        print(f"Commit message: '{commit_msg}'\n")

        cmds = [fossil_exe, "commit", "-m", commit_msg]

        write_log("({0}) RUN '{1}'".format(dt_tag, ' '.join(cmds)))

        if do_run_scm:
            result = subprocess.run(cmds, cwd=target_path)
            assert result.returncode == 0

    write_log('END')

    print('Done (bak-to-fossil-3.py).')


if __name__ == "__main__":
    main()
