from SMTLib.logger import SetupLogger, getLogger
from SMTLib.baseclass import SMTBase
from pathlib import Path
from sys import argv
import argparse
from os import process_cpu_count, remove
from shutil import copy2, rmtree
from srctools.keyvalues import Keyvalues
from srctools import conv_bool
from SMTLib import CASE_SENSITIVE
from multiprocessing import Pool
from time import time


LOG_PATH = Path(argv[0]).parent / "ContentBuilder.log"

def main():
    parser = argparse.ArgumentParser(
        prog="Content Builder",
        description="Builds specific file trees specified via config files."
    )

    parser.add_argument(
        "-v", "--verbose",
        action='store_true',
        dest="verbose",
        help="Specify if the program should print out more information (Not including --progressprint)."
    )

    parser.add_argument(
        "-y", "--yes",
        action='store_true',
        dest="skip_dialog",
        help="Skip the confirmation dialog and immediately proceed to copy the files."
    )

    parser.add_argument(
        "-nl", "--nolog",
        action='store_false',
        dest="nl",
        help="Don't create log files."
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-dr", "--dryrun",
        action="store_true",
        dest="dr",
        help="Perform a dry run - don't actually copy the files, only print out the filestructure."
    )

    group.add_argument(
        "-nt", "--notree",
        action='store_true',
        dest="nt",
        help="Skip performing the file tree calculations. Saves memory and time if you are certain the config is correct, as this won't show you the filestructure before exporting. --yes automatically sets this to true."
    )

    parser.add_argument(
        "-wd", "--working_dir",
        action='store',
        dest='wd',
        help="Override the working directory of the program (or set it, if it's not in the config).",
        default=None
    )

    parser.add_argument(
        "-t", "--threads",
        action="store",
        dest="threads",
        help="Maximum amount of threads this program can use. Default value is half of available threads.",
        default=process_cpu_count() / 2
    )

    parser.add_argument(
        "config",
        help="Path to the config file used to specify the tree structure. Check the Source Mod Tools wiki for more info."
    )

    result = parser.parse_args(argv[1:]) # Don't include argv[0], as it gets interpreted as the config positional

    SetupLogger(LOG_PATH, True, create_files=result.nl)

    logger = getLogger("CB Main")

    try:
        threads = int(result.threads)
        if threads <= 0:
            raise ValueError
        
    except ValueError:
        logger.error(f"Invalid threads argument passed. Expecting  positive integer, got {result.threads}!")
        raise RuntimeError

    if threads > process_cpu_count():
        logger.warning(f"Threads value passed is too high, only {process_cpu_count()} threads are available! Setting the thread count to maximum available.")
        threads = process_cpu_count()

    if result.verbose:
        logger.info(f"Working with {threads} threads.")
        
        if result.skip_dialog:
            logger.info(f"Starting up with --yes passed, no confirmation will be required!")


    CB_obj = ContentBuilder("Content Builder",
                            verbose=result.verbose,
                            cfg_path=Path(result.config),
                            args={
                                "skip_dialog": result.skip_dialog,
                                "threads": threads,
                                "nolog": result.nl,
                                "dryrun": result.dr,
                                "notree": result.nt,
                                "wd": result.wd
                            })
    
    CB_obj.run()

    
def cp_func(s):
    return s.copy()


class CopyPasteDirectory:
    def __init__(self, source:Path, dest:Path):
        self.source = source
        self.dest = dest


    def copy(self):
        self.dest.parent.mkdir(parents=True, exist_ok=True)
        if self.dest.exists():
            if self.dest.is_file():
                remove(self.dest)
            elif self.dest.is_dir():
                rmtree(self.dest)

        copy2(self.source, self.dest)

    def __repr__(self):
        return f"{self.source} -> {self.dest}"


