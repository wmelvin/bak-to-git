#!/usr/bin/env python3

import csv
import sys

from collections import namedtuple
from pathlib import Path


SourceProps = namedtuple("SourceProps", "sort_key, skip, msg, cmd, notes")


def main(argv):
    if len(argv) == 3:
        source_name = argv[1]
        target_name = argv[2]
    else:
        sys.stderr.write(
            "\nUSAGE: csv_import_prior_work.py  source-file-name  "
            + "target-file-name\n\n"
        )
        sys.exit(2)

    source_csv = Path(source_name).resolve()
    assert source_csv.exists()

    target_csv = Path(target_name).resolve()
    assert target_csv.exists()

    output_csv = (
        target_csv.parent / f"{target_csv.stem}-with-prior-imported.csv"
    )
    assert not output_csv.exists()  # Do not overwrite.

    print(f"Reading '{source_csv}'")
    source_props = {}
    with open(source_csv) as fs:
        reader = csv.DictReader(fs)
        for row in reader:
            if len(row["sort_key"]) > 0:
                # print(row["sort_key"])

                #  The ADD_COMMAND column was not in CSV files created
                #  before 2021-11-08.
                if "ADD_COMMAND" in row.keys():
                    cmd = row["ADD_COMMAND"]
                else:
                    cmd = ""

                #  The NOTES column was not in CSV files created
                #  before 2021-11-09.
                if "NOTES" in row.keys():
                    notes = row["NOTES"]
                else:
                    notes = ""

                props = SourceProps(
                    row["sort_key"],
                    row["SKIP_Y"],
                    row["COMMIT_MESSAGE"],
                    cmd,
                    notes,
                )

                #  Assert sort_key is unique.
                assert props.sort_key not in source_props.keys()

                source_props[props.sort_key] = props

    # for k in source_props.keys():
    #     print(source_props[k])

    print(f"Reading '{target_csv}'")
    with open(target_csv) as ft:
        reader = csv.DictReader(ft)
        flds = reader.fieldnames

        print(f"Writing '{output_csv}'")
        with open(output_csv, "w") as fo:
            writer = csv.DictWriter(fo, fieldnames=flds)
            writer.writeheader()
            for row in reader:
                out_row = row
                row_key = out_row["sort_key"]
                if row_key in source_props.keys():

                    #  Assert not replacing existing data.
                    assert 0 == len(out_row["COMMIT_MESSAGE"])
                    assert 0 == len(out_row["ADD_COMMAND"])

                    assert (
                        (0 == len(out_row["SKIP_Y"]))
                        and (0 == len(out_row["NOTES"]))
                    ) or (
                        (out_row["SKIP_Y"] == "Y")
                        and (
                            out_row["NOTES"]
                            == "SKIP_Y set per --skip-names option."
                        )
                    )

                    prop: SourceProps = source_props[row_key]
                    out_row["SKIP_Y"] = prop.skip
                    out_row["COMMIT_MESSAGE"] = prop.msg
                    out_row["ADD_COMMAND"] = prop.cmd
                    out_row["NOTES"] = prop.notes

                writer.writerow(out_row)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
