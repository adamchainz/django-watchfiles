from __future__ import annotations

import tempfile
import time
from pathlib import Path

from django.utils import autoreload

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
        assert not self.watcher.stop_event.is_set()
        self.watcher.stop()
        assert self.watcher.stop_event.is_set()

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


class ReplacedGetReloaderTests(SimpleTestCase):
    def test_replaced_get_reloader(self):
        reloader = autoreload.get_reloader()
        assert isinstance(reloader, WatchfilesReloader)
