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

def split_artist_and_title(artist_and_title):
    title = None
    artist = None
    if ' - ' in artist_and_title:
        artist, title = artist_and_title.split(' - ', 1)
    return title, artist

def get_meta(file_path):
    audio = mutagen.File(file_path)
    return {
        "title": audio['title'][0] if 'title' in audio else None,
        "artist": audio['artist'][0] if 'artist' in audio else None,
        "album": audio['album'][0] if 'album' in audio else None,
        "genre": audio['genre'][0] if 'genre' in audio else None,
    }

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
            artist_and_title = get_meta(file_path)['title']
            title, artist = split_artist_and_title(artist_and_title)
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

for file_name in os.listdir(target):
    file_path = os.path.join(target, file_name)
    if os.path.isfile(file_path):
        mtime = os.path.getmtime(file_path)
        date = time.strftime('%Y-%m-%d', time.localtime(mtime))
        title = get_meta(file_path)['title']
        artist = get_meta(file_path)['artist']
        target_list[f'{artist} - {title}'] = {
            "file_path": file_path,
            "mtime": mtime,
            "date": date,
            "title": title,
            "artist": artist,
        }

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
    unique_tracks = 0
    existing_tracks = 0
    new_tracks = 0

    for artist_and_title, tracks in source_list.items():
        for track in tracks:
            date = track['date']
            dates.add(date)
            if date not in tracks_per_date:
                tracks_per_date[date] = {
                    "total": 0,
                    "unique": 0,
                    "existing": 0,
                    "new": 0
                }
            tracks_per_date[date]['total'] += 1
            if track == tracks[-1]:
                tracks_per_date[date]['unique'] += 1
                if (artist_and_title in target_list):
                    tracks_per_date[date]['existing'] += 1
                else:
                    tracks_per_date[date]['new'] += 1
        
        total_tracks += len(tracks)
        unique_tracks += 1

        if (artist_and_title in target_list):
            existing_tracks += 1
        else:
            new_tracks += 1

        track_status = ('new', 'existing')[artist_and_title in target_list]
        track_dates = list(map(lambda x: x['date'], tracks))
        print(f'[{track_status}] {artist_and_title} ({', '.join(track_dates)})')

    print(f'Tracks per date:\n{'\n'.join(list(map(lambda x: f'{x}: {f'{tracks_per_date[x]['total']} total, {tracks_per_date[x]['unique']} unique, {tracks_per_date[x]['existing']} existing, {tracks_per_date[x]['new']} new'}', sorted(dates))))}')
    print(f'Total tracks: {total_tracks}')
    print(f'Unique tracks: {unique_tracks}')
    print(f'Existing tracks: {existing_tracks}')
    print(f'New tracks: {new_tracks}')