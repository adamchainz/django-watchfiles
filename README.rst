=================
django-watchfiles
=================

.. image:: https://img.shields.io/github/actions/workflow/status/adamchainz/django-watchfiles/main.yml.svg?branch=main&style=for-the-badge
   :target: https://github.com/adamchainz/django-watchfiles/actions?workflow=CI

.. image:: https://img.shields.io/badge/Coverage-100%25-success?style=for-the-badge
   :target: https://github.com/adamchainz/django-watchfiles/actions?workflow=CI

.. image:: https://img.shields.io/pypi/v/django-watchfiles.svg?style=for-the-badge
   :target: https://pypi.org/project/django-watchfiles/

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge
   :target: https://github.com/psf/black

.. image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white&style=for-the-badge
   :target: https://github.com/pre-commit/pre-commit
   :alt: pre-commit

Make Django’s autoreloader more efficient by watching for changes with `watchfiles <https://watchfiles.helpmanual.io/>`__.

----

**Improve your Django and Git skills** with `my books <https://adamj.eu/books/>`__.

----

Requirements
------------

Python 3.9 to 3.14 supported.

Django 4.2 to 6.0 supported.

Installation
------------

1. Install with **pip**:

   .. code-block:: sh

       python -m pip install django-watchfiles

2. Add django-watchfiles to your ``INSTALLED_APPS``:

   .. code-block:: python

       INSTALLED_APPS = [
           ...,
           "django_watchfiles",
           ...,
       ]

That’s it! 😅

Try installing `django-browser-reload <https://github.com/adamchainz/django-browser-reload>`__ as well, to make your browser automatically reload the page when changes are detected.

Usage
-----

django-watchfiles will be automatically used by Django’s |runserver command|__.
You can tell this because ``runserver`` will list ``WatchfilesReloader`` as the watcher class:

.. |runserver command| replace:: ``runserver`` command
__ https://docs.djangoproject.com/en/stable/ref/django-admin/#runserver

.. code-block:: shell

   $ ./manage.py runserver
   Watching for file changes with WatchfilesReloader
   ...

(Rather than the default ``StatReloader``.)

``WatchfilesReloader`` provides the following advantages:

* **Much lower CPU usage**

  Django’s default ``StatReloader`` works by polling all files for changes, sleeping for one second, and looping.
  Meanwhile, ``WatchfilesReloader`` avoids polling; instead, it asks the operating system to report any changes to the watched files.

  The difference can be stark and save you significant battery when developing on a device that isn’t connected to a power source.
  A quick benchmark on a medium-sized project (385,000 lines plus 206 installed packages) using an M1 MacBook showed ``StatReloader`` using ~10% of a core every other second, while ``WatchfilesReloader`` uses 0%.

* **Reduced reload time**

  ``StatReloader`` can take one second or more to detect changes, while ``WatchfilesReloader`` can take as little as 50 milliseconds.
  This means that ``runserver`` starts reloading your code more quickly, and you can iterate more rapidly.

* **Batched reloads**

  Sometimes multiple file changes can occur in quick succession, such as when one file is saved and then updated by a formatter, or when multiple files are changed when you ``git switch`` to another branch.
  In such cases, ``StatReloader`` can trigger multiple reloads, unnecessarily slowing down progress, or it can miss some changes, leading to old code being left running.
  ``WatchfilesReloader`` instead batches changes, using watchfiles’ `debounce feature <https://watchfiles.helpmanual.io/api/watch/#:~:text=debounce,-int>`__, so that multiple changes will only trigger a single reload.

  ``WatchfilesReloader`` uses watchfiles’ defaults here, waiting for changes within a 50 millisecond window, and repeating this wait for up to 1600 milliseconds, as long as changes keep occurring.
  These values provide a good balance between responsiveness and batching.

History
-------

Django’s ``runserver`` started with only the logic for ``StatReloader``, because it’s simple and works on all platforms.

In Django 1.7 (2014), Django gained support for using the Linux file-watching API ``inotify``, through the `pyinotify package <https://pypi.org/project/pyinotify/>`__.
This provided efficient reloading, but was limited to Linux.
This was thanks to Unai Zalakain, Chris Lamb, and Pascal Hartig for that work in `Ticket #9722 <https://code.djangoproject.com/ticket/9722>`__.

In Django 2.2 (2019), Django gained support for `Watchman <https://facebook.github.io/watchman/>`__, a cross-platform file-watching service from Facebook, via the `pywatchman package <https://pypi.org/project/pywatchman/>`__.
This provides efficient reloading on Linux and macOS, but requires developers to install and run the Watchman service separately.
Thanks to Tom Forbes for that work in `Ticket #27685 <https://code.djangoproject.com/ticket/27685>`__.

Unfortunately, the pywatchman package stopped working on Python 3.10, as reported in its `Issue #970 <https://github.com/facebook/watchman/issues/970>`__ (2021).
This issue remained unfixed for a long time, until March 2024, after the release of Python 3.12.
It appears that Watchman and pywatchman are not a priority for maintenance by Facebook.

In 2022, Samel Colvin released `watchfiles <https://pypi.org/project/watchfiles/>`__, a new cross-platform file-watching library for Python.
It is powered by `Notify <https://github.com/notify-rs/notify>`__, a popular and established Rust crate.
(watchfiles is also the Rust-powered rebuild of Samuel’s earlier `watchgod package <https://pypi.org/project/watchgod/>`__ (2017).)

I created django-watchfiles in 2022 to integrate watchfiles with Django’s autoreloader.
The inspiration came from writing about using Watchman in `Boost Your Django DX <https://adamchainz.gumroad.com/l/byddx>`__ and feeling a bit dismayed that it wasn’t particularly easy, and that it wasn’t (yet) working on Python 3.10.

django-watchfiles had its first stable release in 2024.
I may propose integrating it with Django core at some point, when it’s more established.
