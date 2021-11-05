#!/usr/bin/env python3

# ---------------------------------------------------------------------
#  bak_to_fossil_3.py
#
#  Step 3: Read a CSV file edited in step 2 where commit messages are
#  added and files to be skipped are flagged.
#
#  Run fossil (instead of git) to commit each change with the
#  specified date and time.
#
#  William Melvin
# ---------------------------------------------------------------------

import argparse
import csv
import subprocess
import sys

from collections import namedtuple
from datetime import datetime
from pathlib import Path


AppOptions = namedtuple(
    "AppOptions",
    "input_csv, repo_dir, repo_name, init_date, log_dir, fossil_exe"
)

CommitProps = namedtuple(
    "FileProps", "sort_key, full_name, datetime_tag, base_name, commit_message"
)


log_path = Path.cwd() / "log-bak_to_fossil_3.txt"


def write_log(msg):
    print(msg)
    with open(log_path, "a") as log_file:
        log_file.write(f"[{datetime.now():%Y%m%d_%H%M%S}] {msg}\n")


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
            for line in src_file.readlines():
                #  Filter out the email address I was using at the time.
                s = line.replace("(**REDACTED**)", "")
                s = s.replace("**REDACTED**", "")
                dst_file.write(s)


def fossil_create_repo(opts: AppOptions, do_run: bool):
    #  Only proceed if the Fossil repository does not exist.
    p = Path(opts.repo_dir).joinpath(opts.repo_name)
    if p.exists():
        sys.stderr.write("Fossil repository already exists: {0}\n".format(p))
        sys.exit(1)

    cmds = [
        opts.fossil_exe,
        "init",
        opts.repo_name,
        "--date-override",
        opts.init_date,
    ]
    write_log(f"RUN: {log_fmt(cmds)}")
    if do_run:
        result = subprocess.run(cmds, cwd=opts.repo_dir)
        assert result.returncode == 0


def fossil_open_repo(opts: AppOptions, do_run: bool):
    cmds = [opts.fossil_exe, "open", opts.repo_name]
    write_log(f"RUN: {log_fmt(cmds)}")
    if do_run:
        result = subprocess.run(cmds, cwd=opts.repo_dir)
        assert result.returncode == 0


def get_opts(argv) -> AppOptions:

    ap = argparse.ArgumentParser(
        description="BakToGit - Step 3 (alternate): Using fossil instead of "
        + "git."
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

    args = ap.parse_args(argv[1:])

    repo_path = Path(args.repo_dir).expanduser().resolve()

    opts = AppOptions(
        args.input_csv,
        str(repo_path),
        "bakrot.fossil",
        "2020-08-17T11:20:00",
        args.log_dir,
        args.fossil_exe
    )
    # TODO: Replace hard-coded values.

    p = Path(opts.input_csv)
    if not (p.exists() and p.is_file()):
        sys.stderr.write(f"ERROR: File not found: '{p}'")
        sys.exit(1)

    d = Path(opts.repo_dir)
    if not (d.exists() and d.is_dir()):
        sys.stderr.write(f"ERROR: Directory not found: '{d}'")
        sys.exit(1)

    if not d.joinpath(".git").exists():
        sys.stderr.write(f"ERROR: Git repository directory not found in '{d}'")
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

    commit_list = []

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
                s = item.commit_message.strip()
                if 0 < len(s) and not s.endswith("."):
                    s += ". "
                commit_msg += s
                target_name = target_path / Path(item.base_name).name
                existing_file = Path(target_name).exists()

                print(f"COPY {item.full_name}")
                print(f"  TO {target_name}")

                #  Copy file to target repo location.
                copy_filtered_content(item.full_name, target_name)

                if not existing_file:
                    cmds = [opts.fossil_exe, "add", item.base_name]
                    write_log("({0}) RUN: {1}".format(item.datetime_tag, cmds))
                    if do_commit:
                        result = subprocess.run(cmds, cwd=target_path)
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
            result = subprocess.run(cmds, cwd=target_path)
            assert result.returncode == 0

    write_log("END")

    print("Done (bak_to_fossil_3.py).")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
