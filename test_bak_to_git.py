import pytest
import re

# from datetime import datetime
from pathlib import Path

import bak_to_git_1
import bak_to_git_2
import bak_to_git_3
import bak_to_fossil_3

from bak_to_common import split_quoted


def test_split_quoted():
    #  Text with no quotes should be split on spaces.
    s = "a b c  d"
    assert ["a", "b", "c", "d"] == split_quoted(s)

    #  Text in double-quotes should be grouped, including any
    #  single-quoted text inside.
    s = "a \"b 'c d'\""
    assert ["a", "b 'c d'"] == split_quoted(s)

    #  Text in single-quotes should be grouped, including any
    #  double-quoted text inside.
    s = "a 'b \"c d\"'"
    assert ["a", 'b "c d"'] == split_quoted(s)


def csv_header_row():
    return "{},{},{},{},{},{},{},{},{},{}".format(
        "row",
        "sort_key",
        "full_name",
        "prev_full_name",
        "datetime_tag",
        "base_name",
        "SKIP_Y",
        "COMMIT_MESSAGE",
        "ADD_COMMAND",
        "NOTES",
    )


def csv_data_row(
    row_num,
    sort_key,
    full_name,
    prev_full_name,
    datetime_tag,
    base_name,
    skip_y,
    commit_message,
    add_command,
    notes
):
    return "{},{},{},{},{},{},{},{},{},{}".format(
        row_num,
        sort_key,
        full_name,
        prev_full_name,
        datetime_tag,
        base_name,
        skip_y,
        commit_message,
        add_command,
        notes
    )


@pytest.fixture(scope="module")
def temp_paths_1(tmp_path_factory):
    """
    Makes temporary directories, for testing bak_to_git_1, and populates them
    with test files. Returns pathlib.Path objects for each.
    """
    temp_path: Path = tmp_path_factory.mktemp("baktogit1")
    bak_path = temp_path / "_0_bak"
    bak_path.mkdir()
    (bak_path / "test.txt.20211001_083010.bak").write_text("One\n")
    (bak_path / "test.txt.20211101_093011.bak").write_text("Tahoo\n")
    (bak_path / "test.txt.20211201_103012.bak").write_text("Tharee\n")
    return temp_path, bak_path


def test_bak_to_git_1(temp_paths_1):
    temp_path, bak_path = temp_paths_1
    args = [
        "bak_to_git_1.py",
        str(bak_path),
        "--output-dir",
        str(temp_path),
        "--write-debug",
    ]

    bak_to_git_1.main(args)

    #  An output sub-folder, named for the current date_time, should exist.
    pat = re.compile(r"^\d{6}_\d{6}$")
    matches = []
    for p in temp_path.iterdir():
        print(p)
        if p.is_dir() and pat.match(str(p.name)):
            matches.append(p)
    print(matches)
    assert len(matches) == 1

    #  The output CSV file should exist.
    csv_file = Path(matches[0]) / "step-1-files-changed.csv"
    assert csv_file.exists()

    #  The date_time tag from the test data should be in the CSV file.
    csv_text = csv_file.read_text()
    print(csv_text)
    assert "20211201_103012" in csv_text

    #  There should be 1 header row, 3 data rows, 3 separator rows,
    #  and 1 blank line at the end.
    csv_lines = csv_text.split("\n")

    # for x, s in enumerate(csv_lines, start=1):
    #     print(f"({x}): {s}")

    assert 8 == len(csv_lines)


def bak_base_name(bak_name):
    """
    Takes a backup name and returns the base name.
    Example:
      Backup name = "test_bak_to_git.py.20211201_134317.bak"
        Base name = "test_bak_to_git.py"
    """
    return bak_name.rsplit(".", 2)[0]


@pytest.fixture(scope="module")
def temp_paths_2(tmp_path_factory):
    """
    Makes temporary directories, for testing bak_to_git_2, and populates them
    with test files. Returns pathlib.Path objects for each.
    """
    temp_path: Path = tmp_path_factory.mktemp("baktogit2")
    bak_path = temp_path / "_0_bak"
    bak_path.mkdir()

    t1 = "20211001_083010"
    p1 = bak_path / f"test.txt.{t1}.bak"
    p1.write_text("One\n")

    t2 = "20211101_093011"
    p2 = bak_path / f"test.txt.{t2}.bak"
    p2.write_text("Tahoo\n")

    t3 = "20211201_103012"
    p3 = bak_path / f"test.txt.{t3}.bak"
    p3.write_text("Tharee\n")

    csv_path = temp_path / "step-1-files-changed.csv"
    csv_lines = []
    csv_lines.append(csv_header_row())
    csv_lines.append(
        csv_data_row(
            "1",
            f"{t1}:{bak_base_name(p1.name)}",
            str(p1),
            "",
            t1,
            bak_base_name(p1.name),
            "",
            "",
            "",
            "",
        )
    )
    csv_lines.append("2,,,,,,,,,")
    csv_lines.append(
        csv_data_row(
            "3",
            f"{t2}:{bak_base_name(p2.name)}",
            str(p2),
            str(p1),
            t2,
            bak_base_name(p2.name),
            "",
            "",
            "",
            "",
        )
    )
    csv_lines.append("4,,,,,,,,,")
    csv_lines.append(
        csv_data_row(
            "5",
            f"{t3}:{bak_base_name(p3.name)}",
            str(p3),
            str(p2),
            t3,
            bak_base_name(p3.name),
            "",
            "",
            "",
            "",
        )
    )
    csv_lines.append("6,,,,,,,,,")

    csv_path.write_text("\n".join(csv_lines))

    return temp_path, bak_path, csv_path


