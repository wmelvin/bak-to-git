#!/usr/bin/env python3

# ---------------------------------------------------------------------
#  bak_to_git_2.py
# ---------------------------------------------------------------------

import argparse
import csv
import shutil
import subprocess
import sys

from collections import namedtuple
from datetime import datetime
from pathlib import Path

from bak_to_common import ask_to_continue, log_fmt

from btg2_stats import ProgressStats


run_dt = datetime.now()

log_path = Path.cwd() / f"log-bak_to_git_2-{run_dt:%Y%m%d_%H%M%S}.txt"


AppOptions = namedtuple(
    "AppOptions",
    "csv_path, skip_backup, log_dir, run_cmd, stats_file, do_report",
)


def write_log(msg, do_print=False):
    if do_print:
        print(msg)
    with open(log_path, "a") as log_file:
        log_file.write(f"{msg}\n")


def run_compare(run_cmd, left_file, right_file):
    print(f"\nCompare\n  L: {left_file}\n  R: {right_file}\n")

    cmds = [run_cmd, left_file, right_file]

    write_log(f"RUN: {log_fmt(cmds)}")

    result = subprocess.run(
        cmds,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
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
        dest="run_cmd",
        default="bcompare",
        action="store",
        help="Alternate executable command to launch a file comparison "
        + "tool. The tool must take the names of two files to compare as "
        + "the first two command-line arguments. The default is 'bcompare' "
        + "(Beyond Compare by Scooter Software).",
    )

    ap.add_argument(
        "--report",
        dest="do_report",
        action="store_true",
        help="Print a progress report to the console instead of doing an "
        + "interactive session.",
    )

    ap.add_argument(
        "--stats-file",
        dest="stats_file",
        type=str,
        action="store",
        help="Name of the file in which to store data used for progress "
        + "estimates when running with the --report option.",
    )

    args = ap.parse_args(argv[1:])

    #  Also skip backup if running the progress (stats) report.
    skip_bak = args.skip_backup or args.do_report

    opts = AppOptions(
        Path(args.input_csv),
        skip_bak,
        args.log_dir,
        args.run_cmd,
        args.stats_file,
        args.do_report,
    )

    if not (opts.csv_path.exists() and opts.csv_path.is_file()):
        sys.stderr.write(f"ERROR: File not found '{opts.csv_path}'")
        sys.exit(1)

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


def process_row(run_cmd, row, prevs, stats: ProgressStats):
    print(f"Row sort_key = '{row['sort_key']}'")
    base_name = row["base_name"]
    no_msg = len(row["COMMIT_MESSAGE"]) == 0

    #  If the 'SKIP_Y' field is blank, then rows with an
    #  existing commit message are skipped.

    #  Setting 'SKIP_Y' to 'Y' will skip the comparison
    #  regardless of the commit message.
    if row["SKIP_Y"].lower() == "y":
        stats.count_skip()
        return True

    if not no_msg:
        stats.count_commit()

    #  If this session is for statistics report then skip the interaction.
    if stats.do_report:
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
            run_compare(run_cmd, prevs[prev_key], row["full_name"])
        else:
            if len(row["prev_full_name"]) == 0:
                print(f"\nNew file: {base_name}")
                prevs[base_name] = row["full_name"]
                return True
            else:
                warning = "UNEXPECTED PREVIOUS VERSION"
                print(f"\n{warning}: {base_name}")
                run_compare(run_cmd, row["prev_full_name"], row["full_name"])

        answer = ask_to_continue(
            "(k = Keep left file for next comparison) Continue [Y,n,k]? ",
            ["y", "n", "k", ""],
        )

        if answer == "n":
            print("\nStopping.\n")
            return False

        if answer == "k":
            print("\nKeeping previous Left file for comparison.\n")
            stats.log_act("skip")
        else:
            stats.log_act("commit")
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

    stats = ProgressStats(
        opts.stats_file, save_immediate=True, is_reporting=opts.do_report
    )
    stats.start_session(opts.csv_path)

    if opts.do_report:
        stats.load()

    if not opts.skip_backup:
        #  Make a backup of the source csv file in case there are problems
        #  while manually editing the file.

        bak_suffix = f".{now_tag}.bak"

        bak_path = opts.csv_path.with_name(
            f"z-{opts.csv_path.name}"
        ).with_suffix(bak_suffix)

        assert not bak_path.exists()

        print(f"\nSaving backup as '{bak_path.name}'\n")
        write_log(f"BACKUP: '{bak_path}'")
        shutil.copyfile(opts.csv_path, bak_path)

    write_log(f"READ: '{opts.csv_path}'")

    prevs = {}
    with open(opts.csv_path) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if len(row["sort_key"]) > 0:
                stats.count_row()
                if not process_row(opts.run_cmd, row, prevs, stats):
                    break

    stats.stop_session()
    stats.save()

    if opts.do_report:
        rpt = stats.report()
        print(rpt)
        write_log(rpt)
    else:
        print("Done (bak_to_git_2.py).")

    write_log(f"END at {datetime.now():%Y-%m-%d %H:%M:%S}")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
