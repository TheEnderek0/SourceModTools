# Build script by Enderek
# Meant to build sourcemods
from sys import argv
from colorama import Fore, Style
from shutil import copy2 as CopyFile
from os import getcwd
from pathlib import Path
import json as js # Troll :O
from srctools import steam


PROGRESSPRINT = False
fm_path = None
log_path = None
w_dir = None
skip_confirm_dialog = False

def Settings():
    errored = False
    def r_error(message):
        return Style.RESET_ALL + Fore.RED + f"[STARTUP ERROR] {message}" + Style.RESET_ALL

    # Progressprint
    global PROGRESSPRINT
    if "-pp" in argv or "--progressprint" in argv:
        PROGRESSPRINT = True
    else:
        PROGRESSPRINT = False
    # End

    # Override filemanifest
    global fm_path
    try:
        fm_parm = argv.index("--filemanifest")
        fm_path = Path(argv[fm_parm + 1])
        fm_path = Path(getcwd()).joinpath(fm_path).resolve()
        if not fm_path.is_file():
            print(fm_path)
            print(r_error("Specified filemanifest does not exist!"))
            errored = True
    except ValueError as e:
        fm_path = "./filemanifest.json"
        fm_path = Path(getcwd()).joinpath(fm_path).resolve()
        if not fm_path.is_file():
            print(fm_path)
            print(r_error("Cannot find filemanifest!"))
            errored = True
    except IndexError as e:
        print(r_error("Path to filemanifest was not specified!"))
        errored = True
    # End

    # Logfile
    global log_path
    if "-l" in argv:
        search = "-l"
    elif "--logfile" in argv:
        search = "--logfile"
    else:
        search = False
    if search:
        try:
            log_path = Path(getcwd()).joinpath(Path(    argv[argv.index(search) + 1]    )).resolve()
        except IndexError:
            print(r_error("Logfile was specified but no path was provided!"))
            errored = True
    
    if errored:
        exit()
    # End
        
    # Skip dialog
    global skip_confirm_dialog
    if "-s" in argv or "--skipdialog" in argv:
        skip_confirm_dialog = True
    # End
    


    
FM = None # Filemanifest


def print_info(message):
    print(Style.RESET_ALL + Fore.LIGHTBLACK_EX + f"[INFO] {message}" + Style.RESET_ALL)

def print_error(message):
    print(Style.RESET_ALL + Fore.RED + f"[ERROR] {message}" + Style.RESET_ALL)

def print_warning(message):
    print(Style.RESET_ALL + Fore.LIGHTYELLOW_EX + f"[WARNING] {message}" + Style.RESET_ALL)

def print_success(message):
    print(Style.RESET_ALL + Fore.GREEN + f"[SUCCESS] {message}" + Style.RESET_ALL)

p1_old = 0
total_progress = 0

def print_progress(current, total_block, total_max, mess):
    global p1_old
    global total_progress
    p1 = round((total_progress / total_max) * 100) 

    if PROGRESSPRINT:
        p2 = round((current / total_block) * 100)
        message = Style.RESET_ALL + Fore.GREEN + f"[{p1}%]" + Fore.LIGHTGREEN_EX + f"[{p2}%] " + Style.RESET_ALL + str(mess)
        print(message)
    elif p1 > p1_old: # Only do a general progress of p1, also only print if the progress actually changed, to save on time
        print("\r" + Style.RESET_ALL + Fore.GREEN + f"[COPYING IN PROGRESS]: {p1}%" + Style.RESET_ALL, end="")
        p1_old = p1
    
    total_progress += 1


def LoadManifest():
    global FM
    with open(fm_path, "r") as fm_file:
        FM = js.loads(fm_file.read())

def DetermineFullCWD(name: str):
    global w_dir
    cwd = Path(getcwd())

    if name.startswith("<") and (endindx := name.find(">")) != -1:
        name = name[1:endindx]

        path = steam.find_app(int(name))
        w_dir = path.path
        print(w_dir)
        return


    parentlist = list(cwd.parents) + [cwd]
    for p in parentlist:
        if str(p.stem) == name:
            w_dir = p
            return
        
    print_warning(f"Working directory: {cwd} | tried to find parent: {name}")
    print_error("Specified working directory does not exist!")
    exit()

