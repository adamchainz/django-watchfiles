from __future__ import annotations

import threading
from collections.abc import Generator
from collections.abc import Iterable
from fnmatch import fnmatch
from pathlib import Path
from typing import Callable

from django.utils import autoreload
from watchfiles import Change
from watchfiles import watch


class MutableWatcher:
    """
    Watchfiles doesn't give us a way to adjust watches at runtime, but it does
    give us a way to stop the watcher when a condition is set.

    This class wraps this to provide a single iterator that may replace the
    underlying watchfiles iterator when roots are added or removed.
    """

    def __init__(self, filter: Callable[[Change, str], bool]) -> None:
        self.change_event = threading.Event()
        self.stop_event = threading.Event()
        self.roots: set[Path] = set()
        self.filter = filter

    def set_roots(self, roots: set[Path]) -> None:
        if roots != self.roots:
            self.roots = roots
            self.change_event.set()

    def stop(self) -> None:
        self.stop_event.set()

    def __iter__(self) -> Generator[set[tuple[Change, str]]]:
        while True:
            if self.stop_event.is_set():
                return
            self.change_event.clear()
            for changes in watch(
                *self.roots,
                watch_filter=self.filter,
                stop_event=self.stop_event,
                debounce=False,
                rust_timeout=100,
                yield_on_timeout=True,
            ):
                if self.change_event.is_set():
                    break
                yield changes


class WatchfilesReloader(autoreload.BaseReloader):
    def __init__(self) -> None:
        self.watcher = MutableWatcher(self.file_filter)
        self.watched_files_set: set[Path] = set()
        super().__init__()

    def file_filter(self, change: Change, filename: str) -> bool:
        path = Path(filename)
        if path in self.watched_files_set:
            return True
        for directory, globs in self.directory_globs.items():
            try:
                relative_path = path.relative_to(directory)
            except ValueError:
                pass
            else:
                relative_path_str = str(relative_path)
                for glob in globs:
                    if fnmatch(relative_path_str, glob):
                        return True
        return False

    def watched_roots(self, watched_files: Iterable[Path]) -> frozenset[Path]:
        # Adapted from WatchmanReloader
        extra_directories = self.directory_globs.keys()
        watched_file_dirs = {f.parent for f in watched_files}
        sys_paths = set(autoreload.sys_path_directories())
        all_dirs = (*extra_directories, *watched_file_dirs, *sys_paths)
        existing_dirs = (p for p in all_dirs if p.exists())
        return frozenset(existing_dirs)

    def tick(self) -> Generator[None]:
        self.watched_files_set = set(self.watched_files(include_globs=False))
        roots = set(
            autoreload.common_roots(
                self.watched_roots(self.watched_files_set),
            )
        )
        self.watcher.set_roots(roots)

        for changes in self.watcher:  # pragma: no branch
            for _, path in changes:  # pragma: no cover
                self.notify_file_changed(Path(path))
            yield


def replaced_get_reloader() -> autoreload.BaseReloader:
    return WatchfilesReloader()


autoreload.get_reloader = replaced_get_reloader
