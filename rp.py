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

import sys
import os
import time
import datetime
import bisect
import argparse
import shutil
import mutagen
from pathvalidate import sanitize_filename
import progressbar2

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

def read_tags(file_path):
    audio = mutagen.File(file_path)
    return dict(map(lambda kv: (kv[0], kv[1][0]), audio.tags.items()))

def write_tags(file_path, tags):
    mtime = os.path.getmtime(file_path)
    atime = os.path.getatime(file_path)
    audio = mutagen.File(file_path)
    for key, value in tags.items():
        if value:
            audio[key] = value
    audio.save()
    os.utime(file_path, (atime, mtime))

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('source')
    parser.add_argument('target')
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-c',
        '--copy',
        action='store_true',
        help='copy tracks from source to target'
    )
    group.add_argument(
        '-m',
        '--move',
        action='store_true',
        help='move tracks from source to target'
    )
    parser.add_argument(
        '-o',
        '--overwrite',
        choices=['always', 'never'],
        required=True,
        help='strategy to overwrite existing files'
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
        '-i',
        '--ignore',
        nargs='*',
        help='track title(s) to ignore'
    )
    parser.add_argument(
        '-a',
        '--album',
        help='album name to be written into the track file'
    )
    parser.add_argument(
        '-g',
        '--genre',
        help='genre to be written into the track file'
    )
    return parser.parse_args()

def scan(source, target, min_date, max_date, ignore):
    source_tracks = {}
    target_tracks = {}

    no_title = 0
    ignored_titles = {}

    with progressbar2.ProgressBar(
        max_value=len(os.listdir(source)) + len(os.listdir(target)),
        prefix='Scanning: '
    ) as bar:
        i = 0
        for file_name in sorted(os.listdir(source)):
            file_path = os.path.join(source, file_name)
            if os.path.isfile(file_path):
                mtime = os.path.getmtime(file_path)
                date = time.strftime('%Y-%m-%d', time.localtime(mtime))
                if ((not min_date or date >= min_date) and (not max_date or date <= max_date)):
                    tags = read_tags(file_path)
                    artist_and_title = tags.get('title')
                    title, artist = split_artist_and_title(artist_and_title)
                    if title and artist and (
                        not ignore or artist_and_title not in ignore
                    ):
                        if artist_and_title not in source_tracks:
                            source_tracks[artist_and_title] = []
                        bisect.insort(source_tracks[artist_and_title], {
                            "file_path": file_path,
                            "mtime": mtime,
                            "date": date,
                            "title": title,
                            "artist": artist,
                        }, key=lambda x: x["mtime"])
                    else:
                        if not title or not artist:
                            no_title += 1
                        elif artist_and_title not in ignored_titles:
                            ignored_titles[artist_and_title] = 1
                        else:
                            ignored_titles[artist_and_title] += 1
            bar.update(i)
            i += 1

        for file_name in sorted(os.listdir(target)):
            file_path = os.path.join(target, file_name)
            if os.path.isfile(file_path):
                mtime = os.path.getmtime(file_path)
                date = time.strftime('%Y-%m-%d', time.localtime(mtime))
                tags = read_tags(file_path)
                title = tags.get('title')
                artist = tags.get('artist')
                if artist and title:
                    target_tracks[f'{artist} - {title}'] = {
                    "file_path": file_path,
                    "mtime": mtime,
                    "date": date,
                    "title": title,
                    "artist": artist,
                }
            bar.update(i)
            i += 1

    print('====================')
    print('Ignored tracks')
    print('====================')
    print(f'No title ({no_title})')
    print('\n'.join(list(map(lambda x: f'{x} ({ignored_titles[x]})', ignored_titles))))

    return source_tracks, target_tracks

