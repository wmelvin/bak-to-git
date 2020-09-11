#!/usr/bin/env python3

#----------------------------------------------------------------------
# bak-to-git-1.py
#
# 
#
# 2020-09-11
#----------------------------------------------------------------------

from pathlib import Path
from collections import namedtuple
import csv


#baks_dir = '~/Desktop/wemDesk/20200817_BackupRotation/_0_bak/_older/20200831'
baks_dir = '~/Desktop/wemDesk/20200817_BackupRotation/_0_bak/'

repo_dir = '~/Desktop/test/bakrot_repo'


BakProps = namedtuple('BakProps', 'sort_key, full_name, file_name, base_name, datetime_tag')


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
    sort_key = f"{datetime_tag}:{base_name}"

    file_list.append(BakProps(sort_key, full_name, file_name, base_name, datetime_tag))

    if not base_name in base_names:
        base_names.append(base_name)

    if not datetime_tag in datetime_tags:
        datetime_tags.append(datetime_tag)

file_list.sort()
base_names.sort()
datetime_tags.sort()


with open ('out-1-files-all.csv', 'w', newline='') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(['sort_key','full_name','file_name','base_name','datetime_tag'])
    writer.writerows(file_list)


with open ('out-1-base_names.csv', 'w', newline='') as out_file:
    out_file.write(f"base_name\n")
    for a in base_names:
        out_file.write(f"{a}\n")


with open ('out-1-datetime_tags.csv', 'w', newline='') as out_file:
    out_file.write(f"datetime_tag\n")
    for a in datetime_tags:
        out_file.write(f"{a}\n")


ChangeProps = namedtuple(
    'ChangeProps', 
    'sort_key, datetime_tag, base_name, full_name, prev_full_name, repo_full_name'
)

changed_list = []
prev_files = {}

for dt in datetime_tags:
    #print (dt)

    dt_files = [p for p in file_list if p.datetime_tag == dt]
    for t in dt_files:
        #print(f"  {t.full_name}")
        repo_full_name = Path(repo_dir).resolve().joinpath(t.base_name)
        if t.base_name in prev_files:
            prev_props = prev_files[t.base_name]
            prev_content = Path(prev_props.full_name).read_text()
            this_content = Path(t.full_name).read_text()
            if prev_content != this_content:
                # file changed
                changed_list.append(
                    ChangeProps(
                        t.sort_key, 
                        t.datetime_tag, 
                        t.base_name, 
                        t.full_name, 
                        prev_props.full_name, 
                        repo_full_name
                    )
                )
                prev_files[t.base_name] = t
        else:
            # new file
            changed_list.append(
                ChangeProps(
                    t.sort_key, 
                    t.datetime_tag, 
                    t.base_name, 
                    t.full_name, 
                    ''
                    , repo_full_name
                )
            )
            prev_files[t.base_name] = t
        

with open ('out-1-files-changed.csv', 'w', newline='') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(['sort_key','datetime_tag','base_name','full_name','prev_full_name','repo_full_name'])
    writer.writerows(changed_list)


print('Done.')



#----------------------------------------------------------------------

# for dt in datetime_tags:
#     print (dt)
#     dt_list = [p for p in changed_list if p.datetime_tag == dt]
#     for t in dt_list:
#         print(f"  {Path(t.prev_full_name).name} -> {Path(t.full_name).name}")


# for dt in datetime_tags:
#     print (dt)
#     dt_files = []
#     for p in changed_list:
#         if p[1].datetime_tag == dt:
#             dt_files.append(p[1])

#     for t in dt_files:
#         print(f"  {t.full_name}")



# for bn in base_names:
#     print(bn)
#     for t in [p for p in file_list if p.base_name == bn]:
#         print(f"  {t.full_name}")



#----------------------------------------------------------------------

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

