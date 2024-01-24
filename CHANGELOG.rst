=========
Changelog
=========

* Fix Python 3.8 compatibility by replacing call to ``pathlib.Path.is_relative_to()``.

  Thanks to Nathan Koch in `PR #68 <https://github.com/adamchainz/django-watchfiles/pull/68>`__.

0.1.0 (2023-10-11)
------------------

* Update the watcher when Django adds or removes directories.

  Thanks to Tom Forbes in `commit dc1af91 <https://github.com/adamchainz/django-watchfiles/commit/dc1af91876a6a7d6311268f23088fb83657df7c9>`__.

* Support Django 5.0.

* Drop Python 3.7 support.

* Support Python 3.12.

0.0.1 (2022-03-24)
------------------

* Initial release.
