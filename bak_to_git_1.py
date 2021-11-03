#!/usr/bin/env python3

# ---------------------------------------------------------------------
#  bak_to_git_1.py
#
# ---------------------------------------------------------------------

import argparse
import csv
import sys

from collections import namedtuple
from datetime import datetime
from pathlib import Path


AppOptions = namedtuple(
    "AppOptions", "source_dir, output_dir, include_dt, write_debug"
)


BakProps = namedtuple(
    "BakProps", "sort_key, full_name, file_name, base_name, datetime_tag"
)


ChangeProps = namedtuple(
    "ChangeProps",
    "sort_key, full_name, prev_full_name, datetime_tag, base_name,"
    + "SKIP_Y, COMMIT_MESSAGE",
)


def get_opts(argv) -> AppOptions:

    ap = argparse.ArgumentParser(
        description="Read 'wipbak' files and write a 'csv' file."
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
        help="Include a date_time stamp in the output file names."
    )

    ap.add_argument(
        "--write-debug",
        dest="write_debug",
        action="store_true",
        help="Write files containing additional details useful for debugging."
    )

    args = ap.parse_args(argv[1:])

    opts = AppOptions(
        args.source_dir,
        args.output_dir,
        args.include_dt,
        args.write_debug,
    )

    assert Path(opts.source_dir).exists()
    assert Path(opts.source_dir).is_dir()

    return opts


def main(argv):
    now_tag = datetime.now().strftime("%Y%m%d_%H%M%S")

    opts = get_opts(argv)

    if opts.output_dir is None or len(opts.output_dir) == 0:
        output_path = Path.cwd() / "output"
    else:
        output_path = Path(opts.output_dir)

    #  The top-level output directory should exist.
    if not output_path.exists():
        sys.stderr.write(
            "ERROR: Output directory does not exist: {0}\n".format(output_path)
        )
        sys.exit(1)

    output_path = output_path.joinpath(now_tag)
    #  The run-specific output sub-directory should not exist.
    if output_path.exists():
        sys.stderr.write(
            "ERROR: Run-specific output directory exists: {0}\n".format(
                output_path
            )
        )
        sys.exit(1)

    output_path.mkdir()

    bak_files = Path(opts.source_dir).rglob("*.bak")

    file_list = []
    datetime_tags = []
    base_names = []

    #  The backup files, created by the wipbak.sh script, are named with
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
        filename_out_all = str(output_path.joinpath("debug-1-all-files.csv"))
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
            output_path.joinpath("debug-2-base_names.csv")
        )
        with open(filename_out_base_names, "w", newline="") as out_file:
            out_file.write("base_name\n")
            for a in base_names:
                out_file.write(f"{a}\n")

    #  Write datetime-tags list for debugging.
    if opts.write_debug:
        filename_out_dt_tags = str(
            output_path.joinpath("debug-3-datetime_tags.csv")
        )
        with open(filename_out_dt_tags, "w", newline="") as out_file:
            out_file.write("datetime_tag\n")
            for a in datetime_tags:
                out_file.write(f"{a}\n")

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
                            "",
                            "",
                        )
                    )
                    prev_files[t.base_name] = t
            else:
                #  new file
                changed_list.append(
                    ChangeProps(
                        t.sort_key,
                        t.full_name,
                        "",
                        t.datetime_tag,
                        t.base_name,
                        "",
                        "",
                    )
                )
                prev_files[t.base_name] = t

        #  Insert a blank row between each datetime_tag to make it more
        #  obvious which files will be grouped in a commit.
        changed_list.append(ChangeProps("", "", "", "", "", "", ""))

    #  Write main output from step 1.

    if opts.include_dt:
        output_base_name = "out-1-files-changed-{0}.csv".format(now_tag)
        filename_out_files_changed = str(
            output_path.joinpath(output_base_name)
        )
    else:
        filename_out_files_changed = str(
            output_path.joinpath("out-1-files-changed.csv")
        )

    with open(filename_out_files_changed, "w", newline="") as csv_file:
        writer = csv.writer(csv_file)

        #  Add columns, 'SKIP_Y' and 'COMMIT_MESSAGE', to populate
        #  manually in next step.
        writer.writerow(
            [
                "sort_key",
                "full_name",
                "prev_full_name",
                "datetime_tag",
                "base_name",
                "SKIP_Y",
                "COMMIT_MESSAGE",
            ]
        )

        writer.writerows(changed_list)

    print("Done (bak_to_git_1.py).")


if __name__ == '__main__':
    sys.exit(main(sys.argv))
