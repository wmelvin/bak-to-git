import pytest

from datetime import datetime, timedelta

from btg2_stats import ProgressStats


def fake_stats_log_lines():
    fmt = "%Y-%m-%d %H:%M:%S"
    lines = []
    dt = datetime(2021, 12, 11, 10, 00, 00)

    #  First session.
    lines.append(f"S,{dt.strftime(fmt)},input.csv,")
    dt = dt + timedelta(seconds=10)
    lines.append(f"A,{dt.strftime(fmt)},,skip")
    dt = dt + timedelta(seconds=10)
    lines.append(
        f"A,{dt.strftime(fmt)},,commit",
    )
    dt = dt + timedelta(seconds=10)
    lines.append(
        f"A,{dt.strftime(fmt)},,skip",
    )
    dt = dt + timedelta(seconds=10)
    lines.append(
        f"A,{dt.strftime(fmt)},,commit",
    )

    #  Second session.
    dt = dt + timedelta(seconds=300)
    lines.append(
        f"S,{dt.strftime(fmt)},input.csv,",
    )
    dt = dt + timedelta(seconds=10)
    lines.append(
        f"A,{dt.strftime(fmt)},,skip",
    )
    dt = dt + timedelta(seconds=20)
    lines.append(
        f"A,{dt.strftime(fmt)},,commit",
    )
    dt = dt + timedelta(seconds=10)
    lines.append(
        f"A,{dt.strftime(fmt)},,skip",
    )
    dt = dt + timedelta(seconds=20)
    lines.append(
        f"A,{dt.strftime(fmt)},,commit",
    )

    #  Third session.
    dt = dt + timedelta(seconds=300)
    lines.append(
        f"S,{dt.strftime(fmt)},input.csv,",
    )
    dt = dt + timedelta(seconds=10)
    lines.append(
        f"A,{dt.strftime(fmt)},,skip",
    )
    dt = dt + timedelta(seconds=360)  # Outlier.
    lines.append(
        f"A,{dt.strftime(fmt)},,commit",
    )
    dt = dt + timedelta(seconds=10)
    lines.append(
        f"A,{dt.strftime(fmt)},,skip",
    )
    dt = dt + timedelta(seconds=10)
    lines.append(
        f"A,{dt.strftime(fmt)},,commit",
    )

    return lines


def test_progress_stats_run(tmp_path):
    stats_path = tmp_path / "test_stats.csv"
    print(str(stats_path))
    ps = ProgressStats(stats_path, save_immediate=False, is_reporting=False)
    assert ps.file_name == str(stats_path)

    source_file_name = "csv_path_goes_here.csv"
    ps.start_session(source_file_name)
    assert any(x.source_file == source_file_name for x in ps.items)

    log_lines = fake_stats_log_lines()

    #  Should not get any items if is_reporting is False.
    prev_count = len(ps.items)
    ps.get_items(log_lines)
    assert prev_count == len(ps.items)

    #  Should only count rows when is_reporting is True.
    for x in range(5):
        ps.count_row()
    assert ps._row_count == 0


def test_progress_stats_reporting(tmp_path):
    stats_path = tmp_path / "fake_stats.csv"
    print(str(stats_path))
    log_lines = fake_stats_log_lines()
    stats_path.write_text("\n".join(log_lines))

    ps = ProgressStats(stats_path, save_immediate=False, is_reporting=True)
    assert ps.file_name == str(stats_path)

    #  Should get items if is_reporting is True.
    assert 0 == len(ps.items)
    # ps.get_items(log_lines)
    ps.load()
    assert len(log_lines) == len(ps.items)

    count, avg, med = ps.get_stats()
    assert count == 12
    assert avg is not None
    assert avg == 11
    assert med is not None

    #  Should only count rows when is_reporting is True.
    for x in range(5):
        ps.count_row()
    assert ps._row_count == 5


def test_progress_stats_logging(tmp_path, monkeypatch):
    dt_list = [
        datetime(2021, 12, 11, 10, 0, 0),
        datetime(2021, 12, 11, 10, 0, 10),
        datetime(2021, 12, 11, 10, 0, 40),
    ]
    dt_list.reverse()

    def mock_now():
        assert 0 < len(dt_list)
        return dt_list.pop()

    stats_path = tmp_path / "test_progress_stats_logging.csv"
    print(str(stats_path))
    ps1 = ProgressStats(stats_path, save_immediate=False, is_reporting=False)
    monkeypatch.setattr(ps1, "_now", mock_now)
    assert ps1.file_name == str(stats_path)
    ps1.start_session("not_real_input.csv")
    ps1.log_act("skip")
    ps1.log_act("commit")
    ps1.save()
    assert stats_path.exists()

    ps2 = ProgressStats(stats_path, save_immediate=False, is_reporting=True)
    assert ps2.file_name == str(stats_path)
    ps2.load()
    assert 3 == len(ps2.items)


def test_progress_stats_parent(tmp_path):
    stats_path = tmp_path / "NadaDir" / "test_progress_stats_parent.csv"
    print(str(stats_path))
    with pytest.raises(FileNotFoundError) as e:
        ProgressStats(stats_path, save_immediate=False, is_reporting=False)
    assert "NadaDir" in str(e)
