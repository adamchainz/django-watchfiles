from __future__ import annotations

import sys
import threading
from collections.abc import Generator, Iterable
from pathlib import Path
from typing import Any, Callable

from django.core.signals import request_finished
from django.utils import autoreload
from django.utils.autoreload import _error_files  # type: ignore [attr-defined]
from watchfiles import Change, watch

if sys.version_info >= (3, 13):
    path_full_match = Path.full_match
else:
    # True backport turned out to be too hard. Instead, fall back to the
    # pre-existing incorrect fnmatch implementation

    from fnmatch import fnmatch

    def path_full_match(path: Path, pattern: str) -> bool:
        return fnmatch(str(path), pattern)


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
                rust_timeout=100,
                yield_on_timeout=True,
            ):
                if self.change_event.is_set():
                    break
                yield changes


class WatchfilesReloader(autoreload.BaseReloader):
    def __init__(self) -> None:
        super().__init__()
        self.watcher = MutableWatcher(self.file_filter)
        self.watched_files_set: set[Path] = set()
        self.processed_request = threading.Event()

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
                if any(path_full_match(relative_path, glob) for glob in globs):
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

    def update_watches(self) -> None:
        self.watched_files_set = set(self.watched_files(include_globs=False))
        roots = set(
            autoreload.common_roots(
                self.watched_roots(self.watched_files_set),
            )
        )
        self.watcher.set_roots(roots)

    def request_processed(self, **kwargs: Any) -> None:
        self.processed_request.set()

    def tick(self) -> Generator[None]:
        request_finished.connect(self.request_processed)
        num_error_files = len(_error_files)
        self.update_watches()

        for changes in self.watcher:  # pragma: no branch
            should_update = False

            if len(_error_files) != num_error_files:
                # Error files changed, pick them up.
                should_update = True
                num_error_files = len(_error_files)

            if self.processed_request.is_set():
                should_update = True
                self.processed_request.clear()

            if should_update:
                self.update_watches()

            for _, path in changes:  # pragma: no cover
                self.notify_file_changed(Path(path))
            yield


def replaced_get_reloader() -> autoreload.BaseReloader:
    return WatchfilesReloader()


autoreload.get_reloader = replaced_get_reloader
