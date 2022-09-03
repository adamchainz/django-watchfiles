from __future__ import annotations

import logging
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any

import watchfiles
from django.conf import settings
from django.utils import autoreload
from django.utils.autoreload import run_with_reloader
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


def replaced_run_with_reloader(
    main_func: Callable[..., Any], *args: Any, **kwargs: Any
) -> None:
    watchfiles_settings = getattr(settings, "WATCHFILES", {})
    if "watch_filter" in watchfiles_settings:
        watchfiles_settings["watch_filter"] = import_string(
            watchfiles_settings["watch_filter"]
        )()
    if "debug" not in watchfiles_settings:
        log_level = 40 - 10 * kwargs["verbosity"]
        logging.getLogger("watchfiles").setLevel(log_level)
        watchfiles_settings["debug"] = log_level == logging.DEBUG

    autoreload.get_reloader = lambda: WatchfilesReloader(watchfiles_settings)
    return run_with_reloader(main_func, *args, **kwargs)


autoreload.run_with_reloader = replaced_run_with_reloader
