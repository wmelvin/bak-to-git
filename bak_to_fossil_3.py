#!/usr/bin/env python3

# ---------------------------------------------------------------------
#  bak_to_fossil_3.py
#
#  Step 3 (alternate): Read data from a CSV file that was edited in
#  step 2, where commit messages were added and files to be skipped
#  were flagged.  Run fossil (instead of git) to commit each change
#  with the specified date and time.
#
#  This script is only for the initial creation and population of a new
#  (empty) Fossil repository.
#
#  The Fossil repository file is created (fossil init) by this script.
#  It must not already exist.
#
#  The directory for the repository will be created by this script if
#  it does not exist.
#
# ---------------------------------------------------------------------

import argparse
import csv
import subprocess
import sys

from collections import namedtuple
from datetime import datetime
from pathlib import Path
from textwrap import dedent
from typing import List


AppOptions = namedtuple(
    "AppOptions",
    "input_csv, repo_dir, repo_name, init_date, log_dir, fossil_exe, "
    + "filter_file",
)

CommitProps = namedtuple(
    "CommitProps", "sort_key, full_name, datetime_tag, base_name, "
    + "commit_message, add_command"
)


log_path = Path.cwd() / "log-bak_to_fossil_3.txt"

filter_list = []


def write_log(msg):
    print(msg)
    with open(log_path, "a") as log_file:
        # log_file.write(f"[{datetime.now():%Y%m%d_%H%M%S}] {msg}\n")
        log_file.write(f"{msg}\n")


def log_fmt(items):
    s = ""
    for item in items:
        if " " in item:
            s += f'"{item}" '
        else:
            s += f"{item} "
    return s.strip()


def get_date_string(dt_tag):
    #
    #  Tag format: yyyymmdd_hhmmss
    #       index: 012345678901234
    #
    iso_fmt = "{0}-{1}-{2}T{3}:{4}:{5}".format(
        dt_tag[:4],
        dt_tag[4:6],
        dt_tag[6:8],
        dt_tag[9:11],
        dt_tag[11:13],
        dt_tag[13:],
    )
    commit_dt = datetime.fromisoformat(iso_fmt)
    return commit_dt.strftime("%Y-%m-%dT%H:%M:%S")


def copy_filtered_content(src_name, dst_name):
    with open(src_name, "r") as src_file:
        with open(dst_name, "w") as dst_file:
            for num, line in enumerate(src_file.readlines(), start=1):
                for filter_item in filter_list:
                    if filter_item[0] in line:
                        write_log(f"FILTER {src_name} ({num}): {filter_item}")
                        line = line.replace(filter_item[0], filter_item[1])
                dst_file.write(line)


