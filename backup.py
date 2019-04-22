#! /usr/bin/env python3

import subprocess
import re

zpool_source = "zeefes"
backup_search_string = "backup"


def get_backup_zpool():
    lines = subprocess.run(["zpool", "list", "-H"], stdout=subprocess.PIPE).stdout.decode('utf-8')
    res = re.match(r'^(backup[^\t]*)', lines, re.I | re.M)
    if res:
        return res.group(1)
    else:
        return ""
    
def get_snapshot_list(pool, dataset):
    snapshots = []
    lines = subprocess.run(["zfs", "list", "-H", "-tsnapshot", "-oname" ,"-screation"], stdout=subprocess.PIPE).stdout.decode('utf-8')
    for line in lines.splitlines():
        res = re.match(r'^' + pool + r'/' + dataset + r'@(.+)', line)
        if res:
            snapshots.append(res.group(1))
    return snapshots

def delete_snapshots(pool, dset):
    print("Deleting previous snapshots.")
    subprocess.run(["zfs", "destroy", "-v", pool + "/" + dset +"@%"])
    

def do_full_backup(src, dst, dset, snap):
    print("Starting full backup.")
    subprocess.run(["zfs send -v " + src + "/" + dset + "@" + snap + " | zfs receive -F " + dst + "/" + dset], shell=True)

def do_incremental_backup(src, dst, dset, snapfrom, snapto):
    print("Starting incremental backup")
    common = f"{src}/{dset}@{snapfrom}"
    latest = f"{src}/{dset}@{snapto}"
    subprocess.run([f"zfs send -vi {common} {latest} | zfs receive -F {dst}/{dset}"], shell=True)

print("FreeNAS backup tool started.")

zpool_backup = get_backup_zpool()

if not zpool_backup:
    print("Backup zpool not found. Exiting.")
    exit() 

print(f"Found backup pool: {zpool_backup}")

datasets = ["private/Apa", "private/Adam", "private/Reka", "private/Mama", "fenykeptar"]

for dataset in datasets:

    snaps_src = get_snapshot_list(zpool_source, dataset)
    snaps_bak = get_snapshot_list(zpool_backup, dataset)

    if len(snaps_src) == 0:
        print("Could not find source dataset. Exiting.")
        continue

    if len(snaps_bak) == 0:
        print("Could not find backup dataset.")
        do_full_backup(zpool_source, zpool_backup, dataset, snaps_src[-1])
        continue

    if snaps_bak[-1] == snaps_src[-1]:
        print("The backup is up to date. Exiting.")
        continue

    can_inc = False
    for s in snaps_src:
        if s == snaps_bak[-1]:
            can_inc = True

    if can_inc:
        print("Found matching snapshots. Incremental backup is possible.")
        do_incremental_backup(zpool_source, zpool_backup, dataset, snaps_bak[-1], snaps_src[-1])
    else:
        print("Could not find matching snapshots.")
        
        
        
