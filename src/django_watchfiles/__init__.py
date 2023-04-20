from __future__ import annotations

import fnmatch
import threading
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Generator

import watchfiles
from django.utils import autoreload


class MutableWatcher:
    """
    Watchfiles doesn't give us a way to adjust watches at runtime, but it does
    give us a way to stop the watcher when a condition is set.

    This class wraps this to provide a single iterator that may replace the
    underlying watchfiles iterator when roots are added or removed.
    """

    def __init__(self, filter: Callable[[watchfiles.Change, str], bool]) -> None:
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

    def __iter__(self) -> Generator[Any, None, None]:  # TODO: better type
        while True:
            self.change_event.clear()
            for changes in watchfiles.watch(
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
        super().__init__()

    def file_filter(self, change: watchfiles.Change, filename: str) -> bool:
        path = Path(filename)
        # print(f"Path: {path} / {change}")
        if path in set(self.watched_files(include_globs=False)):
            # print("Path in watched files")
            return True
        for directory, globs in self.directory_globs.items():
            if path.is_relative_to(directory):
                # print("Path is sub dir")
                for glob in globs:
                    if fnmatch.fnmatch(str(path.relative_to(directory)), glob):
                        # print("Path is glob match")
                        return True
        # print("file filter", change, path)
        return False

    def watched_roots(self, watched_files: list[Path]) -> frozenset[Path]:
        extra_directories = self.directory_globs.keys()
        watched_file_dirs = {f.parent for f in watched_files}
        sys_paths = set(autoreload.sys_path_directories())
        return frozenset((*extra_directories, *watched_file_dirs, *sys_paths))

    def tick(self) -> Generator[None, None, None]:
        watched_files = list(self.watched_files(include_globs=False))
        roots = set(autoreload.common_roots(self.watched_roots(watched_files)))
        self.watcher.set_roots(roots)

        for changes in self.watcher:
            for _, path in changes:
                self.notify_file_changed(Path(path))
            yield


def replaced_get_reloader() -> autoreload.BaseReloader:
    return WatchfilesReloader()


autoreload.get_reloader = replaced_get_reloader
