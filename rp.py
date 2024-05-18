#!/usr/bin/python3

# Dependencies:
# - python3-mutagen

import os
import time
import datetime
import argparse
import mutagen

def valid_date(date):
    try:
        datetime.date.fromisoformat(date)
        return date
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a valid date: {date}")
    
def get_date(file_path):
    mtime = os.path.getmtime(file_path)
    return time.strftime('%Y-%m-%d', time.localtime(mtime))

def get_title(file_path):
    return mutagen.File(file_path)['title'][0]

parser = argparse.ArgumentParser()
parser.add_argument('source')
parser.add_argument('target')
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
parser.add_argument(
    '-d',
    '--date',
    type=valid_date,
    help='specify the date with YYYY-MM-DD'
)
args = parser.parse_args()

source = args.source
target = args.target

if args.list_tracks:
    total_tracks = 0

    for file_name in os.listdir(source):
        file_path = os.path.join(source, file_name)
        if os.path.isfile(file_path):
            if not args.date or get_date(file_path) == args.date:
                total_tracks +=1
                print(get_title(file_path))

    if not args.date:
        print(f'Total tracks: {total_tracks}')
    else:
        print(f'Total tracks ({args.date}): {total_tracks}')
elif args.list_dates:
    dates = set()
    tracks_per_date = dict()

    for file_name in os.listdir(source):
        file_path = os.path.join(source, file_name)
        if os.path.isfile(file_path):
            date = get_date(file_path)
            dates.add(date)
            if date not in tracks_per_date:
                tracks_per_date[date] = 1
            else:
                tracks_per_date[date] += 1

    if(args.date):
        dates = dates.intersection({args.date})

    for date in sorted(dates):
        print(f'{date} ({tracks_per_date[date]} tracks)')
    print(f'Total dates: {len(dates)}')