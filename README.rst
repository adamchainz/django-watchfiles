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

Use `watchfiles <https://watchfiles.helpmanual.io/>`__ in Django’s autoreloader.

----

**Improve your Django and Git skills** with `my books <https://adamj.eu/books/>`__.

----

Requirements
------------

Python 3.9 to 3.13 supported.

Django 4.2 to 5.1 supported.

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

Django doesn’t provide an official API for alternative autoreloader classes.
Therefore, django-watchfiles monkey-patches ``django.utils.autoreload`` to make its own reloader the only available class.
You can tell it is installed as ``runserver`` will list ``WatchfilesReloader`` as in use:

.. code-block:: shell

   $ ./manage.py runserver
   Watching for file changes with WatchfilesReloader
   ...

Unlike Django’s built-in ``WatchmanReloader``, there is no need for a fallback to ``StatReloader``, since ``watchfiles`` implements its own internal fallback to using ``stat``.
