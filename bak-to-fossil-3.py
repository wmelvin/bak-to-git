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
import sys
from collections import namedtuple
from datetime import datetime
from pathlib import Path


# -- Target-specific configuration:

input_csv = Path.cwd() / "prepare" / "out-1-files-changed-UPLOAD-1-newpath.csv"
#  "-newpath" = Changed '/Work/' to '/Projects/' in file paths.

fossil_repo = "bakrot.fossil"

fossil_init_date = "2020-08-17T11:20:00"
#  First tag in csv: 20200817_112125

repo_dir = "~/Desktop/test/bakrot_fossil"

# -- General configuration:

do_run = True
#  Set to False for debugging without actually running the fossil commands.
#  This will still copy files to the repository directory.

fossil_exe = "~/bin/fossil"

log_name = Path.cwd() / "log-bak-to-fossil-3.txt"


CommitProps = namedtuple(
    "FileProps", "sort_key, full_name, datetime_tag, base_name, commit_message"
)


def write_log(msg):
    print(msg)
    with open(log_name, "a") as log_file:
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


def fossil_create_repo(repo_dir: str):
    #  Only proceed if the Fossil repository does not exist.
    p = Path(repo_dir).joinpath(fossil_repo)
    if p.exists():
        sys.stderr.write("Fossil repository already exists: {0}\n".format(p))
        sys.exit(1)

    cmds = [
        fossil_exe,
        "init",
        fossil_repo,
        "--date-override",
        fossil_init_date,
    ]
    write_log(f"RUN: {log_fmt(cmds)}")
    if do_run:
        result = subprocess.run(cmds, cwd=repo_dir)
        assert result.returncode == 0


def fossil_open_repo(repo_dir: str):
    cmds = [fossil_exe, "open", fossil_repo]
    write_log(f"RUN: {log_fmt(cmds)}")
    if do_run:
        result = subprocess.run(cmds, cwd=repo_dir)
        assert result.returncode == 0


def main():
    write_log("BEGIN")

    target_path = Path(repo_dir).resolve()

    fossil_create_repo(target_path)

    fossil_open_repo(target_path)

    commit_list = []

    write_log(f"Read {input_csv}")

    with open(input_csv) as csv_file:
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
                    cmds = [fossil_exe, "add", item.base_name]
                    write_log("({0}) RUN: {1}".format(item.datetime_tag, cmds))
                    if do_run:
                        result = subprocess.run(cmds, cwd=target_path)
                        assert result.returncode == 0

        if len(commit_msg) == 0:
            commit_msg = f"({dt_tag})"
        else:
            commit_msg = commit_msg.strip()

        cmds = [
            fossil_exe,
            "commit",
            "-m",
            commit_msg,
            "--date-override",
            commit_dt,
        ]

        write_log("({0}) RUN: {1}".format(dt_tag, log_fmt(cmds)))

        if do_run:
            result = subprocess.run(cmds, cwd=target_path)
            assert result.returncode == 0

    write_log("END")

    print("Done (bak-to-fossil-3.py).")


if __name__ == "__main__":
    main()
