=========
Changelog
=========

1.4.0 (2025-09-22)
------------------

* Use watchfiles’ debounce option to batch rapid file changes into a single reload.
  This feature avoids multiple reloads when multiple file changes occur in quick succession.
  Such batched changes can occur include when one file is saved and then updated by a formatter, or when multiple files are changed when you ``git switch`` to another branch.

  `PR #172 <https://github.com/adamchainz/django-watchfiles/pull/172>`__.

* Reload files after they fail with an import-time exception, like a ``SyntaxError``.

  Thanks to Deepak Angrula for the report in `Issue #148 <https://github.com/adamchainz/django-watchfiles/issues/148>`__.

* Watch and reload modules that are loaded during request serving.
  For example, a module may only imported be within a view function, to avoid the initial startup time cost:

  .. code-block:: python

    def index(request):
        from example import fruits

        ...

  Thanks to Tom Forbes for the mechanism in Django’s ``WatchmanReloader``.
  `PR #171 <https://github.com/adamchainz/django-watchfiles/pull/171>`__.

1.3.0 (2025-09-18)
------------------

* Support Django 6.0.

1.2.0 (2025-09-09)
------------------

* Support Python 3.14.

* Correct glob matching to be equivalent to Django’s ``StatReloader`` for ``**`` patterns.
  This fix is limited to Python 3.13+ because it depends the new |Path.full_match()|__ method.

  .. |Path.full_match()| replace:: ``Path.full_match()``
  __ https://docs.python.org/3/library/pathlib.html#pathlib.PurePath.full_match

  `PR #166 <https://github.com/adamchainz/django-watchfiles/pull/166>`__.
  Thanks to Evgeny Arshinov for the report in `Issue #91 <https://github.com/adamchainz/django-watchfiles/issues/91>`__, and Stephen Mitchell for an initial pull request in `PR #134 <https://github.com/adamchainz/django-watchfiles/pull/134>`__.

1.1.0 (2025-02-06)
------------------

* Support Django 5.2.

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
