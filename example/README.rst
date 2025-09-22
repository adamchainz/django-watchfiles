Example Project
===============

Use Python 3.13 to set up with these commands:

.. code-block:: sh

   python -m venv .venv
   source .venv/bin/activate
   python -m pip install -e .. -r requirements.txt

Run the server with:

.. code-block:: sh

   python manage.py runserver

Its first log line should confirm the use of django-watchfiles:

.. code-block:: text

    Watching for file changes with WatchfilesReloader

Open it at http://127.0.0.1:8000/ .
You can then play with changing files and seeing the server reload.

It can also be useful to add faults and then fix them, to check that django-watchfiles recovers correctly.
For example, you might cauges a ``SyntaxError`` by mismatching parentheses, or add a slow error with:

.. code-block:: python

    import time

    time.sleep(1)
    1 / 0

(``1 / 0`` is a `trick to quickly fail <https://adamj.eu/tech/2024/06/18/python-fail-1-over-0/>`__.)
