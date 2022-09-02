from __future__ import annotations

import os
import signal
import sys
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any

import watchfiles
from django.conf import settings
from django.utils import autoreload
from django.utils.autoreload import (
    DJANGO_AUTORELOAD_ENV,
    logger,
    restart_with_reloader,
    start_django,
)
from django.utils.module_loading import import_string


class WatchfilesReloader(autoreload.BaseReloader):
    def __init__(self, watchfiles_settings: dict[str, Any]) -> None:
        super().__init__()
        self.watchfiles_settings = watchfiles_settings

    def watched_roots(self, watched_files: list[Path]) -> frozenset[Path]:
        extra_directories = self.directory_globs.keys()
        watched_file_dirs = {f.parent for f in watched_files}
        sys_paths = set(autoreload.sys_path_directories())
        return frozenset((*extra_directories, *watched_file_dirs, *sys_paths))

    def tick(self) -> Generator[None, None, None]:
        watched_files = list(self.watched_files(include_globs=False))
        roots = autoreload.common_roots(self.watched_roots(watched_files))
        watcher = watchfiles.watch(*roots, **self.watchfiles_settings)
        for file_changes in watcher:
            for _change, path in file_changes:
                self.notify_file_changed(Path(path))
            yield


def run_with_reloader(main_func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
    watchfiles_settings = getattr(settings, "DJANGO_WATCHFILES", {})
    if watchfiles_settings.get("watch_filter"):
        watchfiles_settings["watch_filter"] = import_string(
            watchfiles_settings["watch_filter"]
        )()
    if "debug" not in watchfiles_settings:
        watchfiles_settings["debug"] = kwargs["verbosity"] > 1

    signal.signal(signal.SIGTERM, lambda *args: sys.exit(0))
    try:
        if os.environ.get(DJANGO_AUTORELOAD_ENV) == "true":
            reloader = WatchfilesReloader(watchfiles_settings)
            logger.info("Watching for file changes with %s", type(reloader).__name__)
            start_django(reloader, main_func, *args, **kwargs)
        else:
            exit_code = restart_with_reloader()
            sys.exit(exit_code)
    except KeyboardInterrupt:
        pass


autoreload.run_with_reloader = run_with_reloader
