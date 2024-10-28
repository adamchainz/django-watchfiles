=========
Changelog
=========

1.0.0 (2024-10-28)
------------------

* Drop Django 3.2 to 4.1 support.

* Drop Python 3.8 support.

* Support Python 3.13.

* Fix crashing on non-existent directories, which Django sometimes tries to watch.

  Thanks to baseplate-admin for the report in `Issue #12 <https://github.com/adamchainz/django-watchfiles/issues/12>`__ and Steven Mapes for the fix in `PR #117 <https://github.com/adamchainz/django-watchfiles/pull/117>`__.

0.2.0 (2024-06-19)
------------------

* Support Django 5.1.

0.1.1 (2024-01-24)
------------------

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
