#!/usr/bin/env python3

# ---------------------------------------------------------------------
#  bak-to-git-1.py
#
#  This script uses backup files, created by my wipbak.sh, script to
#  build a series of git commits. This is for a project where the
#  simple shell script was configured to make work-in-progress backups
#  of the fiew files in the project. Git was not considered at the
#  start, so this is an attempt to back(up) into a commit history.
#
#  Step 1: Build a list of backup files and extract the date_time tags
#  from the file names. Sort the list so the files changed in backups
#  with the same date_time tag can be compared and commited as one
#  commit. This step only builds the list and writes it to a CSV file.
#
#  In step 2, the files will be compared so commit messages can be
#  entered in the CSV file. Files can also be skipped so changes can
#  be batched into a single commit.
#
#  
#
#  2021-05-18
# ---------------------------------------------------------------------

import csv
from collections import namedtuple
from datetime import datetime
from pathlib import Path


def get_output_path(file_name):
    return Path.cwd() / 'output' / file_name


def main():

    # baks_dir =
    # '~/Work/20200817_BackupRotation/_0_bak/_older/20200831'

    baks_dir = '~/Work/20200817_BackupRotation/_0_bak/'

    BakProps = namedtuple(
        'BakProps', 'sort_key, full_name, file_name, base_name, datetime_tag'
    )

    bak_files = Path(baks_dir).rglob('*.bak')

    file_list = []
    datetime_tags = []
    base_names = []

    #  The backup files, created by the wipbak.sh script, are named with
    #  a .date_time tag preceeding the .bak extension (suffix). For example,
    #  're-git-1.py.20200905_105914.bak'.

    for f in bak_files:
        #  Path.stem returns the name without the suffix. Split the stem on '.'
        #  and get the last element to retrieve the date_time tag.
        #
        full_name = str(f)
        file_name = f.name
        datetime_tag = f.stem.split('.')[-1:][0]
        base_name = '.'.join(f.name.split('.')[:-2])
        sort_key = f"{datetime_tag}:{base_name}"

        file_list.append(
            BakProps(sort_key, full_name, file_name, base_name, datetime_tag)
        )

        if base_name not in base_names:
            base_names.append(base_name)

        if datetime_tag not in datetime_tags:
            datetime_tags.append(datetime_tag)

    file_list.sort()
    base_names.sort()
    datetime_tags.sort()

    do_write_debugging_files = False

    #  Write all-files list for debugging.
    if do_write_debugging_files:
        filename_out_all = get_output_path('debug-1-all-files.csv')
        with open(filename_out_all, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow([
                'sort_key',
                'full_name',
                'file_name',
                'base_name',
                'datetime_tag'
            ])
            writer.writerows(file_list)

    #  Write base-names list for debugging.
    if do_write_debugging_files:
        filename_out_base_names = get_output_path('debug-2-base_names.csv')
        with open(filename_out_base_names, 'w', newline='') as out_file:
            out_file.write("base_name\n")
            for a in base_names:
                out_file.write(f"{a}\n")

    #  Write datetime-tags list for debugging.
    if do_write_debugging_files:
        filename_out_dt_tags = get_output_path('debug-3-datetime_tags.csv')
        with open(filename_out_dt_tags, 'w', newline='') as out_file:
            out_file.write("datetime_tag\n")
            for a in datetime_tags:
                out_file.write(f"{a}\n")

    ChangeProps = namedtuple(
        'ChangeProps',
        'sort_key, full_name, prev_full_name, datetime_tag, base_name,' +
        'SKIP_Y, COMMIT_MESSAGE'
    )

    changed_list = []
    prev_files = {}

    for dt in datetime_tags:
        # print (dt)

        dt_files = [p for p in file_list if p.datetime_tag == dt]

        for t in dt_files:
            # print(f"  {t.full_name}")
            if t.base_name in prev_files:
                prev_props = prev_files[t.base_name]
                prev_content = Path(prev_props.full_name).read_text()
                this_content = Path(t.full_name).read_text()
                if prev_content != this_content:
                    #  file changed
                    changed_list.append(
                        ChangeProps(
                            t.sort_key,
                            t.full_name,
                            prev_props.full_name,
                            t.datetime_tag,
                            t.base_name,
                            '',
                            ''
                        )
                    )
                    prev_files[t.base_name] = t
            else:
                #  new file
                changed_list.append(
                    ChangeProps(
                        t.sort_key,
                        t.full_name,
                        '',
                        t.datetime_tag,
                        t.base_name,
                        '',
                        ''
                    )
                )
                prev_files[t.base_name] = t

        #  Insert a blank row between each datetime_tag to make it more
        #  obvious which files will be grouped in a commit.
        changed_list.append(ChangeProps('', '', '', '', '', '', ''))

    #  Write main output from step 1.

    output_base_name = 'out-1-files-changed-{0}.csv'.format(
        datetime.now().strftime('%Y%m%d_%H%M%S')
    )
    filename_out_files_changed = get_output_path(output_base_name)

    with open(filename_out_files_changed, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)

        #  Add columns, 'SKIP_Y' and 'COMMIT_MESSAGE', to populate
        #  manually in next step.
        writer.writerow([
            'sort_key', 'full_name', 'prev_full_name',
            'datetime_tag', 'base_name',
            'SKIP_Y', 'COMMIT_MESSAGE'
        ])

        writer.writerows(changed_list)

    print('Done (bak-to-git-1.py).')


if __name__ == "__main__":
    main()
