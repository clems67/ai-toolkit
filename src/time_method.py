import time, functools
from contextlib import contextmanager
from colorama import Fore, Style

@contextmanager
def timed(task_name: str | None = "Task", print_started: bool = True, print_finished: bool = True):
    start = time.time()
    print_start(print_started, task_name)
    try:
        yield
    finally:
        elapsed = time.time() - start
        minutes, seconds = int(elapsed // 60), int(elapsed % 60)
        print_end(minutes, print_finished, seconds, task_name)

def timed_decorator(task_name: str | None = "Task", print_started: bool = True, print_finished: bool = True):
    def decorator(func):
        name = task_name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            print_start(print_started, task_name)
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - start
                minutes, seconds = int(elapsed // 60), int(elapsed % 60)
                print_end(minutes, print_finished, seconds, task_name)
        return wrapper
    return decorator

def print_start(print_started: bool, task_name: str | None):
    if (print_started):
        print(Fore.MAGENTA + f"{task_name} started at {time.strftime('%H:%M:%S')}")
        print(Style.RESET_ALL)

def print_end(minutes: int, print_finished: bool, seconds: int, task_name: str | None):
    if print_finished:
        print(Fore.GREEN + f"{task_name} finished at {time.strftime('%H:%M:%S')} in {minutes} min {seconds} sec")
        print(Style.RESET_ALL)