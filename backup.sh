#!/bin/bash

EXPORT=false
SOURCE_DATASET=""
BACKUP_DATASET=""

while getopts 'ed:' flag; do
  case "${flag}" in
    e) EXPORT=true ;;
    d) SOURCE_DATASET=$OPTARG;;
    *) error "Unexpected option ${flag}" ;;
  esac
done

if [ -z "$SOURCE_DATASET" ]
then
	echo "no dataset defined."
	echo "Usage: backup -d name_of_dataset"
	exit
fi

zpool import -a

echo
echo "available zpools:"
echo

zpool list
echo

BACKUP_DATASET=`zpool list | grep 'backup' | cut -f1 -d' '`

if [ -z "$BACKUP_DATASET" ]
then
	echo "backup zpool not found --> EXIT"
	exit
else
	echo "found backup zpool with the name: $BACKUP_DATASET"
fi

LAST_SNAPSHOT=`zfs list -t snapshot -o name -s creation | grep ^$BACKUP_DATASET/$SOURCE_DATASET | tail -n 1 | cut -f2 -d'@'`

echo "the last snapshot on the backup device: $LAST_SNAPSHOT"

if (zfs list -t snapshot -o name -s creation | grep -q "zeefes/$SOURCE_DATASET@$LAST_SNAPSHOT")
then
	LAST_LIVE_SNAPSHOT=`zfs list -t snapshot -o name -s creation | grep ^zeefes/$SOURCE_DATASET | tail -n 1 | cut -f2 -d'@'`
	echo "the last snapshot on the live device: $LAST_LIVE_SNAPSHOT"
	if [ "$LAST_LIVE_SNAPSHOT" == "$LAST_SNAPSHOT" ]; then
		echo "backup is up to date, no need to send stream"
	else
		echo "new snapshot is found, sending incremental backup"
		zfs send -vi $LAST_SNAPSHOT `zfs list -t snapshot -o name -s creation | grep ^zeefes/$SOURCE_DATASET | tail -n 1` | zfs receive -F $BACKUP_DATASET/$SOURCE_DATASET
	fi
	

else
	echo "last snapshot not found, sending full stream"
	zfs destroy -v $BACKUP_DATASET/$SOURCE_DATASET@%
	zfs send -v `zfs list -t snapshot -o name -s creation | grep ^zeefes/$SOURCE_DATASET | tail -n 1` | zfs receive -F $BACKUP_DATASET/$SOURCE_DATASET
fi

if [ "$EXPORT" = true ]
then
	echo "exporting zpool: $BACKUP_DATASET"
	zpool export $BACKUP_DATASET
else
	echo "$BACKUP_DATASET not exported!"
fi
	