class ContentBuilder(SMTBase):
    def run(self):
        
        try:
            self.export_dir = Path(self.cfg.find_key("export dir").value)
        except KeyError:
            self.logger.error("No export path specified!")
            raise RuntimeError
        
        self.logger.info(f"Exporting to {self.export_dir}")

        if self.verbose:
            self.logger.info("Preparing filestructure to copy...")

        try:
            export_block = self.cfg.find_block("export")
        except KeyError:
            self.logger.error("Export block not found!")
            raise RuntimeError
        
        try:
            destination = self.AbsoluteOrWd(Path(self.cfg["export dir"]))
        except KeyError:
            self.logger.error("No export directory specified!")
            raise RuntimeError
        
        self.f_structure: set[CopyPasteDirectory] = set()

        for kv_block_name in export_block.as_dict().keys(): # pyright: ignore[reportAttributeAccessIssue]

            block = export_block.find_block(kv_block_name)
            files = self.parse_export_block(block)

            relative_path = self.AbsoluteOrWd(Path(block["path_relative", block["path", ""]]))

            self.f_structure |= self.relate_files(files, destination, relative_path, kv_block_name)
        
        if self.verbose:
            self.logger.info("Parsing export blocks done.")

        tree_printed = False
        if not conv_bool(self.args["notree"]) and not conv_bool(self.args["skip_dialog"]): # type: ignore
            self.print_fs_tree()
            tree_printed = True

        if conv_bool(self.args["dryrun"]): # type: ignore
            if not tree_printed:
                self.print_fs_tree()
                tree_printed = True
                return
            else:
                return

        if not conv_bool(self.args["skip_dialog"]): # type: ignore
            if input("Do you want to continue? [Leave empty for yes]: "):
                return
            
        
        self.logger.info("Proceeding to build the filestructure...")
        t_start = time()

        with Pool(self.args["threads"]) as pool: # type: ignore
            pool.map(cp_func, self.f_structure)

        self.logger.info(f"Success! Time taken: {(time() - t_start):2}s")
        

        
    def relate_files(self, files: set[Path], destination:Path, src_relative:Path, block_name: str = "") -> set[CopyPasteDirectory]:
        
        ready = set()
        
        for file_ in files:
            try:
                p_suffix = file_.relative_to(src_relative)
            except ValueError:
                self.logger.error(f"Path {file_} doesn't relate to {src_relative} in block {block_name}!")
                raise RuntimeError
            
            ready.add(
                CopyPasteDirectory(file_, destination / p_suffix)
            )

        return ready
            

    def AbsoluteOrWd(self, path:Path) -> Path:
        if path.is_absolute():
            return path
        else:
            return self.wd / path # type: ignore


    def parse_export_block(self, block: Keyvalues):
        if self.verbose:
            self.logger.info(f"Processing block {block.real_name}...")

        self.logger.debug(f"Parsing {block}")

        flagged_files: set[Path] = set()

        local_wd: Path = self.AbsoluteOrWd(Path(block.find_key("path", def_="").value))

        whitelist_exists = False

        if export_all := block.bool("export all", def_=False):
            files = set(local_wd.rglob("**/*", recurse_symlinks=True))

            files = ExcludeDirectories(files)
            
            flagged_files |= files

        for it_block in block:
            if it_block.name == "whitelist":
                flagged_files |= self.parse_WBBlock(it_block, local_wd, block.real_name)
                whitelist_exists = True
                continue

            if it_block.name == "blacklist":
                flagged_files -= self.parse_WBBlock(it_block, local_wd, block.real_name)
                continue


        if export_all and whitelist_exists and self.verbose:
            self.logger.info(f"Whitelist is not needed for block {block.real_name} as Export All is set to true!")
        
        if not export_all and not whitelist_exists:
            self.logger.warning(f"In block {block.real_name} no whitelist has been set (or no files were marked) and Export All set to false, nothing to export!")


        return flagged_files
    
    def parse_WBBlock(self, block: Keyvalues, local_wd: Path, parent_name:str) -> set[Path]:

        flagged_files = set()

        for block_pair in block:
            if block_pair.name == "regex":
                found = set(local_wd.rglob(block_pair.value, case_sensitive=CASE_SENSITIVE, recurse_symlinks=True))
                
                found = ExcludeDirectories(found)
                
                flagged_files |= found
                if self.verbose:
                    self.logger.info(f"Regex flag {block_pair.value} ({parent_name}) returned {len(found)} files!")
                continue

            if block_pair.name == "file":
                file_test = local_wd / block_pair.value
                if not file_test.exists():
                    self.logger.warning(f"File {file_test} specified in block {parent_name} does not exist!")

                else:
                    if self.verbose:
                        self.logger.info(f"File {file_test} ({parent_name}) found!")
                    
                    flagged_files.add(file_test)

                continue

            if block_pair.name == "dir":
                new_path = local_wd / block_pair.value

                if not new_path.exists():
                    self.logger.warning(f"Specified directory {new_path} in block {parent_name} does not exist!")
                else:
                    if self.verbose:
                        self.logger.info(f"Found directory {new_path} ({parent_name})")
                    
                    files = set(new_path.rglob("**/*", case_sensitive=CASE_SENSITIVE, recurse_symlinks=True))

                    files = ExcludeDirectories(files)

                    flagged_files |= files


        return flagged_files
    

    def print_fs_tree(self):
        self.logger.info("Proceeding to print the filestructure tree...")

        structure = Keyvalues("/", [])

        for cpdir in self.f_structure:
            path = cpdir.dest

            all_paths = [path]
            all_paths.extend(path.parents)

            all_paths = [x.name for x in all_paths]

            self.recurse_add_name_to_fstructure(structure, all_paths)
        
        # Merge dirs where the path isn't splitting
        while len(structure) <= 1:
            nm = structure.real_name
            if nm != "/":
                new_name = nm + "/" + structure[0].real_name
            else:
                new_name = nm + structure[0].real_name

            structure.edit(new_name, structure[0]._value) # type: ignore


        MAX_COUNT = 10 if self.verbose else 5
        pr_str = "Export tree: \n" + structure.repr_as_tree(MAX_COUNT).replace("?file: ", "")
        self.logger.info(pr_str)

        


    def recurse_add_name_to_fstructure(self, fstructure: Keyvalues, names:list[str]):

        if not names:
            return

        name = names.pop()

        if not name:
            name = names.pop()
        block = fstructure.ensure_exists(name)


        if len(names) == 1: # Last one
            last_name = names.pop()
            block.append(Keyvalues("?file", last_name))

            return
    
        self.recurse_add_name_to_fstructure(block, names)

def ExcludeDirectories(paths: set[Path]) -> set[Path]:
    return set(x for x in paths if x.is_file()) # Here we also check if the file exists
                                                # It should, but is_file already does that so...

if __name__ == "__main__":
    main()