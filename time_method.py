import time
from contextlib import contextmanager
from colorama import Fore, Style

@contextmanager
def timed(task_name: str = "Task", print_started: bool = True, print_finished: bool = True):
    start = time.time()
    if(print_started):
        print(Fore.MAGENTA + f"{task_name} started at {time.strftime('%H:%M:%S')}")
        print(Style.RESET_ALL)
    try:
        yield
    finally:
        elapsed = time.time() - start
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        if print_finished:
            print(Fore.BLUE + f"{task_name} finished at {time.strftime('%H:%M:%S')} in {minutes} min {seconds} sec")
            print(Style.RESET_ALL)