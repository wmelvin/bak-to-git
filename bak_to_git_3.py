#!/usr/bin/env python3

# ---------------------------------------------------------------------
#  bak_to_git_3.py
#
# ---------------------------------------------------------------------

import argparse
import csv
import subprocess
import sys

from collections import namedtuple
from datetime import datetime
from datetime import timedelta
from pathlib import Path


AppOptions = namedtuple("AppOptions", "input_csv, repo_dir, do_commit")


# -- Target-specific configuration:


# repo_dir = "~/Desktop/test/bakrot_repo"

# -- General configuration:

# do_run = False
#  Set to False for debugging without actually running git commands.
#  This will still copy files to the repo directory.

log_name = Path.cwd() / "log-bak_to_git_3.txt"


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


def git_date_strings(dt_tag):

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

    #  I feel like the author date should be a little before
    #  the committer date, rather than exactly the same,
    #  but that might be silly.
    #
    author_dt = commit_dt - timedelta(seconds=5)

    return (
        author_dt.strftime("%Y-%m-%dT%H:%M:%S"),
        commit_dt.strftime("%Y-%m-%dT%H:%M:%S"),
    )


def copy_filtered_content(src_name, dst_name):
    with open(src_name, "r") as src_file:
        with open(dst_name, "w") as dst_file:
            for line in src_file.readlines():
                #  Filter out the email address I was using at the time.
                s = line.replace("(**REDACTED**)", "")
                s = s.replace("**REDACTED**", "")
                dst_file.write(s)


def get_opts(argv) -> AppOptions:

    ap = argparse.ArgumentParser(description="BakToGit - step 3: ...")
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
        help="Path to repository directory. This should be a new repository, "
        + "or one where the first commit from the wipbak files is an "
        + "appropriate next commit.",
    )

    ap.add_argument(
        "--do-commit",
        dest="do_commit",
        action="store_true",
        help="Copy files to the repository and run the git command to commit "
        + "changes. By default, this application runs in 'what-if' mode "
        + "where changes are listed but not applied.",
    )

    args = ap.parse_args(argv[1:])

    opts = AppOptions(args.input_csv, args.repo_dir, args.do_commit)

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

    return opts


def main(argv):
    write_log("BEGIN")

    opts = get_opts(argv)

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

    target_path = Path(opts.repo_dir).resolve()

    for dt_tag in datetime_tags:
        print(dt_tag)

        author_dt, commit_dt = git_date_strings(dt_tag)

        git_env = {
            "GIT_COMMITTER_DATE": commit_dt,
            "GIT_AUTHOR_DATE": author_dt,
        }
        write_log(f"GIT ENV {git_env}")

        commit_msg = ""

        for item in commit_list:
            if item.datetime_tag == dt_tag:
                s = item.commit_message.strip()
                if 0 < len(s) and not s.endswith("."):
                    s += ". "
                commit_msg += s
                target_name = target_path / Path(item.base_name).name
                existing_file = Path(target_name).exists()

                write_log(f"COPY {item.full_name}")
                write_log(f"  TO {target_name}")

                if opts.do_commit:
                    #  Copy file to target repo location.
                    copy_filtered_content(item.full_name, target_name)

                if not existing_file:
                    cmds = ["git", "add", item.base_name]
                    write_log(
                        "({0}) RUN: {1}".format(
                            item.datetime_tag, log_fmt(cmds)
                        )
                    )
                    if opts.do_commit:
                        result = subprocess.run(
                            cmds, cwd=target_path, env=git_env
                        )
                        assert result.returncode == 0

        if len(commit_msg) == 0:
            commit_msg = f"({dt_tag})"
        else:
            commit_msg = commit_msg.strip()

        cmds = ["git", "commit", "-a", "-m", commit_msg]

        write_log("({0}) RUN: {1}".format(dt_tag, log_fmt(cmds)))

        if opts.do_commit:
            result = subprocess.run(cmds, cwd=target_path, env=git_env)
            assert result.returncode == 0

    write_log("END")

    print("Done (bak_to_git_3.py).")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
