#!/usr/bin/python3

import os
import time
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('source')
group = parser.add_mutually_exclusive_group()
group.add_argument(
    '-lt',
    '--list-tracks',
    action='store_true',
    help='list all tracks'
)
group.add_argument(
    '-ld',
    '--list-dates',
    action='store_true',
    help='list all dates with number of tracks'
)
args = parser.parse_args()

source = args.source

if args.list_tracks:
    total_tracks = 0

    for filename in os.listdir(source):
        total_tracks +=1
        print(filename)

    print(f'Total tracks: {total_tracks}')
elif args.list_dates:
    dates = set()
    tracks_per_date = dict()

    for filename in os.listdir(source):
        source_file = os.path.join(source, filename)
        mtime = os.path.getmtime(source_file)
        date = time.strftime('%Y-%m-%d', time.localtime(mtime))
        dates.add(date)
        if date not in tracks_per_date:
            tracks_per_date[date] = 1
        else:
            tracks_per_date[date] += 1

    for date in sorted(dates):
        print(f'{date}: {tracks_per_date[date]} tracks')