def summarize(source_tracks, target_tracks, overwrite):
    summary = {
        "by_date": {},
        "total_tracks": 0,
        "unique_tracks": 0,
        "existing_tracks": 0,
        "new_tracks": 0
    }

    print('\n====================')
    print('Track status')
    print('====================')

    for artist_and_title, tracks in source_tracks.items():
        for track in tracks:
            date = track['date']
            if date not in summary['by_date']:
                summary['by_date'][date] = {
                    "total": 0,
                    "unique": 0,
                    "existing": 0,
                    "new": 0
                }
            summary['by_date'][date]['total'] += 1
            if track == tracks[(0, -1)[overwrite == 'always']]:
                summary['by_date'][date]['unique'] += 1
                if artist_and_title in target_tracks:
                    summary['by_date'][date]['existing'] += 1
                else:
                    summary['by_date'][date]['new'] += 1

        summary['total_tracks'] += len(tracks)
        summary['unique_tracks'] += 1

        if artist_and_title in target_tracks:
            summary['existing_tracks'] += 1
        else:
            summary['new_tracks'] += 1

        track_status = ('**new***', 'existing')[artist_and_title in target_tracks]
        track_dates = list(map(lambda x: x['date'], tracks))
        print(f'[{track_status}] {artist_and_title} ({', '.join(track_dates)})')

    print('\n====================')
    print('Track summary by date')
    print('====================')
    print('\n'.join(list(map(lambda x: f'{x}: {(
        f'{summary['by_date'][x]['total']} total'
        f', {summary['by_date'][x]['unique']} unique'
        f', {summary['by_date'][x]['existing']} existing'
        f', {summary['by_date'][x]['new']} new'
    )}', sorted(summary['by_date'].keys())))))

    print('\n====================')
    print('Track summary')
    print('====================')
    print(f'Total tracks: {summary['total_tracks']}')
    print(f'Unique tracks: {summary['unique_tracks']}')
    print(f'Existing tracks: {summary['existing_tracks']}')
    print(f'New tracks: {summary["new_tracks"]}', flush=True)

    return summary

def copy_or_move(
    source,
    target,
    source_tracks,
    target_tracks,
    summary,
    overwrite,
    copy,
    album,
    genre
):
    errors = {}

    with progressbar2.ProgressBar(
        max_value=(summary['new_tracks'], summary['unique_tracks'])[overwrite == 'always'],
        prefix=('Moving: ', 'Copying: ')[copy]
    ) as bar:
        i = 0
        for artist_and_title, tracks in source_tracks.items():
            if (overwrite == 'always' or not artist_and_title in target_tracks):
                track = tracks[(0, -1)[overwrite == 'always']]
                file_name = sanitize_filename(f'{artist_and_title}.ogg')
                target_file_path = os.path.join(target, file_name)
                source_file_path = (
                    track['file_path'],
                    os.path.join(source, f'Copy of {file_name}')
                )[copy]
                try:
                    if copy:
                        shutil.copy2(track['file_path'], source_file_path)
                    write_tags(source_file_path, {
                        'title': track['title'],
                        'artist': track['artist'],
                        'album': album,
                        'genre': genre
                    })
                    shutil.move(source_file_path, target_file_path)
                except Exception as error:
                    errors[artist_and_title] = error
                    if copy:
                        if os.path.isfile(source_file_path):
                            os.remove(source_file_path)
                bar.update(i)
                i += 1

    if len(errors) > 0:
        print('\n====================')
        print('Errors - track not copied or moved!')
        print('====================')
        for artist_and_title, error in errors.items():
            print(f'{artist_and_title} ({type(error).__name__}: {error})')

def main():
    args = parse_args()

    source_tracks, target_tracks = scan(
        args.source,
        args.target,
        args.min_date,
        args.max_date,
        args.ignore
    )

    summary = summarize(
        source_tracks,
        target_tracks,
        args.overwrite
    )

    if args.copy or args.move:
        copy_or_move(
            args.source,
            args.target,
            source_tracks,
            target_tracks,
            summary,
            args.overwrite,
            args.copy,
            args.album,
            args.genre
        )

if __name__ == '__main__':
    sys.exit(main())
