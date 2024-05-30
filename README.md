<div align="center">
 <img src="logo.svg" height="300">
</div>

# rp.py

`rp.py` helps you build an offline music library from the web.

## Why?

In the age of streaming services, where you get access to all the music for a monthly fee, you might ask what's the point. But this is fun, and you'll learn about and discover new music in the process.

## How it works

`rp.py` expects a *source* directory with music tracks which come, for example, from a web radio and can have duplicates. Use your favorite tool to collect your music tracks. The second directory expected is the *target* directory, which is your music library that you can import in your favorite music app.

The goal is to regularly transfer incoming tracks with `rp.py` from the source directory into the target directory and extend your music library day by day. You can choose to copy or move them, and if existing tracks should always be replaced or kept.

Each time you run `rp.py` you will see a report of how many duplicates have been found, how many tracks already exist in your library and how many will be added.

## Installation

1. Install dependencies.

        sudo apt install python3-mutagen python3-pathvalidate python3-progressbar2

2. Clone this repository.

        git clone git@github.com:vicox/rp.py.git

3. Create an alias.

        alias rp.py=/your/path/to/rp.py/rp.py


## Usage

    rp.py source target -o {always,never} [-c | -m]

### source (required)

The path to the source directory, i.e. the incoming tracks.

### target (required)

The path to the target directory, i.e. your music library.

### -o --overwrite (required)

Strategy to overwrite existing files, always or never. 'always' will also prefer newer tracks, and 'never' will prefer older tracks in your source directory if there are duplicates.

### -c --copy | -m --move

Copy or move tracks from source to target. If none of both are provided, only the report is printed.

### -i --ignore

List of track titles to ignore.

### -a --album

Fixed album name to be written into the track file.

### -g --genre

Fixed genre to be written into the track file.

### --max-date

Ignore tracks after YYYY-MM-DD.

### --min-date

Ignore tracks before YYYY-MM-DD.

## Example output

    $ rp.py incoming library -o always -c
    Scanning: 100% (10 of 10) |###############| Elapsed Time: 0:00:00 Time:  0:00:00
    ====================
    Ignored tracks
    ====================
    No title (0)

    ====================
    Track status
    ====================
    [**new***] Maxim Novak - Your Love (2024-05-03)
    [**new***] Brylie Christopher Oxley - Anticipation (2024-05-04)
    [existing] Zapa - Beiramar (2024-05-03)
    [existing] K.I.R.K. - Don't Go (2024-05-04)
    [existing] Lisa Hammer - Otherworldly Waltz (2024-05-04)

    ====================
    Track summary by date
    ====================
    2024-05-03: 3 total, 2 unique, 1 existing, 1 new
    2024-05-04: 4 total, 3 unique, 2 existing, 1 new

    ====================
    Track summary
    ====================
    Total tracks: 7
    Unique tracks: 5
    Existing tracks: 3
    New tracks: 2
    Copying: 100% (5 of 5) |##################| Elapsed Time: 0:00:00 Time:  0:00:00

## Current limitations

* Incoming tracks are required to have the artist and title stored in the meta tag *title* in the format `{artist} - {title}`.
* Files are always stored in the target directory with `.ogg`, independent of the source file extensions.

---
<a href="https://www.freepik.com/free-vector/retro-music-tapes-set_9176300.htm#from_view=detail_alsolike">Image by pch.vector on Freepik</a>