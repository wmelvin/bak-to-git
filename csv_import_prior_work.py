#!/usr/bin/env python3

import csv

from collections import namedtuple
from pathlib import Path


SourceProps = namedtuple("SourceProps", "sort_key, skip, msg, cmd")


#  This utility script has hard-coded paths.

source_csv = Path("./prepare/out-1-files-changed-EDIT.csv").resolve()
assert source_csv.exists()

target_csv = Path(
    "./output/project_bakrot/211108_080325/step-1-files-changed.csv"
).resolve()
assert target_csv.exists()

output_csv = target_csv.parent / f"{target_csv.stem}-with-prior-imported.csv"
assert not output_csv.exists()  # Do not overwrite.

source_props = []
with open(source_csv) as f:
    reader = csv.DictReader(f)
    for row in reader:
        if len(row["sort_key"]) > 0:
            # print(row["sort_key"])

            if "ADD_COMMAND" in row.keys():
                cmd = row["ADD_COMMAND"]
            else:
                cmd = ""

            props = SourceProps(
                row["sort_key"],
                row["SKIP_Y"],
                row["COMMIT_MESSAGE"],
                cmd,
            )
            source_props.append(props)

for prop in source_props:
    print(prop)

# NEXT: Read target, write output...
