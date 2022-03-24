=================
django-watchfiles
=================

Use `watchfiles <https://watchfiles.helpmanual.io/>`__ in Django’s autoreloader.

Requirements
------------

Python 3.7 to 3.10 supported.

Django 2.2 to 4.0 supported.

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
