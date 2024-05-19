#!/usr/bin/python3
#
#    rp.py helps you build an offline music library from the web.
#    Copyright (C) 2024  Georg Schmidl <georg.schmidl@vicox.net>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import os
import time
import datetime
import bisect 
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
    '--max-date',
    type=valid_date,
    help='ignore tracks after YYYY-MM-DD'
)
parser.add_argument(
    '--min-date',
    type=valid_date,
    help='ignore tracks before YYYY-MM-DD'
)
args = parser.parse_args()

source = args.source
target = args.target

source_list = dict()
target_list = dict()

for file_name in os.listdir(source):
    file_path = os.path.join(source, file_name)
    if os.path.isfile(file_path):
        date = get_date(file_path)
        if ((not args.min_date or date >= args.min_date)
                and (not args.max_date or date <= args.max_date)):
            artist_and_title = get_title(file_path)
            if artist_and_title not in source_list:
                source_list[artist_and_title] = list()
            bisect.insort(source_list[artist_and_title], {
                "file_path": file_path,
                "date": get_date(file_path),
            }, key=lambda x: x["date"])

if args.list_tracks:
    total_tracks = 0

    for artist_and_title, tracks in source_list.items():
        date = tracks[0]['date']
        total_tracks +=1
        print(f'({date}) {artist_and_title}')

    print(f'Total tracks: {total_tracks}')
elif args.list_dates:
    dates = set()
    tracks_per_date = dict()

    for artist_and_title, tracks in source_list.items():
        date = tracks[0]['date']
        dates.add(date)
        if date not in tracks_per_date:
            tracks_per_date[date] = 1
        else:
            tracks_per_date[date] += 1

    for date in sorted(dates):
        print(f'{date} ({tracks_per_date[date]} tracks)')
    print(f'Total dates: {len(dates)}, total tracks: {sum(tracks_per_date.values())}')