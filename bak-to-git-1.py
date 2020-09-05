
from pathlib import Path

#baks_dir = '~/Desktop/wemDesk/20200817_BackupRotation/_0_bak/'
baks_dir = '~/Desktop/wemDesk/20200817_BackupRotation/_0_bak/_older/20200831'

repo_dir = '~/Desktop/test/bakrot_repo'

# baks = Path(baks_dir)
# bak_files = baks.rglob('*.bak')

bak_files = Path(baks_dir).rglob('*.bak')

#date_time_tags = [f.stem.split('.')[-1:] for f in bak_files]

date_time_tags = []

for f in bak_files:
    tag = f.stem.split('.')[-1:]
    if not tag in date_time_tags:
        date_time_tags.append(tag)

#print(type(f.stem))

date_time_tags.sort()

for a in date_time_tags:
    print(a)