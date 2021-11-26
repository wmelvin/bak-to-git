#!/usr/bin/env python3

# ---------------------------------------------------------------------
#  bak_to_git_1.py
# ---------------------------------------------------------------------

import argparse
import csv
import sys

from collections import namedtuple
from datetime import datetime
from pathlib import Path
from typing import List


AppOptions = namedtuple(
    "AppOptions", "source_dir, output_dir, include_dt, write_debug, skip_list"
)


BakProps = namedtuple(
    "BakProps", "sort_key, full_name, file_name, base_name, datetime_tag"
)


ChangeProps = namedtuple(
    "ChangeProps",
    "row_num, sort_key, full_name, prev_full_name, datetime_tag, base_name,"
    + "SKIP_Y, COMMIT_MESSAGE, ADD_COMMAND, NOTES",
)


def get_opts(argv) -> AppOptions:

    ap = argparse.ArgumentParser(
        description="BakToGit Step 1: Read backup (.bak) files, created by "
        + "the 'wipbak' script, and write a CSV file with the data need to "
        + "build a git commit history."
    )
    # TODO: Expand description.

    ap.add_argument(
        "source_dir",
        action="store",
        help="Source directory containing the *.bak files created by "
        + "'wipbak'.",
    )

    ap.add_argument(
        "--output-dir",
        dest="output_dir",
        action="store",
        help="Name of output directory, which must already exist.",
    )

    ap.add_argument(
        "--timestamp",
        dest="include_dt",
        action="store_true",
        help="Include a date_time stamp in the output file names.",
    )

    ap.add_argument(
        "--write-debug",
        dest="write_debug",
        action="store_true",
        help="Write files containing additional details useful for debugging.",
    )

    ap.add_argument(
        "--skip-names",
        dest="skip_names",
        action="store",
        help="File names to mark SKIP_Y in output. Separate multiple names "
        + "with commas (no spaces).",
    )

    args = ap.parse_args(argv[1:])

    if args.skip_names is None:
        skip_list = []
    else:
        skip_list = [a for a in args.skip_names.split(",") if 0 < len(a)]

    opts = AppOptions(
        args.source_dir,
        args.output_dir,
        args.include_dt,
        args.write_debug,
        skip_list,
    )

    assert Path(opts.source_dir).exists()
    assert Path(opts.source_dir).is_dir()

    return opts


def main(argv):
    now_tag = datetime.now().strftime("%y%m%d_%H%M%S")

    opts = get_opts(argv)

    if opts.output_dir is None or len(opts.output_dir) == 0:
        output_path = Path.cwd() / "output"
    else:
        output_path = Path(opts.output_dir).expanduser().resolve()

    #  The top-level output directory should exist.
    if not output_path.exists():
        sys.stderr.write(
            "ERROR: Output directory does not exist: {0}\n".format(output_path)
        )
        sys.exit(1)

    output_path = output_path.joinpath(now_tag)

    #  The run-specific output sub-directory should not exist at this point.
    if output_path.exists():
        sys.stderr.write(
            "ERROR: Run-specific output directory exists: {0}\n".format(
                output_path
            )
        )
        sys.exit(1)

    output_path.mkdir()

    assert output_path.exists()

    print(f"Scanning '{opts.source_dir}'")

    bak_files = Path(opts.source_dir).rglob("*.bak")

    file_list: List[BakProps] = []
    datetime_tags = []
    base_names = []

    #  The backup files, created by the 'wipbak' script, are named with
    #  a .date_time tag preceeding the .bak extension (suffix). For example,
    #  'bak_to_git_1.py.20200905_105914.bak'.

    for f in bak_files:
        #  Path.stem returns the name without the suffix. Split the stem on '.'
        #  and get the last element to retrieve the date_time tag.
        #
        full_name = str(f)
        file_name = f.name
        datetime_tag = f.stem.split(".")[-1:][0]
        base_name = ".".join(f.name.split(".")[:-2])
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

    #  Write all-files list for debugging.
    if opts.write_debug:
        filename_out_all = str(output_path.joinpath("z-debug-1-all-files.csv"))
        with open(filename_out_all, "w", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(
                [
                    "sort_key",
                    "full_name",
                    "file_name",
                    "base_name",
                    "datetime_tag",
                ]
            )
            writer.writerows(file_list)

    #  Write base-names list for debugging.
    if opts.write_debug:
        filename_out_base_names = str(
            output_path.joinpath("z-debug-2-base_names.csv")
        )
        with open(filename_out_base_names, "w", newline="") as out_file:
            out_file.write("base_name\n")
            for a in base_names:
                out_file.write(f"{a}\n")

    #  Write datetime-tags list for debugging.
    if opts.write_debug:
        filename_out_dt_tags = str(
            output_path.joinpath("z-debug-3-datetime_tags.csv")
        )
        with open(filename_out_dt_tags, "w", newline="") as out_file:
            out_file.write("datetime_tag\n")
            for a in datetime_tags:
                out_file.write(f"{a}\n")

    changed_list: List[ChangeProps] = []
    row_num = 0
    prev_files = {}

    for dt in datetime_tags:
        # print (dt)

        dt_files: List[BakProps] = [
            p for p in file_list if p.datetime_tag == dt
        ]

        for t in dt_files:
            # print(f"  {t.full_name}")
            if t.base_name in opts.skip_list:
                skipy = "Y"
                note = "SKIP_Y set per --skip-names option."
            else:
                skipy = ""
                note = ""
            if t.base_name in prev_files:
                prev_props = prev_files[t.base_name]
                prev_content = Path(prev_props.full_name).read_text()
                this_content = Path(t.full_name).read_text()
                if prev_content != this_content:
                    #  file changed
                    row_num += 1
                    props = ChangeProps(
                        row_num,
                        t.sort_key,
                        t.full_name,
                        prev_props.full_name,
                        t.datetime_tag,
                        t.base_name,
                        skipy,
                        "",
                        "",
                        note,
                    )
                    changed_list.append(props)
                    prev_files[t.base_name] = t
            else:
                #  new file
                row_num += 1
                props = ChangeProps(
                    row_num,
                    t.sort_key,
                    t.full_name,
                    "",
                    t.datetime_tag,
                    t.base_name,
                    skipy,
                    "",
                    "",
                    note,
                )
                changed_list.append(props)
                prev_files[t.base_name] = t

        #  Insert a blank row between each datetime_tag to make it more
        #  obvious which files will be grouped in a commit.
        row_num += 1
        changed_list.append(
            ChangeProps(row_num, "", "", "", "", "", "", "", "", "")
        )

    #  Write main output from step 1.

    if opts.include_dt:
        output_base_name = "step-1-files-changed-{0}.csv".format(now_tag)
        filename_out_files_changed = str(
            output_path.joinpath(output_base_name)
        )
    else:
        filename_out_files_changed = str(
            output_path.joinpath("step-1-files-changed.csv")
        )

    print(f"Writing '{filename_out_files_changed}'")

    with open(filename_out_files_changed, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)

        #  Add 'SKIP_Y', 'COMMIT_MESSAGE', 'ADD_COMMAND', and 'NOTES'
        #  columns to populate manually in Step 2.
        writer.writerow(
            [
                "row",
                "sort_key",
                "full_name",
                "prev_full_name",
                "datetime_tag",
                "base_name",
                "SKIP_Y",
                "COMMIT_MESSAGE",
                "ADD_COMMAND",
                "NOTES",
            ]
        )

        writer.writerows(changed_list)

    print("Done (bak_to_git_1.py).")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
