"""Compute the duration of media files

\b
This caches the duration of media files in a cache directory, so that
subsequent runs are faster. If media files are modified, the cache is recomputed

MEDIA is a list of media files to compute the duration of
"""

import sys
import operator
from typing import Optional, Sequence, Literal
from pathlib import Path

import click

from . import MediaFile, display_duration, set_debug


@click.command(context_settings={"max_content_width": 120}, help=__doc__)
@click.option(
    "--cache-dir",
    type=click.Path(path_type=Path, dir_okay=True),
    default=Path("~/.cache/mlength"),
    show_default=True,
    help="Cache directory",
)
@click.option(
    "--lib",
    type=click.Choice(["mediainfo", "ffprobe"]),
    envvar="MLENGTH_LIB",
    default="ffprobe",
    show_default=True,
    show_envvar=True,
    help="Library to use for parsing media files",
)
@click.option(
    "--cache/--no-cache",
    default=True,
    show_default=True,
    help="Enable/disable caching",
)
@click.option(
    "-o",
    "--operation",
    type=click.Choice(["sum", "max", "min", "avg"]),
    default=None,
    help="Operation to perform on the durations",
)
@click.option(
    "-d",
    "--display",
    type=click.Choice(["ms", "s", "m", "human", "path", "all"]),
    default="human",
    help="Display format for durations",
)
@click.option("--debug", "_debug", is_flag=True, help="Enable debug mode")
@click.argument(
    "MEDIA",
    type=click.Path(exists=True, path_type=Path, allow_dash=True),
    nargs=-1,
    required=True,
)
def main(
    media: Sequence[Path],
    operation: Optional[Literal["sum", "max", "min", "avg"]],
    cache_dir: Path,
    lib: Literal["mediainfo", "ffprobe"],
    display: Literal["ms", "s", "m", "human", "path", "all"],
    _debug: bool,
    cache: bool,
) -> None:
    cache_dir = Path(cache_dir).expanduser().absolute()
    cache_dir.mkdir(parents=True, exist_ok=True)
    if len(media) == 1 and str(media[0]) == "-":
        media = [Path(f) for f in sys.stdin.read().splitlines()]
        for m in media:
            if not m.exists():
                # raise click exception
                raise click.BadParameter(f"File {m} from STDIN does not exist")
    if len(media) == 0:
        click.echo("No media files specified", err=True)
        return
    if _debug:
        set_debug(True)
    media_files = [MediaFile(m, cache_dir) for m in media]
    durations_gen = (
        mf.cached_duration(lib) if cache else mf.parse_duration(lib)
        for mf in media_files
    )
    if operation is None:
        for i, d in enumerate(durations_gen):
            if display == "path":
                click.echo(media[i])
            else:
                click.echo(display_duration(d, display=display, path=media[i]))
        return

    durations = list(durations_gen)

    if operation == "sum":
        if display in ["path", "all"]:
            click.echo("Cannot display path for sum/all", err=True)
            raise SystemExit(1)
        click.echo(display_duration(sum(durations), display=display, path=None))
    elif operation == "avg":
        average = sum(durations) / len(media_files)
        if display_duration in ["path", "all"]:
            click.echo("Cannot display path/all for average", err=True)
            raise SystemExit(1)
        click.echo(display_duration(average, display=display, path=None))
    elif operation == "max":
        max_index = max(enumerate(durations), key=operator.itemgetter(1))[0]
        click.echo(
            display_duration(
                durations[max_index], display=display, path=media[max_index]
            )
        )
    elif operation == "min":
        min_index = min(enumerate(durations), key=operator.itemgetter(1))[0]
        click.echo(
            display_duration(
                durations[min_index], display=display, path=media[min_index]
            )
        )
    else:
        raise ValueError(f"Invalid operation {operation}")


if __name__ == "__main__":
    main(prog_name="mlength")
