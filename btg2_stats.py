import statistics

from collections import namedtuple
from datetime import datetime, timedelta
from pathlib import Path
from typing import List


ProgressItem = namedtuple("ProgressItem", "type, time, source_file, act")


class ProgressStats:
    def __init__(
        self, stats_file: str, save_immediate: bool, is_reporting: bool
    ):
        if stats_file is None:
            self.file_name = ""
        else:
            self.file_name = str(stats_file)

        self.do_log = (0 < len(self.file_name)) and (not is_reporting)
        self.do_report = (0 < len(self.file_name)) and is_reporting
        assert not (self.do_log and self.do_report)

        p = Path(self.file_name).parent
        if not p.exists():
            raise FileNotFoundError(f"Cannot find directory '{p}'")

        self.save_immediate = save_immediate
        self.source_file = None
        self.items: List[ProgressItem] = []
        self.messages = []
        self._row_count = 0
        self._commit_count = 0
        self._skip_count = 0

        self._dt_format = "%Y-%m-%d %H:%M:%S"

    def count_row(self):
        if self.do_report:
            self._row_count += 1

    def count_commit(self):
        if self.do_report:
            self._commit_count += 1

    def count_skip(self):
        if self.do_report:
            self._skip_count += 1

    def _now(self):
        return datetime.now()

    def start_session(self, csv_path):
        if self.do_log:
            self.source_file = str(csv_path)
            self.items.append(
                ProgressItem("S", self._now(), self.source_file, "start")
            )
            if self.save_immediate:
                self.save()

    def stop_session(self):
        if self.do_log:
            self.items.append(ProgressItem("S", self._now(), "", "stop"))
            if self.save_immediate:
                self.save()

    def log_act(self, act: str):
        if self.do_log:
            self.items.append(ProgressItem("A", self._now(), "", act))
            if self.save_immediate:
                self.save()

    def save(self):
        if self.do_log and (0 < len(self.items)):
            do_header = not Path(self.file_name).exists()
            with open(self.file_name, "a") as f:
                if do_header:
                    f.write("TYPE,TIME,SOURCE,ACT\n")
                for item in self.items:
                    f.write(
                        '"{}","{}","{}","{}"\n'.format(
                            item.type,
                            item.time.strftime(self._dt_format),
                            item.source_file,
                            item.act,
                        )
                    )
            self.items.clear()

    def get_items(self, log_lines):
        if self.do_report:
            for num, line in enumerate(log_lines, start=1):
                a = [x.strip('"') for x in line.split(",")]
                if len(a) == 4:
                    if a[0] in ["S", "A"]:
                        self.items.append(
                            ProgressItem(
                                a[0],
                                datetime.strptime(a[1], self._dt_format),
                                a[2],
                                a[3],
                            )
                        )
                else:
                    self.messages.append(
                        f"ERROR: Invalid format in row {num}."
                    )

    def load(self):
        if self.do_report:
            with open(self.file_name) as f:
                self.get_items(f.readlines())

    def get_stats(self):
        """
        Returns (count, mean, median) of durations in seconds.
        """

        #  If more than 5 minutes then there was probably a break or a
        #  distraction in the manual process.
        max_secs = 5 * 60

        durs = []
        last_time = None
        for item in self.items:
            if item.type == "S":
                last_time = item.time
            elif item.type == "A":
                if last_time is not None:
                    durs.append(int((item.time - last_time).total_seconds()))
                last_time = item.time

        if 0 == len(durs):
            return (None, None, None)
        else:
            durs2 = [x for x in durs if x < max_secs]
            n_outliers = len(durs) - len(durs2)
            if 0 < n_outliers:
                self.messages.append(
                    f"NOTE: Outliers removed from mean = {n_outliers}."
                )
            med = statistics.median_high(durs)
            avg = statistics.mean(durs2)
            return (len(durs), int(avg), int(med))

    def report(self):
        if self.do_report:
            rpt = []
            done = self._commit_count + self._skip_count
            todo = self._row_count - done
            if 0 < self._row_count and 0 < done:
                pct_done = f"{(done / self._row_count):0.0%}"
            else:
                pct_done = "(?)"

            rpt.append("")
            rpt.append("{:>43}".format("PROGRESS REPORT"))
            rpt.append("{:>42}: {}".format("Total", self._row_count))
            rpt.append(
                "{:>42}: {}".format(
                    "Completed",
                    "{0}  (Commit: {1}, Skip: {2})".format(
                        done, self._commit_count, self._skip_count
                    ),
                )
            )
            rpt.append("{:>42}: {}".format("Remaining", todo))
            rpt.append("{:>42}: {}".format("% Complete", pct_done))
            rpt.append("")

            count, avg, med = self.get_stats()

            if (count is not None) and (0 < todo):
                rpt.append("{:>42}: {}".format("Number of data points", count))
                rpt.append("{:>42}: {}".format("Mean seconds per item", avg))
                est_time = timedelta(seconds=(avg * todo))
                rpt.append(
                    "{:>42}: {}".format(
                        "Estimated time remaining based on mean", str(est_time)
                    )
                )
                rpt.append("{:>42}: {}".format("Median seconds per item", med))
                est_time = timedelta(seconds=(med * todo))
                rpt.append(
                    "{:>42}: {}".format(
                        "Estimated time remaining based on median",
                        str(est_time),
                    )
                )
                rpt.append("")

            if 0 < len(self.messages):
                rpt.append("Messages:")
                for msg in self.messages:
                    rpt.append(msg)
                rpt.append("")

            return "\n".join(rpt)
