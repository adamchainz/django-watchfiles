from __future__ import annotations

import tempfile
import time
from pathlib import Path

import pytest
from django.utils import autoreload
from watchfiles import Change

from django_watchfiles import MutableWatcher
from django_watchfiles import WatchfilesReloader
from tests.compat import SimpleTestCase


class MutableWatcherTests(SimpleTestCase):
    def setUp(self):
        self.watcher = MutableWatcher(lambda *args: True)
        self.addCleanup(self.watcher.stop)

        temp_dir = self.enterContext(tempfile.TemporaryDirectory())
        self.temp_path = Path(temp_dir)

    def test_set_roots_unchanged(self):
        assert not self.watcher.change_event.is_set()
        self.watcher.set_roots(set())
        assert not self.watcher.change_event.is_set()

    def test_set_roots_changed(self):
        assert not self.watcher.change_event.is_set()
        self.watcher.set_roots({Path("/tmp")})
        assert self.watcher.change_event.is_set()

    def test_stop(self):
        (self.temp_path / "test.txt").touch()
        self.watcher.set_roots({self.temp_path})
        iterator = iter(self.watcher)
        # Flush initial events
        next(iterator)

        self.watcher.stop()

        with pytest.raises(StopIteration):
            next(iterator)

        # Not possible to restart
        with pytest.raises(StopIteration):
            next(iter(self.watcher))

    def test_iter_no_changes(self):
        (self.temp_path / "test.txt").touch()
        self.watcher.set_roots({self.temp_path})
        iterator = iter(self.watcher)
        # flush initial events
        next(iterator)
        time.sleep(0.1)  # 100ms Rust timeout

        changes = next(iterator)

        assert changes == set()

    def test_iter_yields_changes(self):
        (self.temp_path / "test.txt").touch()
        self.watcher.set_roots({self.temp_path})
        iterator = iter(self.watcher)
        # flush initial events
        next(iterator)

        (self.temp_path / "test.txt").touch()
        changes = next(iterator)

        assert isinstance(changes, set)
        assert len(changes) == 1
        _, path = changes.pop()
        assert path == str(self.temp_path.resolve() / "test.txt")

    def test_iter_respects_change_event(self):
        (self.temp_path / "test.txt").touch()
        self.watcher.set_roots({self.temp_path})
        iterator = iter(self.watcher)
        # flush initial events
        next(iterator)

        self.watcher.set_roots(set())
        self.watcher.set_roots({self.temp_path})
        changes = next(iterator)

        assert isinstance(changes, set)
        assert len(changes) == 0


class WatchfilesReloaderTests(SimpleTestCase):
    def setUp(self):
        temp_dir = self.enterContext(tempfile.TemporaryDirectory())
        self.temp_path = Path(temp_dir)

        self.reloader = WatchfilesReloader()

    def test_file_filter_watched_file(self):
        test_txt = self.temp_path / "test.txt"
        self.reloader.watched_files_set = {test_txt}

        result = self.reloader.file_filter(Change.modified, str(test_txt))

        assert result is True

    def test_file_filter_unwatched_file(self):
        test_txt = self.temp_path / "test.txt"

        result = self.reloader.file_filter(Change.modified, str(test_txt))

        assert result is False

    def test_file_filter_glob_matched(self):
        self.reloader.watch_dir(self.temp_path, "*.txt")

        result = self.reloader.file_filter(
            Change.modified, str(self.temp_path / "test.txt")
        )

        assert result is True

    def test_file_filter_glob_multiple_globs_unmatched(self):
        self.reloader.watch_dir(self.temp_path, "*.css")
        self.reloader.watch_dir(self.temp_path, "*.html")

        result = self.reloader.file_filter(
            Change.modified, str(self.temp_path / "test.py")
        )

        assert result is False

    def test_file_filter_glob_multiple_dirs_unmatched(self):
        self.reloader.watch_dir(self.temp_path, "*.css")
        temp_dir2 = self.enterContext(tempfile.TemporaryDirectory())
        self.reloader.watch_dir(Path(temp_dir2), "*.html")

        result = self.reloader.file_filter(
            Change.modified, str(self.temp_path / "test.py")
        )

        assert result is False

    def test_file_filter_glob_relative_path_impossible(self):
        temp_dir2 = self.enterContext(tempfile.TemporaryDirectory())

        self.reloader.watch_dir(Path(temp_dir2), "*.txt")

        result = self.reloader.file_filter(
            Change.modified, str(self.temp_path / "test.txt")
        )

        assert result is False

    def test_tick(self):
        test_txt = self.temp_path / "test.txt"
        self.reloader.extra_files = {test_txt}

        iterator = self.reloader.tick()
        result = next(iterator)
        assert result is None

        result = self.reloader.file_filter(Change.modified, str(test_txt))
        assert result is True


class ReplacedGetReloaderTests(SimpleTestCase):
    def test_replaced_get_reloader(self):
        reloader = autoreload.get_reloader()
        assert isinstance(reloader, WatchfilesReloader)
