from __future__ import annotations

import sys
import threading
from collections.abc import Generator, Iterable
from pathlib import Path
from typing import Callable

from django.utils import autoreload
from watchfiles import Change, watch

if sys.version_info >= (3, 13):
    path_full_match = Path.full_match
else:
    import contextlib
    import functools
    import operator
    import os
    import posixpath
    import re

    # Copied from Python 3.13 fnmatch

    _re_setops_sub = re.compile(r"([&~|])").sub
    _re_escape = functools.lru_cache(maxsize=512)(re.escape)

    def _translate(pat, star, question_mark):
        res = []
        add = res.append
        star_indices = []

        i, n = 0, len(pat)
        while i < n:
            c = pat[i]
            i = i + 1
            if c == "*":
                # store the position of the wildcard
                star_indices.append(len(res))
                add(star)
                # compress consecutive `*` into one
                while i < n and pat[i] == "*":
                    i += 1
            elif c == "?":
                add(question_mark)
            elif c == "[":
                j = i
                if j < n and pat[j] == "!":
                    j = j + 1
                if j < n and pat[j] == "]":
                    j = j + 1
                while j < n and pat[j] != "]":
                    j = j + 1
                if j >= n:
                    add("\\[")
                else:
                    stuff = pat[i:j]
                    if "-" not in stuff:
                        stuff = stuff.replace("\\", r"\\")
                    else:
                        chunks = []
                        k = i + 2 if pat[i] == "!" else i + 1
                        while True:
                            k = pat.find("-", k, j)
                            if k < 0:
                                break
                            chunks.append(pat[i:k])
                            i = k + 1
                            k = k + 3
                        chunk = pat[i:j]
                        if chunk:
                            chunks.append(chunk)
                        else:
                            chunks[-1] += "-"
                        # Remove empty ranges -- invalid in RE.
                        for k in range(len(chunks) - 1, 0, -1):
                            if chunks[k - 1][-1] > chunks[k][0]:
                                chunks[k - 1] = chunks[k - 1][:-1] + chunks[k][1:]
                                del chunks[k]
                        # Escape backslashes and hyphens for set difference (--).
                        # Hyphens that create ranges shouldn't be escaped.
                        stuff = "-".join(
                            s.replace("\\", r"\\").replace("-", r"\-") for s in chunks
                        )
                    i = j + 1
                    if not stuff:
                        # Empty range: never match.
                        add("(?!)")
                    elif stuff == "!":
                        # Negated empty range: match any character.
                        add(".")
                    else:
                        # Escape set operations (&&, ~~ and ||).
                        stuff = _re_setops_sub(r"\\\1", stuff)
                        if stuff[0] == "!":
                            stuff = "^" + stuff[1:]
                        elif stuff[0] in ("^", "["):
                            stuff = "\\" + stuff
                        add(f"[{stuff}]")
            else:
                add(_re_escape(c))
        assert i == n
        return res, star_indices

    # Copied from Python 3.13 glob

    magic_check = re.compile("([*?[])")

    _special_parts = ("", ".", "..")
    _no_recurse_symlinks = object()

    def translate(pat, *, recursive=False, include_hidden=False, seps=None):
        """Translate a pathname with shell wildcards to a regular expression.

        If `recursive` is true, the pattern segment '**' will match any number of
        path segments.

        If `include_hidden` is true, wildcards can match path segments beginning
        with a dot ('.').

        If a sequence of separator characters is given to `seps`, they will be
        used to split the pattern into segments and match path separators. If not
        given, os.path.sep and os.path.altsep (where available) are used.
        """
        if not seps:
            if os.path.altsep:
                seps = (os.path.sep, os.path.altsep)
            else:
                seps = os.path.sep
        escaped_seps = "".join(map(re.escape, seps))
        any_sep = f"[{escaped_seps}]" if len(seps) > 1 else escaped_seps
        not_sep = f"[^{escaped_seps}]"
        if include_hidden:
            one_last_segment = f"{not_sep}+"
            one_segment = f"{one_last_segment}{any_sep}"
            any_segments = f"(?:.+{any_sep})?"
            any_last_segments = ".*"
        else:
            one_last_segment = f"[^{escaped_seps}.]{not_sep}*"
            one_segment = f"{one_last_segment}{any_sep}"
            any_segments = f"(?:{one_segment})*"
            any_last_segments = f"{any_segments}(?:{one_last_segment})?"

        results = []
        parts = re.split(any_sep, pat)
        last_part_idx = len(parts) - 1
        for idx, part in enumerate(parts):
            if part == "*":
                results.append(one_segment if idx < last_part_idx else one_last_segment)
            elif recursive and part == "**":
                if idx < last_part_idx:
                    if parts[idx + 1] != "**":
                        results.append(any_segments)
                else:
                    results.append(any_last_segments)
            else:
                if part:
                    if not include_hidden and part[0] in "*?":
                        results.append(r"(?!\.)")
                    results.extend(_translate(part, f"{not_sep}*", not_sep))
                if idx < last_part_idx:
                    results.append(any_sep)
        res = "".join(results)
        return rf"(?s:{res})\Z"

    @functools.lru_cache(maxsize=512)
    def _compile_pattern(pat, sep, case_sensitive, recursive=True):
        """Compile given glob pattern to a re.Pattern object (observing case
        sensitivity)."""
        flags = re.NOFLAG if case_sensitive else re.IGNORECASE
        regex = translate(pat, recursive=recursive, include_hidden=True, seps=sep)
        return re.compile(regex, flags=flags).match

    class _Globber:
        """Class providing shell-style pattern matching and globbing."""

        def __init__(self, sep, case_sensitive, case_pedantic=False, recursive=False):
            self.sep = sep
            self.case_sensitive = case_sensitive
            self.case_pedantic = case_pedantic
            self.recursive = recursive

        # Low-level methods

        lstat = operator.methodcaller("lstat")
        add_slash = operator.methodcaller("joinpath", "")

        @staticmethod
        def scandir(path):
            """Emulates os.scandir(), which returns an object that can be used as
            a context manager. This method is called by walk() and glob().
            """
            return contextlib.nullcontext(path.iterdir())

        @staticmethod
        def concat_path(path, text):
            """Appends text to the given path."""
            return path.with_segments(path._raw_path + text)

        @staticmethod
        def parse_entry(entry):
            """Returns the path of an entry yielded from scandir()."""
            return entry

        # High-level methods

        def compile(self, pat):
            return _compile_pattern(pat, self.sep, self.case_sensitive, self.recursive)

        def selector(self, parts):
            """Returns a function that selects from a given path, walking and
            filtering according to the glob-style pattern parts in *parts*.
            """
            if not parts:
                return self.select_exists
            part = parts.pop()
            if self.recursive and part == "**":
                selector = self.recursive_selector
            elif part in _special_parts:
                selector = self.special_selector
            elif not self.case_pedantic and magic_check.search(part) is None:
                selector = self.literal_selector
            else:
                selector = self.wildcard_selector
            return selector(part, parts)

        def special_selector(self, part, parts):
            """Returns a function that selects special children of the given path."""
            select_next = self.selector(parts)

            def select_special(path, exists=False):
                path = self.concat_path(self.add_slash(path), part)
                return select_next(path, exists)

            return select_special

        def literal_selector(self, part, parts):
            """Returns a function that selects a literal descendant of a path."""

            # Optimization: consume and join any subsequent literal parts here,
            # rather than leaving them for the next selector. This reduces the
            # number of string concatenation operations and calls to add_slash().
            while parts and magic_check.search(parts[-1]) is None:
                part += self.sep + parts.pop()

            select_next = self.selector(parts)

            def select_literal(path, exists=False):
                path = self.concat_path(self.add_slash(path), part)
                return select_next(path, exists=False)

            return select_literal

        def wildcard_selector(self, part, parts):
            """Returns a function that selects direct children of a given path,
            filtering by pattern.
            """

            match = None if part == "*" else self.compile(part)
            dir_only = bool(parts)
            if dir_only:
                select_next = self.selector(parts)

            def select_wildcard(path, exists=False):
                try:
                    # We must close the scandir() object before proceeding to
                    # avoid exhausting file descriptors when globbing deep trees.
                    with self.scandir(path) as scandir_it:
                        entries = list(scandir_it)
                except OSError:
                    pass
                else:
                    for entry in entries:
                        if match is None or match(entry.name):
                            if dir_only:
                                try:
                                    if not entry.is_dir():
                                        continue
                                except OSError:
                                    continue
                            entry_path = self.parse_entry(entry)
                            if dir_only:
                                yield from select_next(entry_path, exists=True)
                            else:
                                yield entry_path

            return select_wildcard

        def recursive_selector(self, part, parts):
            """Returns a function that selects a given path and all its children,
            recursively, filtering by pattern.
            """
            # Optimization: consume following '**' parts, which have no effect.
            while parts and parts[-1] == "**":
                parts.pop()

            # Optimization: consume and join any following non-special parts here,
            # rather than leaving them for the next selector. They're used to
            # build a regular expression, which we use to filter the results of
            # the recursive walk. As a result, non-special pattern segments
            # following a '**' wildcard don't require additional filesystem access
            # to expand.
            follow_symlinks = self.recursive is not _no_recurse_symlinks
            if follow_symlinks:
                while parts and parts[-1] not in _special_parts:
                    part += self.sep + parts.pop()

            match = None if part == "**" else self.compile(part)
            dir_only = bool(parts)
            select_next = self.selector(parts)

            def select_recursive(path, exists=False):
                path = self.add_slash(path)
                match_pos = len(str(path))
                if match is None or match(str(path), match_pos):
                    yield from select_next(path, exists)
                stack = [path]
                while stack:
                    yield from select_recursive_step(stack, match_pos)

            def select_recursive_step(stack, match_pos):
                path = stack.pop()
                try:
                    # We must close the scandir() object before proceeding to
                    # avoid exhausting file descriptors when globbing deep trees.
                    with self.scandir(path) as scandir_it:
                        entries = list(scandir_it)
                except OSError:
                    pass
                else:
                    for entry in entries:
                        is_dir = False
                        try:
                            if entry.is_dir(follow_symlinks=follow_symlinks):
                                is_dir = True
                        except OSError:
                            pass

                        if is_dir or not dir_only:
                            entry_path = self.parse_entry(entry)
                            if match is None or match(str(entry_path), match_pos):
                                if dir_only:
                                    yield from select_next(entry_path, exists=True)
                                else:
                                    # Optimization: directly yield the path if this is
                                    # last pattern part.
                                    yield entry_path
                            if is_dir:
                                stack.append(entry_path)

            return select_recursive

        def select_exists(self, path, exists=False):
            """Yields the given path, if it exists."""
            if exists:
                # Optimization: this path is already known to exist, e.g. because
                # it was returned from os.scandir(), so we skip calling lstat().
                yield path
            else:
                try:
                    self.lstat(path)
                    yield path
                except OSError:
                    pass

    class _StringGlobber(_Globber):
        lstat = staticmethod(os.lstat)
        scandir = staticmethod(os.scandir)
        parse_entry = operator.attrgetter("path")
        concat_path = operator.add

        if os.name == "nt":

            @staticmethod
            def add_slash(pathname):
                tail = os.path.splitroot(pathname)[2]
                if not tail or tail[-1] in "\\/":
                    return pathname
                return f"{pathname}\\"
        else:

            @staticmethod
            def add_slash(pathname):
                if not pathname or pathname[-1] == "/":
                    return pathname
                return f"{pathname}/"

    # Copied from Python 3.13 pathlib

    def path_full_match(path, pattern, *, case_sensitive=None):
        """
        Return True if this path matches the given glob-style pattern. The
        pattern is matched against the entire path.
        """
        if not hasattr(pattern, "with_segments"):
            pattern = path.with_segments(pattern)
        if case_sensitive is None:
            case_sensitive = path._flavour is posixpath

        # The string representation of an empty path is a single dot ('.'). Empty
        # paths shouldn't match wildcards, so we change it to the empty string.
        strpath = str(path) if path.parts else ""
        pattern = str(pattern) if pattern.parts else ""
        globber = _StringGlobber(path._flavour.sep, case_sensitive, recursive=True)
        return globber.compile(pattern)(strpath) is not None


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