def fossil_create_repo(opts: AppOptions, do_run: bool):
    d = Path(opts.repo_dir)
    p = d.joinpath(opts.repo_name)

    #  Only proceed if the Fossil repository does not already exist.
    if p.exists():
        sys.stderr.write("Fossil repository already exists: {0}\n".format(p))
        sys.exit(1)

    if not d.exists():
        write_log(f"mkdir {d}")
        d.mkdir()

    cmds = [
        opts.fossil_exe,
        "init",
        opts.repo_name,
        "--date-override",
        opts.init_date,
    ]
    write_log(f"RUN: {log_fmt(cmds)}")
    if do_run:
        result = subprocess.run(
            cmds,
            cwd=opts.repo_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        write_log(f"STDOUT: {result.stdout.strip()}")
        assert result.returncode == 0


def fossil_open_repo(opts: AppOptions, do_run: bool):
    cmds = [opts.fossil_exe, "open", opts.repo_name]
    write_log(f"RUN: {log_fmt(cmds)}")
    if do_run:
        result = subprocess.run(
            cmds,
            cwd=opts.repo_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        write_log(f"STDOUT: {result.stdout.strip()}")
        assert result.returncode == 0


def strip_outer_quotes(text: str) -> str:
    s = text.strip()
    if len(s) == 0:
        return s
    if s[0] == '"':
        return s.strip('"')
    if s[0] == "'":
        return s.strip("'")
    return s


def load_filter_list(filter_file):
    if filter_file is None:
        return
    with open(filter_file) as f:
        lines = f.readlines()
    for line in lines:
        s = line.strip()
        if 0 < len(s) and not s.startswith("#"):
            a = s.split(",")
            assert 2 == len(a)
            # filter_item = (a[0].strip().strip('"'), a[1].strip().strip('"'))
            filter_item = (strip_outer_quotes(a[0]), strip_outer_quotes(a[1]))
            filter_list.append(filter_item)


def get_opts(argv) -> AppOptions:

    ap = argparse.ArgumentParser(
        description="BakToGit Step 3 (alternate): Use fossil instead of "
        + "git..."
    )
    # TODO: Fill in description.

    ap.add_argument(
        "input_csv",
        action="store",
        help="Path to CSV file, manually edited in step 2 to add commit "
        + "messages.",
    )

    ap.add_argument(
        "repo_dir",
        action="store",
        help="Path to repository directory. This should be a new (empty) "
        + "repository, or one where the first commit from the wipbak files "
        + "is an appropriate next commit.",
    )

    ap.add_argument(
        "--repo-name",
        dest="repo_name",
        action="store",
        help="Name of the fossil repository (usually has a .fossil "
        + "extension).",
    )

    ap.add_argument(
        "--init-date",
        dest="init_date",
        action="store",
        help="Date and time to use for fossil repository initialization. "
        + "This should be at, or before, the time of the first source (.bak) "
        + "file to commit. Use the ISO 8601 format for date and time "
        + "(yyyy-mm-ddThh:mm:ss). Example: 2021-07-14T16:20:01",
    )

    ap.add_argument(
        "--log-dir",
        dest="log_dir",
        action="store",
        help="Output directory for log files.",
    )

    ap.add_argument(
        "--fossil-exe",
        dest="fossil_exe",
        action="store",
        help="Path to the Fossil executable file.",
    )

    ap.add_argument(
        "--filter-file",
        dest="filter_file",
        action="store",
        help="Path to text file with list of string replacements in "
        + 'comma-separated format ("old string", "new string").',
    )

    args = ap.parse_args(argv[1:])

    repo_path = Path(args.repo_dir).expanduser().resolve()

    repo_name = args.repo_name
    if repo_name is None:
        #  Default to repo_dir name with a .fossil suffix.
        repo_name = f"{repo_path.stem}.fossil"

    fossil_exe = args.fossil_exe
    if fossil_exe is None:
        #  Default to assuming the 'fossil' command is available in the PATH.
        fossil_exe = "fossil"

    opts = AppOptions(
        args.input_csv,
        str(repo_path),
        repo_name,
        args.init_date,
        args.log_dir,
        args.fossil_exe,
        args.filter_file,
    )

    p = Path(opts.input_csv)
    if not (p.exists() and p.is_file()):
        sys.stderr.write(f"ERROR: File not found: '{p}'")
        sys.exit(1)

    if opts.log_dir is not None:
        if not Path(opts.log_dir).exists():
            sys.stderr.write(
                f"ERROR: Log directory not found '{opts.log_dir}'"
            )
            sys.exit(1)

    if opts.fossil_exe is not None:
        if not Path(opts.fossil_exe).exists():
            sys.stderr.write(f"ERROR: File not found '{opts.fossil_exe}'")
            sys.exit(1)

    if opts.filter_file is not None:
        if not Path(opts.filter_file).exists():
            sys.stderr.write(f"ERROR: File not found '{opts.filter_file}'")
            sys.exit(1)

    return opts


def main(argv):
    opts = get_opts(argv)

    global log_path
    if opts.log_dir is not None:
        log_path = (
            Path(opts.log_dir).expanduser().resolve().joinpath(log_path.name)
        )

    write_log("BEGIN")

    answer = input(
        "Commit to repository (otherwise run in 'what-if' mode) [N,y]? "
    )
    if answer.lower() == "y":
        do_commit = True
        write_log("MODE: COMMIT")
    else:
        do_commit = False
        write_log("MODE: What-if (actions logged, repository not affected)")

    fossil_create_repo(opts, do_commit)

    fossil_open_repo(opts, do_commit)

    target_path = Path(opts.repo_dir)

    load_filter_list(opts.filter_file)

    commit_list: List[CommitProps] = []

    write_log(f"Read {opts.input_csv}")

    with open(opts.input_csv) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            if len(row["full_name"]) > 0:
                do_skip = str(row["SKIP_Y"]).upper() == "Y"
                if not do_skip:
                    commit_list.append(
                        CommitProps(
                            row["sort_key"],
                            row["full_name"],
                            row["datetime_tag"],
                            row["base_name"],
                            row["COMMIT_MESSAGE"],
                            row["ADD_COMMAND"],
                        )
                    )

    commit_list.sort()

    datetime_tags = []
    for item in commit_list:
        if item.datetime_tag not in datetime_tags:
            datetime_tags.append(item.datetime_tag)

    datetime_tags.sort()

    for dt_tag in datetime_tags:
        print(dt_tag)

        commit_dt = get_date_string(dt_tag)

        commit_msg = ""

        for item in commit_list:
            if item.datetime_tag == dt_tag:
                com_msg = item.commit_message.strip()

                #  If the commit_message has only a single period, that
                #  indicates the message is attached to another file in
                #  the same commit, and that the current file was reviewed
                #  in Step 2 of the overall process.
                if com_msg == ".":
                    com_msg = ""

                if 0 < len(com_msg) and not com_msg.endswith("."):
                    com_msg += ". "

                commit_msg += com_msg

                add_cmd = item.add_command.strip()

                target_name = target_path / Path(item.base_name).name
                existing_file = Path(target_name).exists()

                write_log(f"COPY {item.full_name}")
                write_log(f"  TO {target_name}")

                if do_commit:
                    #  Copy file to target repo location.
                    copy_filtered_content(item.full_name, target_name)

                if not existing_file:
                    cmds = [opts.fossil_exe, "add", item.base_name]
                    write_log("({0}) RUN: {1}".format(item.datetime_tag, cmds))
                    if do_commit:
                        result = subprocess.run(
                            cmds,
                            cwd=target_path,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                        )
                        write_log(f"STDOUT: {result.stdout.strip()}")
                        assert result.returncode == 0

        if len(commit_msg) == 0:
            commit_msg = f"({dt_tag})"
        else:
            commit_msg = commit_msg.strip()

        cmds = [
            opts.fossil_exe,
            "commit",
            "-m",
            commit_msg,
            "--date-override",
            commit_dt,
        ]

        write_log("({0}) RUN: {1}".format(dt_tag, log_fmt(cmds)))

        if do_commit:
            result = subprocess.run(
                cmds,
                cwd=target_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            write_log(f"STDOUT: {result.stdout.strip()}")
            assert result.returncode == 0

    write_log("END")

    if do_commit:
        print(
            dedent(
                """
                WARNING: Log file may contain initial password for the Fossil
                repository default admin-user. You should change the password,
                especially if it will be exposed outside the local system.
                You can also edit the log file to remove the password.
                """
            )
        )

    print(f"Log file is '{log_path}'\n")

    print("Done (bak_to_fossil_3.py).")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
