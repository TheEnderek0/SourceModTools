from pathlib import Path
from srctools.steam import find_app
from .logger import getLogger
from os import getcwd
from sys import platform

LOGGER = getLogger("Path")

def parse_path(raw_path: str, available_vars: dict[str, str|Path] = {}, wd_mode = False) -> Path:
    """Parse the path passed via str.
    Expands <appid> and {var} variables, {var}s must be passed in available_vars where the key is the casefold representation of the name of the used var in the path.
    The value may be a Path, but such var may only be inserted at the very start of the parsed path, e.g. {var1}/something/..."""
    p_path = raw_path

    if p_path.startswith("<"): # We're looking for an appid
        try:
            appid_end_idx = p_path.index(">")
        except ValueError:
            LOGGER.error(f"Path {raw_path} is invalid! Missing AppID closing bracket '>'!")
            raise RuntimeError

        appid, p_path = p_path[1:appid_end_idx], p_path[appid_end_idx+1:]
        
        try:
            appid = int(appid)
        except ValueError:
            LOGGER.error(f"Path {raw_path} has non-numerical AppID!")
            raise RuntimeError
        
        try:
            app = find_app(appid)
        except KeyError:
            LOGGER.error(f"Cannot find AppID {appid}!")
            raise RuntimeError
        
        p_path = str(app.path) + p_path

    while p_path.find("{") != -1:
        var_start = p_path.index("{")
        try:
            var_end = p_path.index("}")
        except ValueError:
            LOGGER.error(f"Path {raw_path}" + " has unclosed }!")
            raise RuntimeError
        

        var_name = p_path[var_start+1:var_end]


        if not var_name.casefold() in available_vars.keys():
            LOGGER.error(f"Unknown path variable '{var_name}' in path {raw_path}!")
            raise RuntimeError
        
        var_value = available_vars[var_name.casefold()]

        if type(var_value) == Path and var_start != 0:
            LOGGER.error(f"Cannot insert PATH into other path at a place other than the very start! {raw_path}, var: {var_name}")
            raise RuntimeError

        p_path = p_path.replace("{" + var_name + "}", str(var_value))


    p_path = Path(p_path)

    if not p_path.is_absolute():
        if not wd_mode:
            p_path = available_vars["wd"] / p_path
        else:
            p_path = Path(getcwd()) / p_path
        
    return p_path



def FindParent(path: Path , parent_name: str) -> Path|None:
    """Finds the first parent path with the stem equal to parent_name, iterating from the bottom to the root. Isn't case sensitive on windows.
    Returns None if not found."""
    for tpath in (list(path.parents) + [path]):
        if platform == "win32":
            if tpath.stem.casefold() == parent_name.casefold():
                return tpath
        
        else:
            if tpath.stem == parent_name:
                return tpath
    
    return None

