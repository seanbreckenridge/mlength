# mlength

gets the length of media files and caches the result

## Installation

Requires `python3.8+`

To install with pip, run:

```
pip install git+https://github.com/seanbreckenridge/mlength
```

This requires either `ffprobe` (from `ffmpeg`) or [`mediainfo`](https://mediaarea.net/en/MediaInfo) to be installed.

## Usage

```
Usage: mlength [OPTIONS] MEDIA...

  Compute the duration of media files

  This caches the duration of media files in a cache directory, so that
  subsequent runs are faster. If media files are modified, the cache is recomputed

  MEDIA is a list of media files to compute the duration of

Options:
  --cache-dir PATH                Cache directory  [default: ~/.cache/mlength]
  --lib [mediainfo|ffprobe]       Library to use for parsing media files  [env
                                  var: MLENGTH_LIB; default: ffprobe]
  --cache / --no-cache            Enable/disable caching  [default: cache]
  -o, --operation [sum|max|min|avg]
                                  Operation to perform on the durations
  -d, --display [ms|s|m|human|path|all]
                                  Display format for durations
  --debug                         Enable debug mode
  --help                          Show this message and exit.
```

```bash
$ mlength sound.mpeg
00:00:02.95
$ mlength -d all sound.mpeg
2951|2.95|0.05|00:00:02.95|sound.mpeg
```

I use this in lots of small scripts:

Get the shortest media file in a directory, with the [list-movies](https://github.com/seanbreckenridge/seanb-utils/blob/main/shellscripts/list-movies) script:

- `list-music -X mlength -o sum` (find length of an album in current directory)
- `list-movies -X mlength -d path -o min` (find shortest movie in current directory)
- `list-movies -X mlength -d all | sort -n` (sort results by length)

If the media file is modified, the cache is recomputed.

### Tests

```bash
git clone 'https://github.com/seanbreckenridge/mlength'
cd ./mlength
pip install '.[testing]'
flake8 ./mlength
mypy ./mlength
```
