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

from bak_to_common import log_fmt


AppOptions = namedtuple(
    "AppOptions", "input_csv, skip_backup, log_dir, compare_cmd"
)


run_dt = datetime.now()

log_path = Path.cwd() / f"log-bak_to_git_2-{run_dt:%Y%m%d_%H%M%S}.txt"


def write_log(msg, do_print=False):
    if do_print:
        print(msg)
    with open(log_path, "a") as log_file:
        log_file.write(f"{msg}\n")


def run_compare(compare_cmd, left_file, right_file):
    print(f"\nCompare\n  L: {left_file}\n  R: {right_file}\n")

    cmds = [compare_cmd, left_file, right_file]

    write_log(f"RUN: {log_fmt(cmds)}")

    result = subprocess.run(
        cmds, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )

    if 0 < len(result.stdout):
        write_log(f"STDOUT: {result.stdout.strip()}")

    assert result.returncode in [0, 1, 2, 11, 12, 13]
    #  bcompare return codes:
    #    Code  Meaning
    #       0  Success
    #       1  Binary same
    #       2  Rules-based same
    #      11  Binary differences
    #      12  Similar
    #      13  Rules-based differences
    #
    # TODO: Look at return codes for other tools (kdiff3, meld).


def get_opts(argv) -> AppOptions:

    ap = argparse.ArgumentParser(
        description="BakToGit Step 2: Run Beyond Compare (bcompare) to "
        + "review source file changes between 'wipbak' backups. This is "
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
        help="Do not create a backup of the input CSV file. By default, a "
        + "backup copy is created at the start of a session.",
    )

    ap.add_argument(
        "--log-dir",
        dest="log_dir",
        action="store",
        help="Output directory for log files.",
    )

    ap.add_argument(
        "--compare-cmd",
        dest="compare_cmd",
        default="bcompare",
        action="store",
        help="Name of the executable command to launch the file comparison "
        + "tool. The default is 'bcompare' (Beyond Compare).",
    )

    args = ap.parse_args(argv[1:])

    opts = AppOptions(
        args.input_csv, args.skip_backup, args.log_dir, args.compare_cmd
    )

    assert Path(opts.input_csv).exists()
    assert Path(opts.input_csv).is_file()

    if opts.log_dir is not None:
        if not Path(opts.log_dir).exists():
            sys.stderr.write(
                f"ERROR: Log directory not found '{opts.log_dir}'"
            )
            sys.exit(1)

    return opts


def get_rename(add_command):
    """
    Checks add_command for "RENAME: <old_name>".
    Returns the value of old_name if there is a match.
    Otherwise returns an empty string.
    """
    if add_command is None or len(add_command) == 0:
        return ""
    s = add_command.strip()
    if s.lower().startswith("rename:"):
        old_name = s.split(":")[1].strip().strip('"').strip("'")
        assert 0 < len(old_name)
        return old_name
    else:
        return ""


def process_row(compare_cmd, row, prevs):
    print(f"Row sort_key = '{row['sort_key']}'")
    base_name = row["base_name"]
    no_msg = len(row["COMMIT_MESSAGE"]) == 0

    #  If the 'SKIP_Y' field is blank, then rows with an
    #  existing commit message are skipped.

    #  Setting 'SKIP_Y' to 'Y' will skip the comparison
    #  regardless of the commit message.
    if row["SKIP_Y"].lower() == "y":
        return True

    #  Setting 'SKIP_Y' to 'N' will run the comparison
    #  regardless of the commit message.
    no_skip = row["SKIP_Y"].lower() == "n"

    if no_msg or no_skip:
        base_rename = get_rename(row["ADD_COMMAND"])
        if 0 < len(base_rename):
            prev_key = base_rename
            print(f"\nRENAME: '{base_rename}'")
        else:
            prev_key = base_name

        if prev_key in prevs.keys():
            run_compare(compare_cmd, prevs[prev_key], row["full_name"])
        else:
            if len(row["prev_full_name"]) == 0:
                print(f"\nNew file: {base_name}")
                prevs[base_name] = row["full_name"]
                return True
            else:
                warning = "UNEXPECTED PREVIOUS VERSION"
                print(f"\n{warning}: {base_name}")
                run_compare(
                    compare_cmd, row["prev_full_name"], row["full_name"]
                )

        answer = input(
            "(k = Keep left file for next comparison) Continue [Y,n,k]? "
        )

        if answer.lower() == "n":
            print("\nStopping.\n")
            return False

        if answer.lower() == "k":
            print("\nKeeping previous Left file for comparison.\n")
        else:
            prevs[base_name] = row["full_name"]
            print("")
    else:
        prevs[base_name] = row["full_name"]
    return True


def main(argv):
    now_tag = datetime.now().strftime("%y%m%d_%H%M%S")

    opts = get_opts(argv)

    global log_path
    if opts.log_dir is not None:
        log_path = (
            Path(opts.log_dir).expanduser().resolve().joinpath(log_path.name)
        )

    write_log(f"BEGIN at {run_dt:%Y-%m-%d %H:%M:%S}")

    if not opts.skip_backup:
        #  Make a backup of the input_csv in case there are problems while
        #  manually editing the file.
        bak_suffix = f".{now_tag}.bak"
        p = Path(opts.input_csv)
        bak_path = p.with_name(f"z-{p.name}").with_suffix(bak_suffix)
        assert not bak_path.exists()
        print(f"\nSaving backup as '{bak_path.name}'\n")
        write_log(f"BACKUP: '{bak_path}'")
        shutil.copyfile(opts.input_csv, bak_path)

    write_log(f"READ: '{opts.input_csv}'")

    prevs = {}
    with open(opts.input_csv) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if len(row["sort_key"]) > 0:
                if not process_row(opts.compare_cmd, row, prevs):
                    break

    write_log(f"END at {datetime.now():%Y-%m-%d %H:%M:%S}")

    print("Done (bak_to_git_2.py).")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
