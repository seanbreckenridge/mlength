from typing import Optional, Sequence, Literal, Union
from pathlib import Path

import click

Ms = Union[int, float]


_DEBUG = False


def set_debug(debug: bool) -> None:
    global _DEBUG
    _DEBUG = debug


def debug(message: str) -> None:
    if _DEBUG:
        click.echo(f"DEBUG: {message}", err=True)


class MediaFile:
    def __init__(
        self,
        path: Path,
        cache_dir: Path,
    ) -> None:
        self.path = path
        self.cache_file = cache_dir / Path(*self.path.absolute().parts[1:])

    __slots__ = ("path", "cache_file")

    def __repr__(self) -> str:
        return f"MediaFile({self.path})"

    def __str__(self) -> str:
        return str(self.path)

    def mediainfo_duration(self) -> Ms:
        from pymediainfo import MediaInfo  # type: ignore[import]

        debug(f"parsing {self.path}")
        tracks = MediaInfo.parse(self.path).tracks  # type: ignore[attr-defined]
        debug(f"tracks: {tracks}")
        if len(tracks) == 0:
            raise ValueError(f"Could not parse duration for {self.path}")
        duration: int
        for track in tracks:
            if track.duration is not None:
                duration = track.duration
                break
        else:
            raise ValueError(f"Could not parse duration for {self.path}")
        debug(f"parsed duration: {duration}")
        return duration

    def ffprobe_duration(self) -> Ms:
        import shlex
        import subprocess
        import shutil

        if not shutil.which("ffprobe"):
            raise ValueError(
                "ffprobe not found, cannot parse duration (this is installed as part of ffmpeg)"
            )

        cmd: Sequence[str] = [
            "ffprobe",
            "-i",
            str(self.path.absolute()),
            *shlex.split("-show_entries format=duration -v quiet -of csv='p=0'"),
        ]
        debug(f"running command: {cmd}")
        try:
            buf = subprocess.check_output(cmd)
        except subprocess.CalledProcessError as e:
            debug(f"could not parse duration for {self.path}, received {e}")
            raise ValueError(f"Could not parse duration for {self.path}") from e
        output = buf.decode().strip()
        if output == "" or output == "N/A":
            debug(f"could not parse duration for {self.path}, received {output}")
            raise ValueError(f"Could not parse duration for {self.path}")
        duration = int(float(output) * 1000)
        debug(f"parsed duration: {duration}")
        return duration

    def parse_duration(self, lib: Literal["mediainfo", "ffprobe"]) -> Ms:
        if lib == "mediainfo":
            try:
                duration = self.mediainfo_duration()
            except ValueError:
                # fall back to ffprobe
                duration = self.ffprobe_duration()
        else:
            duration = self.ffprobe_duration()
        return duration

    def read_cached_duration(self) -> Ms:
        # assumes the cache file exists
        try:
            cached_dur = int(self.cache_file.read_text())
        except ValueError:
            raise ValueError(f"Could not parse duration for {self.path}")
        debug(f"cached duration: {cached_dur}")
        return cached_dur

    def write_cached_duration(self, duration: Ms) -> None:
        if not self.cache_file.parent.exists():
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        debug(f"writing duration {duration} to {self.cache_file}")
        self.cache_file.write_text(str(duration))

    def cached_duration(self, lib: Literal["mediainfo", "ffprobe"]) -> Ms:
        cf = self.cache_file
        if not cf.exists():
            debug(f"cache file {cf} does not exist")
            # write to cache file
            duration = self.parse_duration(lib)
            self.write_cached_duration(duration)
            return duration

        cf_st = cf.stat()
        media_st = self.path.stat()
        # if the cache file is older than the media file, then it's stale, recompute
        if cf_st.st_mtime < media_st.st_mtime:
            debug(f"cache file {cf} is older than media file {self.path}, recomputing")
            cf.unlink()
            return self.cached_duration(lib)  # recurse

        debug("cache file is newer than media file, reading from cache file")
        # otherwise, read from the cache file
        return self.read_cached_duration()


def display_duration(
    ms: Ms,
    *,
    display: Literal["ms", "path", "s", "m", "human", "all"],
    path: Optional[Path],
) -> str:
    if display == "ms":
        return str(round(ms, 2))
    elif display == "path":
        assert path is not None, "path must be provided when display is path"
        return str(path)
    elif display == "s":
        return str(round(ms / 1000, 2))
    elif display == "m":
        return str(round(ms / 1000 / 60, 2))
    elif display == "human":
        # divmod to get hours, minutes, seconds
        m, s = divmod(ms / 1000, 60)
        h, m = divmod(m, 60)
        seconds = f"{s:.2f}".zfill(5)  # pad x.xx with zeros
        return f"{int(h):02d}:{int(m):02d}:{seconds}"
    elif display == "all":
        # recursive call
        assert path is not None, "path must be provided when display is all"
        return "|".join(
            [
                display_duration(ms, display=d, path=path)  # type: ignore[arg-type]
                for d in ("ms", "s", "m", "human", "path")
            ],
        )
    else:
        raise ValueError(f"Invalid display {display}")
