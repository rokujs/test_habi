import logging
import time
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


def measure_time(func: Callable[P, R]) -> Callable[P, R]:
    """
    Decorator that measures and logs the execution time of a function.

    Usage:
        @measure_time
        def my_endpoint():
            ...

    Logs the function name and execution time in milliseconds.
    """

    @wraps(func)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        start_time = time.perf_counter()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            end_time = time.perf_counter()
            elapsed_ms = (end_time - start_time) * 1000
            logger.info(
                "Function '%s' executed in %.2f ms",
                func.__name__,
                elapsed_ms,
            )

    return wrapper