def test_bak_to_git_2(temp_paths_2, monkeypatch):

    compared = []

    def mock_compare(run_cmd, left_file, right_file):
        # print(f"RUN: {run_cmd}")
        # print(f"L: {left_file}")
        # print(f"R: {right_file}")
        compared.append((left_file, right_file))
        return

    def mock_prompt():
        return "y"

    temp_path, bak_path, csv_path = temp_paths_2
    # print(temp_path)
    # print(bak_path)
    # print(csv_path)
    # print(csv_path.read_text())

    args = [
        "bak_to_git_2.py",
        str(csv_path),
        "--log-dir",
        str(temp_path),
    ]

    monkeypatch.setattr(bak_to_git_2, "run_compare", mock_compare)

    monkeypatch.setattr(bak_to_git_2, "ask_to_continue", mock_prompt)

    bak_to_git_2.main(args)

    # print(compared)

    #  New files have no previous instance so run_compare is not called.
    #  The run_compare function should have been called 2 times.
    assert 2 == len(compared)


@pytest.fixture(scope="module")
def temp_paths_3(tmp_path_factory):
    """
    Makes temporary directories, for testing bak_to_git_3, and populates them
    with test files. Returns pathlib.Path objects for each.
    """
    temp_path: Path = tmp_path_factory.mktemp("baktogit3")
    bak_path = temp_path / "_0_bak"
    bak_path.mkdir()

    t1 = "20211001_083010"
    p1 = bak_path / f"test.txt.{t1}.bak"
    p1.write_text("One\nTahoo\nTharee\n")

    t2 = "20211101_093011"
    p2 = bak_path / f"test.txt.{t2}.bak"
    p2.write_text("One\nTahoo\nThree\n")

    t3 = "20211201_103012"
    p3 = bak_path / f"test.txt.{t3}.bak"
    p3.write_text("One\nTwo\nThree\n")

    csv_path = temp_path / "step-1-files-changed.csv"
    csv_lines = []
    csv_lines.append(csv_header_row())
    csv_lines.append(
        csv_data_row(
            "1",
            f"{t1}:{bak_base_name(p1.name)}",
            str(p1),
            "",
            t1,
            bak_base_name(p1.name),
            "",
            "Initial commit.",
            "",
            "",
        )
    )
    csv_lines.append("2,,,,,,,,,")
    csv_lines.append(
        csv_data_row(
            "3",
            f"{t2}:{bak_base_name(p2.name)}",
            str(p2),
            str(p1),
            t2,
            bak_base_name(p2.name),
            "y",
            "",
            "",
            "Note: skipping.",
        )
    )
    csv_lines.append("4,,,,,,,,,")
    csv_lines.append(
        csv_data_row(
            "5",
            f"{t3}:{bak_base_name(p3.name)}",
            str(p3),
            str(p2),
            t3,
            bak_base_name(p3.name),
            "",
            "Corrected Mr. Owl's typos.",
            "",
            "",
        )
    )
    csv_lines.append("6,,,,,,,,,")

    csv_path.write_text("\n".join(csv_lines))

    return temp_path, bak_path, csv_path


def test_bak_to_git_3(temp_paths_3, monkeypatch):

    runs = []

    def mock_run_git(cmds, run_dir, git_env):
        runs.append(cmds)
        return

    def mock_prompt():
        return "y"

    temp_path, bak_path, csv_path = temp_paths_3
    # print(temp_path)
    # print(bak_path)
    # print(csv_path)
    # print(csv_path.read_text())

    repo_path = temp_path / "fake_git_repo"
    repo_path.mkdir()
    (repo_path / ".git").mkdir()

    args = [
        "bak_to_git_3.py",
        str(csv_path),
        str(repo_path),
        "--log-dir",
        str(temp_path),
    ]

    # "--filter-file", "./filter-list.txt"

    monkeypatch.setattr(bak_to_git_3, "run_git", mock_run_git)

    monkeypatch.setattr(bak_to_git_3, "ask_to_continue", mock_prompt)

    bak_to_git_3.main(args)

    #  Should be 1 add and 2 commits (1 skip).
    assert 3 == len(runs)


def test_bak_to_fossil_3(temp_paths_3, monkeypatch):

    runs = []

    def mock_run_fossil(cmds, run_dir):
        runs.append(cmds)
        return

    def mock_prompt():
        return "y"

    temp_path, bak_path, csv_path = temp_paths_3
    # print(temp_path)
    # print(bak_path)
    # print(csv_path)
    # print(csv_path.read_text())

    repo_path = temp_path / "fake_fossil_repo"
    repo_path.mkdir()
    fake_fossil = temp_path / "fake_fossil"
    fake_fossil.write_text("Not the fossil.")

    args = [
        "bak_to_fossil_3.py",
        str(csv_path),
        str(repo_path),
        "--repo-name",
        "test.fossil",
        "--init-date",
        "2021-10-01T08:30:00",
        "--fossil-exe",
        str(fake_fossil),
        "--log-dir",
        str(temp_path),
    ]

    # "--filter-file", "./filter-list.txt"

    monkeypatch.setattr(bak_to_fossil_3, "run_fossil", mock_run_fossil)

    monkeypatch.setattr(bak_to_fossil_3, "ask_to_continue", mock_prompt)

    bak_to_fossil_3.main(args)

    #  Should be 1 create-repo, 1 open-repo, 1 add, and 2 commits (1 skip).
    assert 5 == len(runs)
