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
import shutil
import mutagen
from pathvalidate import sanitize_filename

def valid_date(date):
    try:
        datetime.date.fromisoformat(date)
        return date
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a valid date: {date}")

def get_title(file_path):
    return mutagen.File(file_path)['title'][0]

def set_meta(file_path, title, artist, album, genre):
    mtime = os.path.getmtime(file_path)
    atime = os.path.getatime(file_path)
    audio = mutagen.File(file_path)
    audio['title'] = title
    audio['artist'] = artist
    audio['album'] = album
    audio['genre'] = genre
    audio.save()
    os.utime(file_path, (atime, mtime))

parser = argparse.ArgumentParser()
parser.add_argument('source')
parser.add_argument('target')
group = parser.add_mutually_exclusive_group()
group.add_argument(
    '--copy',
    action='store_true',
    help='copy tracks from source to target'
)
group.add_argument(
    '--move',
    action='store_true',
    help='move tracks from source to target'
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
parser.add_argument(
    '--ignore-title',
    nargs='*',
    help='track title(s) to ignore'
)
parser.add_argument(
    '--album',
    required=True,
    help='album to be written into the track file'
)
parser.add_argument(
    '--genre',
    required=True,
    help='genre to be written into the track file'
)
args = parser.parse_args()

source = args.source
target = args.target

source_list = dict()
target_list = dict()

for file_name in os.listdir(source):
    file_path = os.path.join(source, file_name)
    if os.path.isfile(file_path):
        mtime = os.path.getmtime(file_path)
        date = time.strftime('%Y-%m-%d', time.localtime(mtime))
        if ((not args.min_date or date >= args.min_date)
                and (not args.max_date or date <= args.max_date)):
            artist_and_title = get_title(file_path)
            split = artist_and_title.split(' - ', 1)
            title = split[1]
            artist = split[0]
            if title and artist and (not args.ignore_title or artist_and_title not in args.ignore_title):
                if artist_and_title not in source_list:
                    source_list[artist_and_title] = list()
                bisect.insort(source_list[artist_and_title], {
                    "file_path": file_path,
                    "mtime": mtime,
                    "date": date,
                    "title": title,
                    "artist": artist,
                }, key=lambda x: x["mtime"])
            else:
                print(f'ignoring {file_name}')

if args.copy:
    for artist_and_title, tracks in source_list.items():
        track = tracks[-1]
        file_name = sanitize_filename(f'{artist_and_title}.ogg')
        target_file_path = os.path.join(target, file_name)
        print(f'copying {file_name}')
        shutil.copy2(track['file_path'], target_file_path)
        set_meta(target_file_path, track['title'], track['artist'], args.album, args.genre)

elif args.move:
    print('not implemented yet')
else:
    dates = set()
    tracks_per_date = dict()
    total_tracks = 0

    for artist_and_title, tracks in source_list.items():
        date = tracks[-1]['date']
        dates.add(date)
        if date not in tracks_per_date:
            tracks_per_date[date] = 1
        else:
            tracks_per_date[date] += 1
        total_tracks +=1
        print(f'[{', '.join(list(map(lambda x: x['date'], tracks)))}] {artist_and_title}')

    print(f'Tracks per date:\n{'\n'.join(list(map(lambda x: f'{x} ({tracks_per_date[x]})', sorted(dates))))}')
    print(f'Total tracks: {total_tracks}')