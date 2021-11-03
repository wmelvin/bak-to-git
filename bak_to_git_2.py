#!/usr/bin/env python3

# ---------------------------------------------------------------------
#  bak_to_git_2.py
#
# ---------------------------------------------------------------------

import argparse
import csv
import shutil
import subprocess
import sys

from collections import namedtuple
from datetime import datetime
from pathlib import Path


AppOptions = namedtuple("AppOptions", "input_csv, skip_backup")


#  Specify input file.
# input_csv = Path.cwd() / 'output' / 'out-1-files-changed.csv'
# input_csv = Path.cwd() / 'test' / 'out-1-files-changed-TEST-1.csv'
# input_csv = Path.cwd() / "prepare" / "out-1-files-changed-EDIT.csv"


def run_bc(left_file, right_file):
    print(f"\nCompare\n  L: {left_file}\n  R: {right_file}\n")

    result = subprocess.run(["bcompare", left_file, right_file])

    assert result.returncode in [0, 1, 2, 11, 12, 13]
    #  bcompare return codes:
    #    Code  Meaning
    #       0  Success
    #       1  Binary same
    #       2  Rules-based same
    #      11  Binary differences
    #      12  Similar
    #      13  Rules-based differences


def get_opts(argv) -> AppOptions:

    ap = argparse.ArgumentParser(
        description="BakToGit - step 2: Run Beyond Compare (bcompare) to "
        + "review source file changes between 'wipbak' backups. This is"
        + "to be used along with manually editing the CSV file to set "
        + "the 'SKIP_Y' and 'COMMIT_MESSAGE' columns."
    )

    ap.add_argument(
        "input_csv",
        action="store",
        help="Path to CSV file created by bak_to_git_1.py.",
    )

    ap.add_argument(
        "--skip-backup",
        dest="skip_backup",
        action="store_true",
        help="Do not create a backup of the input CSV file. By default a "
        + "backup copy is created at the start of a session."
    )

    args = ap.parse_args(argv[1:])

    opts = AppOptions(args.input_csv, args.skip_backup)

    assert Path(opts.input_csv).exists()
    assert Path(opts.input_csv).is_file()

    return opts


def main(argv):
    now_tag = datetime.now().strftime("%y%m%d_%H%M%S")

    opts = get_opts(argv)

    if not opts.skip_backup:
        #  Make a backup of the input_csv in case there are problems while
        #  manually editing the file.
        bak_suffix = f".{now_tag}.bak"
        p = Path(opts.input_csv)
        bak_path = p.with_name(f"z-{p.name}").with_suffix(bak_suffix)
        assert not bak_path.exists()
        print(f"\nSaving backup as '{bak_path.name}'\n")
        shutil.copyfile(opts.input_csv, bak_path)

    prevs = {}
    with open(opts.input_csv) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if len(row["sort_key"]) > 0:
                print(row["sort_key"])
                base_name = row["base_name"]

                # if len(row['prev_full_name']) == 0:
                if False:

                    print("New file")
                else:
                    no_msg = len(row["COMMIT_MESSAGE"]) == 0

                    #  If the 'SKIP_Y' field is blank, then rows with an
                    #  existing commit message are skipped.

                    #  Setting 'SKIP_Y' to 'Y' will skip the comparison
                    #  regardless of the commit message.
                    force_skip = row["SKIP_Y"].upper() == "Y"

                    #  Setting 'SKIP_Y' to 'N' will run the comparison
                    #  regardless of the commit message.
                    force_no_skip = row["SKIP_Y"].upper() == "N"

                    if not force_skip:
                        if no_msg or force_no_skip:
                            if base_name in prevs.keys():
                                run_bc(prevs[base_name], row["full_name"])
                            else:
                                if len(row["prev_full_name"]) == 0:
                                    print(f"New file: {base_name}")
                                    prevs[base_name] = row["full_name"]
                                    continue
                                else:
                                    warning = "UNEXPECTED PREVIOUS VERSION"
                                    print(f"{warning}: {base_name}")
                                    run_bc(
                                        row["prev_full_name"], row["full_name"]
                                    )

                            answer = input("Continue (or Keep left) [Y,n,k]? ")

                            if answer.lower() == "n":
                                break

                            if answer.lower() == "k":
                                print(
                                    "(Keep previous Left file for comparison)."
                                )
                            else:
                                prevs[base_name] = row["full_name"]
                        else:
                            prevs[base_name] = row["full_name"]

    print("Done (bak_to_git_2.py).")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
