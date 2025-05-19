from __future__ import annotations

import sys
from contextlib import AbstractContextManager
from typing import Any, Callable, TypeVar

from django import test

_T = TypeVar("_T")

if sys.version_info < (3, 11):

    def _enter_context(cm: Any, addcleanup: Callable[..., None]) -> Any:
        # We look up the special methods on the type to match the with
        # statement.
        cls = type(cm)
        try:
            enter = cls.__enter__
            exit = cls.__exit__
        except AttributeError:  # pragma: no cover
            raise TypeError(
                f"'{cls.__module__}.{cls.__qualname__}' object does "
                f"not support the context manager protocol"
            ) from None
        result = enter(cm)
        addcleanup(exit, cm, None, None, None)
        return result


class SimpleTestCase(test.SimpleTestCase):
    if sys.version_info < (3, 11):

        def enterContext(self, cm: AbstractContextManager[_T]) -> _T:
            result: _T = _enter_context(cm, self.addCleanup)
            return result
