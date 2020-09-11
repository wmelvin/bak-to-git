
from pathlib import Path
from collections import namedtuple
import csv


#baks_dir = '~/Desktop/wemDesk/20200817_BackupRotation/_0_bak/_older/20200831'
baks_dir = '~/Desktop/wemDesk/20200817_BackupRotation/_0_bak/'

repo_dir = '~/Desktop/test/bakrot_repo'


BakProps = namedtuple('BakProps', 'full_name, file_name, backup_basename, datetime_tag')


bak_files = Path(baks_dir).rglob('*.bak')

file_list = []
datetime_tags = []
base_names = []

#  The backup files, created by the wipbak.sh script, are named with
#  a .date_time tag preceeding the .bak extension (suffix). For example, 
#  're-git-1.py.20200905_105914.bak'.

for f in bak_files:
    #  Path.stem returns the name without the suffix. Split the stem on '.'
    #  and get the last element to retrieve the date_time tag.
    #
    full_name = str(f)
    file_name = f.name
    datetime_tag = f.stem.split('.')[-1:][0]
    base_name = '.'.join(f.name.split('.')[:-2])

    file_list.append(BakProps(full_name, file_name, base_name, datetime_tag))

    if not base_name in base_names:
        base_names.append(base_name)

    if not datetime_tag in datetime_tags:
        datetime_tags.append(datetime_tag)

base_names.sort()
datetime_tags.sort()

with open ('test-1-props.csv', 'w', newline='') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(['full_name','file_name','backup_basename','datetime_tag'])
    for props in file_list:
        writer.writerows(file_list)

with open ('test-2-base_names.csv', 'w', newline='') as out_file:
    out_file.write(f"backup_basename\n")
    for a in base_names:
        out_file.write(f"{a}\n")

with open ('test-3-datetime_tags.csv', 'w', newline='') as out_file:
    out_file.write(f"datetime_tag\n")
    for a in datetime_tags:
        out_file.write(f"{a}\n")



# baks_list = []

# for t in date_time_tags:
#     #print(f"--- file names containing '{a}' -->")
#     filespec = f"*{t}*"
#     dt_files = Path(baks_dir).rglob(filespec)
#     for bak_path in dt_files:
        
#         bak_basename = '.'.join(bak_path.name.split('.')[:-2])
#         # Example: Gets 're-git-1.py' from 're-git-1.py.20200905_105914.bak'.        

#         filename_in_repo = Path(repo_dir).resolve().joinpath(bak_basename)

#         baks_list.append((str(bak_path), str(filename_in_repo)))

# # for t in baks_list:
# #     print(t)

# with open ('test.csv', 'w', newline='') as csv_file:
#     writer = csv.writer(csv_file)
#     writer.writerow(['BackupFileName','RepoFileName'])
#     writer.writerows(baks_list)

