# Duplicate checking script by Enderek
from colorama import Fore, Style
from os import getcwd
from pathlib import Path
import json as js
from sys import argv
from sys import exit as exit_final

cfg_path: Path = None
config: dict = None
p_folder: Path = None
s_folder: Path = None
dirs: list = None
moddir: Path = None
delete_mode: bool = False


def print_info(message):
    print(Style.RESET_ALL + Fore.LIGHTBLACK_EX + f"[INFO] {message}" + Style.RESET_ALL)

def print_error(message):
    print(Style.RESET_ALL + Fore.RED + f"[ERROR] {message}" + Style.RESET_ALL)

def print_warning(message):
    print(Style.RESET_ALL + Fore.LIGHTYELLOW_EX + f"[WARNING] {message}" + Style.RESET_ALL)

def print_success(message):
    print(Style.RESET_ALL + Fore.GREEN + f"[SUCCESS] {message}" + Style.RESET_ALL)

def exit():
    """Pause the program and then exit"""
    input("Press any key to exit the program.")
    exit_final()

def Settings():
    if "-c" in argv:
        ind = argv.index("-c")
    elif "--config" in argv:
        ind = argv.index("--config")
    else:
        ind = -1

    global cfg_path
    if ind > 0:
        ind += 1
        try:
            cfg_path = Path(argv[ind])
        except IndexError:
            print_error("Config argument given but no path specified!")
            exit()
    else:
        cfg_path = Path("./settings.json")
    
    global delete_mode

    delete_mode = "-d" in argv




def LoadConfig():
    global config
    if not cfg_path.is_file():
        return False

    with open(cfg_path, "r") as c_file:
        config = js.loads(c_file.read())
    return True

def GetModdir():
    try:
        modname = config["Moddir"]
    except:
        print_error("Moddir was not specified in the config file.")
        exit()
    
    global moddir

    cwd = Path(getcwd())
    for parent in cwd.parents:
        if str(parent.stem) == modname:
            moddir = parent
            return
    
    print_error("Moddir could not be located.")
    exit()

def LoadRest():
    global s_folder, p_folder, dirs
    try:
        p_folder = config["PrimaryFolder"]
    except:
        print_error("No PrimaryFolder specified!")
        exit()
    
    try:
        s_folder = config["SecondaryFolder"]
    except:
        print_error("No SecondaryFolder specified!")
        exit()
    
    try:
        dirs = config["CheckDirectories"]
    except:
        print_error("No CheckDirectories specified!")

def ConvertToPaths():
    global p_folder, s_folder
    p_folder = moddir.joinpath(p_folder).resolve()
    s_folder = moddir.joinpath(s_folder).resolve()

    if not p_folder.is_dir():
        print_error("Primary folder does not exist!")
        exit()
    
    if not s_folder.is_dir():
        print_error("Secondary folder does not exist!")
        exit()

def CheckDuplicates(folder):
    print_warning(f"Checking for {folder}")
    p_path = p_folder.joinpath(folder)
    s_path = s_folder.joinpath(folder)
    if not p_path.is_dir():
        print_warning(f"Specified folder {folder} does not exist in Primary!")
        return
    
    if not s_path.is_dir():
        print_warning(f"Specified folder {folder} does not exist in Secondary!")
        return
    
    p_filelist = [x for x in list(p_path.glob("**/*")) if x.is_file()] # Get all of the files
    s_filelist = [x for x in list(s_path.glob("**/*")) if x.is_file()]

    # Make the paths relative and convert to string
    templist = []
    for p in p_filelist:
        t = p.relative_to(p_path)
        templist.append(str(t))
    p_filelist, templist = templist, []
    
    for s in s_filelist:
        t2 = s.relative_to(s_path)
        templist.append(str(t2))
    s_filelist, templist = templist, []

    print_info(f"Files in Primary:   {len(p_filelist)}")
    print_info(f"Files in Secondary: {len(s_filelist)}")

    for fl in p_filelist: # We'll always iterate by the primary pathlist files
        if fl in s_filelist:
            print_info(f"[Duplicate] {fl}")

    if delete_mode:
        print_warning("Are you sure you want to delete these files?")
        input("Press Ctrl+C or close the window to cancel, otherwise, proceeding to delete.")
        for fl in p_filelist:
            if fl in s_filelist:
                delpath: Path = s_path / fl
                print(f"[Deleting] {delpath}")
                delpath.unlink(missing_ok=True)


    

def main():
    Settings()
    print_info("Welcome to DuplicateChecker by Enderek")
    print_info("Loading config from:")
    print_info(f"[ConfigPath]: {str(cfg_path)}")
    LoadConfig()
    print_success("Loaded.")
    print_info("Getting moddir...")
    GetModdir()
    print_info("Loading rest of the config file...")
    LoadRest()
    ConvertToPaths()
    print_info(f"[Primary]   {p_folder}")
    print_info(f"[Secondary] {s_folder}")
    print_info("Proceeding to check for duplicates...")

    for val in dirs:
        CheckDuplicates(val)



    exit()

main()
