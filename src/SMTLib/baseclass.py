"""
Holds the base class that all programs inherit from
"""

from pathlib import Path
from srctools import Keyvalues
from .logger import getLogger
from .path import parse_path, FindParent

class SMTBase():
    def __init__(self, name:str, verbose:bool, cfg_path:Path, args: dict[str, str|int] = {}):
        """Base class for all SourceModTool programs, handles basic functionality such as config loading and some invoke argument parsing"""

        self.logger = getLogger(name)

        self.args = args.copy()
        self.name = name

        self.verbose = verbose
        if self.verbose:
            self.logger.info("Verbose mode set to True, prepare for logs!")
        
        if not cfg_path.exists():
            self.logger.error(f"Cannot find file {cfg_path.absolute()}")
            raise FileNotFoundError()
    
        with open(cfg_path, "r") as cfg_file:
            self.cfg = Keyvalues.parse(cfg_file)

        self.cfg = self.cfg[0] # We don't need the root kv block
        
        self.logger.info(f"Loaded config '{self.cfg.real_name}'!")

        if "wd" in args.keys() and args["wd"] is not None: # Working dir override
            self.wd = Path(args["wd"]) # pyright: ignore[reportArgumentType]
        else:
            self.findwd()

        if self.wd is None:
            self.logger.error("Cannot locate working directory!")
            raise RuntimeError



        self.logger.info(f"Working directory is: {self.wd}")
        if not self.wd.exists(): # type: ignore
            self.logger.warning(f"The selected path for working directory: {self.wd} does not exist!")




    def findwd(self):
        """Locate working directory specified in the config file."""

        try:
            wd_cfg = self.cfg.find_key("working directory")
        except KeyError:
            self.logger.error("Cannot locate Working Directory block in config file!")
            raise RuntimeError
        


        if not wd_cfg.has_children():
            # Case of "Working Directory" "<path>"
            self.wd = parse_path(wd_cfg.value, wd_mode=True)
            return
        else:
            try:
                find_ = wd_cfg.find_key("find").value
            except KeyError:
                self.logger.error("Working Directory find technique requires the Find keyvalue!")
                raise RuntimeError
            
            method = wd_cfg.find_key("use", def_="program").value.casefold()

            if method == "program":
                from sys import argv
                base_path = Path(argv[0])

            elif method == "cwd":
                from os import getcwd
                base_path = Path(getcwd())
            
            else:
                self.logger.error(f"Unsupported find method in Working Directory block: '{method}'!")
                raise RuntimeError
            
            self.wd = FindParent(base_path, find_)

            if self.wd is None:
                self.logger.error(f"Working Directory: Cannot find {find_} in {base_path}!")
                raise RuntimeError
            
            append_ = wd_cfg.find_key("append", def_="").value
            
            self.wd /= append_
            
            return

    
    def __repr__(self):
        return f'<Program object "{self.name}">'

    

    