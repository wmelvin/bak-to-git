
from pathlib import Path

#baks_dir = '~/Desktop/wemDesk/20200817_BackupRotation/_0_bak/'
baks_dir = '~/Desktop/wemDesk/20200817_BackupRotation/_0_bak/_older/20200831'

repo_dir = '~/Desktop/test/bakrot_repo'

bak_files = Path(baks_dir).rglob('*.bak')

date_time_tags = []

# The backup files, created by the wipbak.sh script, are named with
# a .date_time tag preceeding the .bak extension (suffix). For example, 
# 're-git-1.py.20200905_105914.bak'.

for f in bak_files:
    # Path.stem returns the name without the suffix. Split the stem on '.'
    # and get the last element to retrieve the date_time tag.
    #
    tag = f.stem.split('.')[-1:][0]
    if not tag in date_time_tags:
        date_time_tags.append(tag)

date_time_tags.sort()

for a in date_time_tags:
    print(f"--- file names containing '{a}' -->")
    fspec = f"*{a}*"
    dt_files = Path(baks_dir).rglob(fspec)
    for b in dt_files:
        print(str(b))

