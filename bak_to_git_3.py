#!/usr/bin/env python3

# ---------------------------------------------------------------------
#  bak_to_git_3.py
# ---------------------------------------------------------------------

import argparse
import csv
import os
import subprocess
import sys

from collections import namedtuple
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import List

from bak_to_common import (
    datetime_fromisoformat,
    log_fmt,
    plain_quotes,
    split_quoted,
    strip_outer_quotes,
)


AppOptions = namedtuple(
    "AppOptions", "input_csv, repo_dir, log_dir, what_if, filter_file"
)


CommitProps = namedtuple(
    "CommitProps",
    "sort_key, full_name, datetime_tag, base_name, "
    + "commit_message, add_command",
)

run_dt = datetime.now()

log_path = Path.cwd() / f"log-bak_to_git_3-{run_dt:%Y%m%d_%H%M%S}.txt"

filter_list = []


def write_log(msg):
    print(msg)
    with open(log_path, "a") as log_file:
        # log_file.write(f"[{datetime.now():%Y%m%d_%H%M%S}] {msg}\n")
        log_file.write(f"{msg}\n")


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

    commit_dt = datetime_fromisoformat(iso_fmt)

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
            for num, line in enumerate(src_file.readlines(), start=1):
                for filter_item in filter_list:
                    if filter_item[0] in line:
                        write_log(f"FILTER {src_name} ({num}): {filter_item}")
                        line = line.replace(filter_item[0], filter_item[1])
                dst_file.write(line)


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

    ap = argparse.ArgumentParser(description="BakToGit Step 3: ...")
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
        "--filter-file",
        dest="filter_file",
        action="store",
        help="Path to text file with list of string replacements in "
        + 'comma-separated format ("old string", "new string").',
    )

    ap.add_argument(
        "--what-if",
        dest="what_if",
        action="store_true",
        help="Run in 'what-if' mode, and do not ask to commit changes.",
    )

    args = ap.parse_args(argv[1:])

    opts = AppOptions(
        args.input_csv,
        args.repo_dir,
        args.log_dir,
        args.what_if,
        args.filter_file,
    )

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

    if opts.filter_file is not None:
        if not Path(opts.filter_file).exists():
            sys.stderr.write(f"ERROR: File not found '{opts.filter_file}'")
            sys.exit(1)

    return opts


def git_mv_cmd(add_cmd, base_name):
    old_name = add_cmd.split(":")[1].strip().strip('"').strip("'")
    assert 0 < len(old_name)
    s = f'mv "{old_name}" "{base_name}"'
    return s


def run_git(cmds, run_dir, git_env):
    result = subprocess.run(cmds, cwd=run_dir, env=git_env)
    assert result.returncode == 0


def ask_to_continue():
    answer = input(
        "Commit to repository (otherwise run in 'what-if' mode) [N,y]? "
    )
    return answer.lower()


def main(argv):
    opts = get_opts(argv)

    global log_path
    if opts.log_dir is not None:
        log_path = (
            Path(opts.log_dir).expanduser().resolve().joinpath(log_path.name)
        )

    write_log(f"BEGIN at {run_dt:%Y-%m-%d %H:%M:%S}")

    if opts.what_if:
        do_commit = False
    else:
        do_commit = ask_to_continue() == "y"

    if do_commit:
        write_log("MODE: COMMIT")
    else:
        write_log("MODE: What-if (actions logged, repository not affected)")

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
        pre_commit = []
        post_commit = []
        commit_this: List[CommitProps] = []

        for item in commit_list:
            if item.datetime_tag == dt_tag:
                com_msg = plain_quotes(item.commit_message.strip())

                #  Stop on non-ascii characters in the commit message.
                #  TODO: This check should be temporary, just to see what
                #  chars, besides left and right quotes, are showing up.
                as_ascii = ascii(com_msg)
                # if "\\u" in as_ascii:
                if "\\" in as_ascii:
                    print(com_msg)
                    print(as_ascii)
                    assert 0

                #  If the commit_message has only a single charcter,
                #  treat it as ditto (no matter what character) indicating
                #  the message is attached to another file in the same
                #  commit, and the current file was reviewed in Step 2 of
                #  the overall process.
                if len(com_msg) == 1:
                    com_msg = ""

                if 0 < len(com_msg) and not com_msg.endswith("."):
                    com_msg += ". "

                commit_msg += com_msg

                add_cmd = item.add_command.strip()
                if 0 < len(add_cmd):
                    if add_cmd.lower().startswith("pre:"):
                        pre_commit.append(add_cmd[4:].strip())
                    elif add_cmd.lower().startswith("post:"):
                        post_commit.append(add_cmd[5:].strip())
                    elif add_cmd.lower().startswith("rename:"):
                        pre_commit.append(git_mv_cmd(add_cmd, item.base_name))

                commit_this.append(item)

        #  Run any pre-commit git commands (such as 'mv').
        if 0 < len(pre_commit):
            for git_args in pre_commit:
                cmds = ["git"] + split_quoted(git_args)
                write_log("({0}) RUN (PRE): {1}".format(dt_tag, log_fmt(cmds)))
                if do_commit:
                    run_git(cmds, target_path, git_env)

        #  Copy files to commit for current date_time tag.
        for props in commit_this:
            target_name = target_path / Path(props.base_name).name
            existing_file = Path(target_name).exists()

            write_log(f"COPY {props.full_name}")
            write_log(f"  TO {target_name}")

            if do_commit:
                #  Copy file to target repo location.
                copy_filtered_content(props.full_name, target_name)
                ts = datetime_fromisoformat(commit_dt).timestamp()
                os.utime(target_name, (ts, ts))

            if not existing_file:
                cmds = ["git", "add", props.base_name]
                write_log(
                    "({0}) RUN: {1}".format(props.datetime_tag, log_fmt(cmds))
                )
                if do_commit:
                    run_git(cmds, target_path, git_env)

        #  Run 'git commit' for current date_time tag.
        if len(commit_msg) == 0:
            commit_msg = f"({dt_tag})"
        else:
            commit_msg = commit_msg.strip()

        cmds = ["git", "commit", "-a", "-m", commit_msg]

        write_log("({0}) RUN: {1}".format(dt_tag, log_fmt(cmds)))

        if do_commit:
            run_git(cmds, target_path, git_env)

        #  Run any post-commit git commands (such as 'tag').
        if 0 < len(post_commit):
            for git_args in post_commit:
                cmds = ["git"] + split_quoted(git_args)
                write_log(
                    "({0}) RUN (POST): {1}".format(dt_tag, log_fmt(cmds))
                )
                if do_commit:
                    run_git(cmds, target_path, git_env)

    write_log(f"END at {datetime.now():%Y-%m-%d %H:%M:%S}")

    print("Done (bak_to_git_3.py).")


if __name__ == "__main__":
    sys.exit(main(sys.argv))
