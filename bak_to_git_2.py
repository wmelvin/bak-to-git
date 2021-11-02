#!/usr/bin/env python3

# ---------------------------------------------------------------------
#  bak_to_git_2.py
#
#  Step 2: Read a CSV file, created in step 1, and launch the 'Beyond
#  Compare' file differencing tool to see changes.
#
#  This script does not write any output files.
#
#  Manually add commit messages to the CSV file, and select files to
#  skip to batch changes into a single commit.
#
#  William Melvin
#
#  2021-08-24
# ---------------------------------------------------------------------

import csv
import subprocess
from pathlib import Path


#  Specify input file.
# input_csv = Path.cwd() / 'output' / 'out-1-files-changed.csv'
# input_csv = Path.cwd() / 'test' / 'out-1-files-changed-TEST-1.csv'
input_csv = Path.cwd() / "prepare" / "out-1-files-changed-EDIT.csv"


def run_bc(left_file, right_file):
    print("Compare\n  L: {0}\n  R: {1}".format(left_file, right_file))
    subprocess.run(["bcompare", left_file, right_file])


def main():
    prevs = {}
    with open(input_csv) as csv_file:
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
    main()
