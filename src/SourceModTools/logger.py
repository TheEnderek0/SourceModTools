import logging
from pathlib import Path
from os import remove, rename
from colorama import Fore, Style, just_fix_windows_console
from sys import platform

MAX_LOGS = 5


if platform == "win32":
    just_fix_windows_console()


class Formatter():
    def __init__(self, use_colors = True):
        
        if use_colors:
            self.formats = {
                logging.DEBUG:  logging.Formatter(Style.DIM + "[D] %(name)s: %(message)s " + Style.RESET_ALL),
                logging.INFO:   logging.Formatter(Style.NORMAL + "[I] %(name)s: %(message)s " + Style.RESET_ALL),
                logging.WARN: logging.Formatter(Style.BRIGHT + Fore.LIGHTYELLOW_EX + "[W] %(name)s: %(message)s " + Style.RESET_ALL),
                logging.ERROR: logging.Formatter(Style.BRIGHT + Fore.RED + "[E] %(name)s: %(message)s " + Style.RESET_ALL),
                logging.CRITICAL: logging.Formatter(Style.DIM + Fore.LIGHTRED_EX + "[C] %(name)s: %(message)s " + Style.RESET_ALL),
            }
        else:
            self.formats = {
                logging.DEBUG:  logging.Formatter("[D] %(name)s: %(message)s"),
                logging.INFO:   logging.Formatter("[I] %(name)s: %(message)s"),
                logging.WARN: logging.Formatter("[W] %(name)s: %(message)s"),
                logging.ERROR: logging.Formatter("[E] %(name)s: %(message)s"),
                logging.CRITICAL: logging.Formatter("[C] %(name)s: %(message)s"),
            }

    def format(self, record: logging.LogRecord):
        formatter = self.formats[record.levelno]
        return formatter.format(record)
    



def SetupLogger(log_file: Path, debug_mode = False):

    if type(log_file) == str:
        log_file = Path(log_file)


    # We have a previous log, rename it to .../name_i.txt, or delete if it exeeds MAX_LOGS
    if log_file.exists():
        f_ext = log_file.suffix
        f_name = log_file.stem


        for i in range(MAX_LOGS, -1, -1): #Cycle from [0; MAX_LOGS] but in reverse order 
            
            if i > 0:
                this_file = log_file.with_name(f"{f_name}_{i}{f_ext}")
            else:
                this_file = log_file
            
            new_file = log_file.with_name(f"{f_name}_{i + 1}{f_ext}")

            if i > 1:
                below_file = log_file.with_name(f"{f_name}_{i - 1}{f_ext}")
            else:
                below_file = log_file

            # If the below file doesn't exist don't do anything. In a situation where we have the files:
            # log_5.txt
            # log_3.txt
            # ...
            # Someone has deleted the log_4 file, but don't remove log_5 since we aren't over the MAX_LOGS limit yet
            # log_3 will become log_4 (if it has log_2 below, etc.) and it at the next iteration only log_5 will get replaced

            if this_file.exists() and below_file.exists():
                if i == MAX_LOGS:
                    remove(this_file)
                else:
                    rename(this_file, new_file)


    file_handler = logging.FileHandler(log_file, mode="w")
    console_handler = logging.StreamHandler()

    console_handler.setFormatter(Formatter()) # pyright: ignore[reportArgumentType]
    file_handler.setFormatter(Formatter(False)) # pyright: ignore[reportArgumentType]

    logging.basicConfig(
        handlers = [file_handler, console_handler],
        level = logging.DEBUG if debug_mode else logging.INFO
    )

    logger = logging.getLogger('LOGGER')

    logger.info(f"Logger initialized, logging to {log_file.absolute()}, debug={debug_mode}")


def getLogger(name:str):
    return logging.getLogger(name)
    