class ExportFolder: #Helper class for every json block in "export": [<blocks>]
    path_relative: Path = None
    path_folder: Path = None
    absolute_path: Path = None
    export_all = True
    whitelist = None
    blacklist = None

    filelist = []

    def __init__(self, block):
        try:
            self.path_folder = block["path"]
        except:
            print_error(f"Block {block} has no defined \"path\"!")
            raise RuntimeError
        
        self.absolute_path = w_dir.joinpath(self.path_folder).resolve()
        if not self.absolute_path.is_dir():
            print_error(f"In block {self.path_folder}, Path: {self.absolute_path} does not exist! ")
            raise RuntimeError
        
        try:
            self.path_relative = w_dir.joinpath(Path(block["path_relative"])).resolve()
            if not self.path_relative.is_dir():
                print_error(f"Block {self.path_folder} has invalid path_relative defined!")
                exit()
        except:
            print_error(f"Block {self.path_folder} has no path_relative defined!")
            raise RuntimeError
        
        try:
            self.export_all = block["export_all"]
        except:
            print_warning(f"Block {self.path_folder} has no \"export_all\" defined, defaulting to True!")
            self.export_all = True
        
        try:
            self.whitelist = block["whitelist"]
        except:
            if not self.export_all:
                print_error(f"In block {self.path_folder} export_all set to false, but whitelist does not exist! Export files are unknown!")
                exit()
            # It doesn't need to exist if we export_all is enabled
        
        try:
            self.blacklist = block["blacklist"]
        except:
            if self.export_all:
                print_warning(f"In block {self.path_folder} export_all set to true and blacklist does not exist, everything in {self.path_folder} will be exported!")
            else:
                print_warning(f"In block {self.path_folder} export_all set to false, only whitelisted files will be exported!")


    def FindFilesbyBlock(self, block: dict):
        result = []
        if "folders" in block.keys():
            for folder in block["folders"]:
                my_path = self.absolute_path.joinpath(Path(folder)).resolve() # Get the path of the object
                local_result = [x for x in list(my_path.glob("**/*")) if x.is_file()] # We're looking by folder, but we want only the files either way
                result.extend(local_result)
        
        if "files" in block.keys():
            for file_ in block["files"]:
                my_path = self.absolute_path.joinpath(Path(file_)).resolve()
                if my_path.is_file():
                    result.append(my_path)
                else:
                    print_warning(f"In block {self.path_folder} file {file_} does not exist!")
        
        if "filetypes" in block.keys():
            for filetype in block["filetypes"]:
                local_result = [x for x in list(self.absolute_path.glob(f"**/*{filetype}")) if x.is_file()]
                result.extend(local_result)
        
        return result

        
    def FindFiles(self):
        blacklisted_files = []
        whitelisted_files = []
        all_files = []
        if self.whitelist:
            whitelisted_files = self.FindFilesbyBlock(self.whitelist)
        
        if self.blacklist and self.export_all: #If we aren't exporting all, blacklist is unnecessary
            blacklisted_files = self.FindFilesbyBlock(self.blacklist)
        
        if self.export_all:
            all_files = [x for x in list(self.absolute_path.glob("**/*")) if x.is_file() and not x in blacklisted_files]
            #if self.blacklist:
            #    for b_file in blacklisted_files:
            #        i = 0
            #        for _ in all_files:
            #            file_ = str(all_files[i])
            #            if file_ == str(b_file):
            #                all_files.pop(i)
            #            else:
            #                i += 1
        for w_file in whitelisted_files:
            if not w_file in all_files:
                all_files.append(w_file) # Transfer over the whitelisted files
        
        self.filelist = all_files
        return len(all_files)
                
    def PrintFiles(self, file_):
        file_.write(f"> BEGIN FILE LOG FOR BLOCK: {self.path_folder}\n")
        for path_ in self.filelist:
            file_.write(f"| {str(path_)}\n")
        file_.write("> END LOG \n\n")

def CopyFiles(files: list, rel_path: Path, copy_path: Path, total: int):
    this_total = len(files)
    
    i = 0
    for fileC in files:
        f_rel_path = fileC.relative_to(rel_path)
        final_path = copy_path.joinpath(f_rel_path).resolve()
        if not final_path.parent.is_dir(): # Ensure this path exists, before we copy
            final_path.parent.mkdir(parents = True, exist_ok = True)

        print_progress(i, this_total, total, fileC)
        CopyFile(fileC, final_path)
        i += 1
        
        





def main():
    Settings() # Initialise settings

    print_info("Loading filemanifest...")
    print_info(f"[Filemanifest] {fm_path}")

    LoadManifest()

    print_success("Successfully loaded filemanifest.")
    print_info("Checking for working directory...")
    DetermineFullCWD(FM["workingdir"])
    print_success(f"[Working directory] {w_dir}")

    print_info("Parsing filemanifest...")
    blocks = []
    for block in FM["export"]:
        sas = ExportFolder(block)
        blocks.append(sas)
    print_success("Filemanifest parsed without any problems.")

    print_info("Attempting to locate all specified files...")
    total = 0
    for block in blocks:
        total += block.FindFiles() # Find all of the files defined by the blocks, also this function returns the amount of files in this block
    print_info(f"Done: {total} files.")

    if log_path:
        print_info(f"Logfile specified, printing to {log_path}")
        with open(log_path, "w+") as logfile:
            for block in blocks:
                block.PrintFiles(logfile)
        print_info("Done.")
    
    print_info("Proceeding to copy files...")

    copy_to = w_dir.joinpath(Path(FM["exportdir"]))
    print_info(f"Copying to: {copy_to}")
    
    if not skip_confirm_dialog:
        inp: str = input("[Confirmation required] Please confirm that path specified above this message is the actual path you want to copy to [Write \"no\" to abort]: ")
        if inp.lower() == "no":
            exit()

    for block in blocks:
        CopyFiles(block.filelist, block.path_relative, copy_to, total)
    
    print(" => Copying done.")

    
    
    
    



main()