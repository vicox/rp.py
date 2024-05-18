#!/usr/bin/python3

import os
import time
import datetime
import argparse

def valid_date(date):
    try:
        datetime.date.fromisoformat(date)
        return date
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a valid date: {date}")

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
parser.add_argument(
    '-d',
    '--date',
    type=valid_date,
    help='specify the date with YYYY-MM-DD'
)
args = parser.parse_args()

source = args.source
    
def get_date(filename):
    path = os.path.join(source, filename)
    mtime = os.path.getmtime(path)
    return time.strftime('%Y-%m-%d', time.localtime(mtime))

if args.list_tracks:
    total_tracks = 0

    for filename in os.listdir(source):
        if not args.date or get_date(filename) == args.date:
            total_tracks +=1
            print(filename)

    if not args.date:
        print(f'Total tracks: {total_tracks}')
    else:
        print(f'Total tracks ({args.date}): {total_tracks}')
elif args.list_dates:
    dates = set()
    tracks_per_date = dict()

    for filename in os.listdir(source):
        date = get_date(filename)
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