from __future__ import annotations

from pathlib import Path
from typing import Generator, Optional, Sequence, Union
import json

import watchfiles
from django.utils import autoreload


class WatchmanConfigFilter(watchfiles.DefaultFilter):
    allowed_extensions = ".py"

    def __init__(
        self,
        *,
        ignore_dirs: Optional[Sequence[str]] = None,
        ignore_entity_patterns: Optional[Sequence[str]] = None,
        ignore_paths: Optional[Sequence[Union[str, Path]]] = None,
    ) -> None:
        if ignore_dirs is None:
            with open(".watchmanconfig") as inf:
                watchmanconfig = json.load(inf)
            pattern_set = set(watchmanconfig["ignore_dirs"])
            pattern_set.add(watchfiles.DefaultFilter.ignore_dirs)
            ignore_dirs = list(pattern_set)
        super().__init__(
            ignore_dirs=ignore_dirs,
            ignore_entity_patterns=ignore_entity_patterns,
            ignore_paths=ignore_paths,
        )


class WatchfilesReloader(autoreload.BaseReloader):
    def watched_roots(self, watched_files: list[Path]) -> frozenset[Path]:
        extra_directories = self.directory_globs.keys()
        watched_file_dirs = {f.parent for f in watched_files}
        sys_paths = set(autoreload.sys_path_directories())
        return frozenset((*extra_directories, *watched_file_dirs, *sys_paths))

    def tick(self) -> Generator[None, None, None]:
        watched_files = list(self.watched_files(include_globs=False))
        roots = autoreload.common_roots(self.watched_roots(watched_files))
        watcher = watchfiles.watch(
            *roots, watch_filter=WatchmanConfigFilter(), debug=True
        )
        for file_changes in watcher:
            for _change, path in file_changes:
                self.notify_file_changed(Path(path))
            yield


def replaced_get_reloader() -> autoreload.BaseReloader:
    return WatchfilesReloader()


autoreload.get_reloader = replaced_get_reloader
